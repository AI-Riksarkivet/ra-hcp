"""Stateful MAPI mock — MockMapiState + URL dispatcher."""

from __future__ import annotations

import copy
import json
import logging
from typing import Any

import httpx
import respx
from httpx import Response as HttpxResponse

from .fixtures import (
    AVAILABLE_SERVICE_PLANS,
    CONTENT_CLASSES,
    GROUP_ACCOUNTS,
    NAMESPACES,
    NS_CHARGEBACK,
    NS_STATISTICS,
    RETENTION_CLASSES,
    TENANT_CHARGEBACK,
    TENANT_STATISTICS,
    TENANTS,
    USER_ACCOUNTS,
    default_ns_settings,
    default_tenant_settings,
)

logger = logging.getLogger("mock_server.mapi")

# Settings keys handled as generic GET/POST sub-resources
TENANT_SETTING_KEYS = frozenset(
    {
        "consoleSecurity",
        "contactInfo",
        "emailNotification",
        "namespaceDefaults",
        "searchSecurity",
        "permissions",
    }
)
NS_SETTING_KEYS = frozenset(
    {
        "complianceSettings",
        "permissions",
        "customMetadataIndexingSettings",
        "replicationCollisionSettings",
    }
)


# ── Response helpers ─────────────────────────────────────────────────


def _json_response(data: Any, status_code: int = 200) -> HttpxResponse:
    return HttpxResponse(status_code=status_code, json=data)


def _empty_response(status_code: int = 200) -> HttpxResponse:
    return HttpxResponse(status_code=status_code)


# ── MockMapiState ────────────────────────────────────────────────────


class MockMapiState:
    """In-memory state for all MAPI resources."""

    def __init__(self) -> None:
        self.tenants: dict[str, dict] = {}
        self.namespaces: dict[str, dict[str, dict]] = {}  # {tenant: {ns: data}}
        self.user_accounts: dict[str, dict[str, dict]] = {}  # {tenant: {user: data}}
        self.group_accounts: dict[str, dict[str, dict]] = {}  # {tenant: {group: data}}
        self.content_classes: dict[str, dict[str, dict]] = {}  # {tenant: {cc: data}}
        self.retention_classes: dict[
            tuple, dict[str, dict]
        ] = {}  # {(t,ns): {rc: data}}
        self.tenant_settings: dict[str, dict[str, dict]] = {}  # {tenant: {key: data}}
        self.ns_settings: dict[tuple, dict[str, dict]] = {}  # {(t,ns): {key: data}}
        self.data_access_perms: dict[tuple, dict] = {}  # {(t,type,name): perms}

    # ── Generic CRUD helpers ─────────────────────────────────────

    def _list_names(self, store: dict, key_field: str = "name") -> HttpxResponse:
        return _json_response({key_field: list(store.keys())})

    def _get_item(self, store: dict, name: str) -> HttpxResponse:
        if name not in store:
            return _json_response({}, 404)
        return _json_response(store[name])

    def _head_item(self, store: dict, name: str) -> HttpxResponse:
        return _empty_response(200 if name in store else 404)

    def _create_item(
        self, store: dict, name: str, body: dict, name_field: str = "name"
    ) -> HttpxResponse:
        if name in store:
            return _json_response({"message": f"{name} already exists"}, 409)
        body[name_field] = name
        store[name] = body
        return _empty_response(200)

    def _modify_item(self, store: dict, name: str, body: dict) -> HttpxResponse:
        if name not in store:
            return _json_response({}, 404)
        store[name].update(body)
        return _empty_response(200)

    def _delete_item(self, store: dict, name: str) -> HttpxResponse:
        if name not in store:
            return _json_response({}, 404)
        del store[name]
        return _empty_response(200)

    # ── Tenant lifecycle (init/cleanup sub-collections) ──────────

    def create_tenant(self, name: str, body: dict) -> HttpxResponse:
        if name in self.tenants:
            return _json_response({"message": f"{name} already exists"}, 409)
        body["name"] = name
        self.tenants[name] = body
        self.namespaces.setdefault(name, {})
        self.user_accounts.setdefault(name, {})
        self.group_accounts.setdefault(name, {})
        self.content_classes.setdefault(name, {})
        self.tenant_settings.setdefault(name, default_tenant_settings())
        return _empty_response(200)

    def delete_tenant(self, name: str) -> HttpxResponse:
        if name not in self.tenants:
            return _json_response({}, 404)
        # Clean up all sub-resources
        for ns in list(self.namespaces.get(name, {})):
            self.retention_classes.pop((name, ns), None)
            self.ns_settings.pop((name, ns), None)
        self.tenants.pop(name)
        self.namespaces.pop(name, None)
        self.user_accounts.pop(name, None)
        self.group_accounts.pop(name, None)
        self.content_classes.pop(name, None)
        self.tenant_settings.pop(name, None)
        # Clean data access perms for this tenant
        for key in [k for k in self.data_access_perms if k[0] == name]:
            del self.data_access_perms[key]
        return _empty_response(200)

    # ── Namespace lifecycle ──────────────────────────────────────

    def create_namespace(self, tenant: str, name: str, body: dict) -> HttpxResponse:
        ns_map = self.namespaces.get(tenant)
        if ns_map is None:
            return _json_response({}, 404)
        if name in ns_map:
            return _json_response({"message": f"{name} already exists"}, 409)
        body["name"] = name
        ns_map[name] = body
        self.retention_classes.setdefault((tenant, name), {})
        self.ns_settings.setdefault((tenant, name), default_ns_settings())
        return _empty_response(200)

    def delete_namespace(self, tenant: str, name: str) -> HttpxResponse:
        ns_map = self.namespaces.get(tenant)
        if ns_map is None or name not in ns_map:
            return _json_response({}, 404)
        del ns_map[name]
        self.retention_classes.pop((tenant, name), None)
        self.ns_settings.pop((tenant, name), None)
        return _empty_response(200)

    # ── Settings access ──────────────────────────────────────────

    def get_tenant_setting(self, tenant: str, key: str) -> HttpxResponse:
        settings = self.tenant_settings.get(tenant, {})
        return _json_response(settings.get(key, {}))

    def update_tenant_setting(self, tenant: str, key: str, body: dict) -> HttpxResponse:
        if tenant not in self.tenants:
            return _json_response({}, 404)
        self.tenant_settings.setdefault(tenant, {})[key] = body
        return _empty_response(200)

    def get_ns_setting(self, tenant: str, ns: str, key: str) -> HttpxResponse:
        settings = self.ns_settings.get((tenant, ns), {})
        return _json_response(settings.get(key, {}))

    def update_ns_setting(
        self, tenant: str, ns: str, key: str, body: dict
    ) -> HttpxResponse:
        ns_map = self.namespaces.get(tenant, {})
        if ns not in ns_map:
            return _json_response({}, 404)
        self.ns_settings.setdefault((tenant, ns), {})[key] = body
        return _empty_response(200)

    def delete_ns_setting(self, tenant: str, ns: str, key: str) -> HttpxResponse:
        settings = self.ns_settings.get((tenant, ns), {})
        if key in settings:
            del settings[key]
        return _empty_response(200)

    # ── Data access permissions ──────────────────────────────────

    def get_data_access_perms(
        self, tenant: str, acct_type: str, name: str
    ) -> HttpxResponse:
        return _json_response(self.data_access_perms.get((tenant, acct_type, name), {}))

    def update_data_access_perms(
        self, tenant: str, acct_type: str, name: str, body: dict
    ) -> HttpxResponse:
        self.data_access_perms[(tenant, acct_type, name)] = body
        return _empty_response(200)

    # ── Protocol settings ────────────────────────────────────────

    def get_protocol(self, tenant: str, ns: str, protocol: str | None) -> HttpxResponse:
        settings = self.ns_settings.get((tenant, ns), {})
        protocols = settings.get("protocols", {})
        key = protocol or "default"
        return _json_response(protocols.get(key, {}))

    def update_protocol(
        self, tenant: str, ns: str, protocol: str | None, body: dict
    ) -> HttpxResponse:
        ns_map = self.namespaces.get(tenant, {})
        if ns not in ns_map:
            return _json_response({}, 404)
        settings = self.ns_settings.setdefault((tenant, ns), {})
        protocols = settings.setdefault("protocols", {})
        key = protocol or "default"
        protocols[key] = body
        return _empty_response(200)


# ── Seed ─────────────────────────────────────────────────────────────


def seed_mapi_state(state: MockMapiState) -> None:
    """Copy fixture data into the state object and initialize default settings."""
    state.tenants = copy.deepcopy(TENANTS)
    state.namespaces = copy.deepcopy(NAMESPACES)
    state.user_accounts = copy.deepcopy(USER_ACCOUNTS)
    state.group_accounts = copy.deepcopy(GROUP_ACCOUNTS)
    state.content_classes = copy.deepcopy(CONTENT_CLASSES)
    state.retention_classes = copy.deepcopy(RETENTION_CLASSES)

    for tenant in TENANTS:
        state.tenant_settings[tenant] = default_tenant_settings()

    for tenant, ns_map in NAMESPACES.items():
        for ns in ns_map:
            state.ns_settings[(tenant, ns)] = default_ns_settings()


# ── Dispatcher ───────────────────────────────────────────────────────


def _parse_body(request: httpx.Request) -> dict:
    if request.content:
        try:
            return json.loads(request.content)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def _make_mapi_dispatcher(state: MockMapiState):  # noqa: C901 — intentionally large
    """Return a side_effect callable that routes all MAPI requests."""

    def dispatcher(request: httpx.Request) -> HttpxResponse:
        method = request.method
        path = request.url.path  # e.g. /mapi/tenants/default/userAccounts
        rest = path.removeprefix("/mapi/").strip("/")

        if not rest:
            logger.info("%s %s → 404 (empty)", method, path)
            return _json_response({"message": "Not found"}, 404)

        segments = rest.split("/")
        n = len(segments)
        logger.info("%s %s  (segments=%s)", method, path, segments)

        if segments[0] != "tenants":
            return _json_response({"message": "Not found"}, 404)

        body = _parse_body(request) if method in ("PUT", "POST") else {}

        # ── /tenants ─────────────────────────────────────────────
        if n == 1:
            if method == "GET":
                return state._list_names(state.tenants)
            if method == "PUT":
                name = body.get("name", "")
                return state.create_tenant(name, body)
            return _json_response({}, 405)

        tenant = segments[1]

        # ── /tenants/{T} ─────────────────────────────────────────
        if n == 2:
            if method == "GET":
                return state._get_item(state.tenants, tenant)
            if method == "HEAD":
                return state._head_item(state.tenants, tenant)
            if method == "POST":
                return state._modify_item(state.tenants, tenant, body)
            if method == "DELETE":
                return state.delete_tenant(tenant)
            return _json_response({}, 405)

        resource = segments[2]

        # ── /tenants/{T}/userAccounts ────────────────────────────
        if resource == "userAccounts":
            store = state.user_accounts.get(tenant)
            if store is None:
                return _json_response({}, 404)

            if n == 3:
                if method == "GET":
                    return state._list_names(store, "username")
                if method == "PUT":
                    name = body.get("username", "")
                    return state._create_item(store, name, body, "username")
                if method == "POST":
                    return _empty_response(200)  # resetPasswords
                return _json_response({}, 405)

            username = segments[3]

            if n == 4:
                if method == "GET":
                    return state._get_item(store, username)
                if method == "HEAD":
                    return state._head_item(store, username)
                if method == "POST":
                    return state._modify_item(store, username, body)
                if method == "DELETE":
                    return state._delete_item(store, username)
                return _json_response({}, 405)

            if n == 5:
                sub = segments[4]
                if sub == "changePassword" and method == "POST":
                    return _empty_response(200)
                if sub == "dataAccessPermissions":
                    if method == "GET":
                        return state.get_data_access_perms(tenant, "user", username)
                    if method == "POST":
                        return state.update_data_access_perms(
                            tenant, "user", username, body
                        )
            return _json_response({}, 404)

        # ── /tenants/{T}/groupAccounts ───────────────────────────
        if resource == "groupAccounts":
            store = state.group_accounts.get(tenant)
            if store is None:
                return _json_response({}, 404)

            if n == 3:
                if method == "GET":
                    return state._list_names(store, "groupname")
                if method == "PUT":
                    name = body.get("groupname", "")
                    return state._create_item(store, name, body, "groupname")
                return _json_response({}, 405)

            groupname = segments[3]

            if n == 4:
                if method == "GET":
                    return state._get_item(store, groupname)
                if method == "HEAD":
                    return state._head_item(store, groupname)
                if method == "POST":
                    return state._modify_item(store, groupname, body)
                if method == "DELETE":
                    return state._delete_item(store, groupname)
                return _json_response({}, 405)

            if n == 5 and segments[4] == "dataAccessPermissions":
                if method == "GET":
                    return state.get_data_access_perms(tenant, "group", groupname)
                if method == "POST":
                    return state.update_data_access_perms(
                        tenant, "group", groupname, body
                    )
            return _json_response({}, 404)

        # ── /tenants/{T}/contentClasses ──────────────────────────
        if resource == "contentClasses":
            store = state.content_classes.get(tenant)
            if store is None:
                return _json_response({}, 404)

            if n == 3:
                if method == "GET":
                    return state._list_names(store)
                if method == "PUT":
                    name = body.get("name", "")
                    return state._create_item(store, name, body)
                return _json_response({}, 405)

            cc_name = segments[3]

            if n == 4:
                if method == "GET":
                    return state._get_item(store, cc_name)
                if method == "HEAD":
                    return state._head_item(store, cc_name)
                if method == "POST":
                    return state._modify_item(store, cc_name, body)
                if method == "DELETE":
                    return state._delete_item(store, cc_name)
                return _json_response({}, 405)

            return _json_response({}, 404)

        # ── /tenants/{T}/namespaces ──────────────────────────────
        if resource == "namespaces":
            ns_map = state.namespaces.get(tenant)
            if ns_map is None:
                return _json_response({}, 404)

            if n == 3:
                if method == "GET":
                    return state._list_names(ns_map)
                if method == "PUT":
                    name = body.get("name", "")
                    return state.create_namespace(tenant, name, body)
                return _json_response({}, 405)

            ns_name = segments[3]

            if n == 4:
                if method == "GET":
                    return state._get_item(ns_map, ns_name)
                if method == "HEAD":
                    return state._head_item(ns_map, ns_name)
                if method == "POST":
                    return state._modify_item(ns_map, ns_name, body)
                if method == "DELETE":
                    return state.delete_namespace(tenant, ns_name)
                return _json_response({}, 405)

            if n < 5:
                return _json_response({}, 404)

            ns_sub = segments[4]

            # /tenants/{T}/namespaces/{N}/retentionClasses
            if ns_sub == "retentionClasses":
                rc_store = state.retention_classes.get((tenant, ns_name))
                if rc_store is None:
                    return _json_response({}, 404)

                if n == 5:
                    if method == "GET":
                        return state._list_names(rc_store)
                    if method == "PUT":
                        name = body.get("name", "")
                        return state._create_item(rc_store, name, body)
                    return _json_response({}, 405)

                if n == 6:
                    rc_name = segments[5]
                    if method == "GET":
                        return state._get_item(rc_store, rc_name)
                    if method == "HEAD":
                        return state._head_item(rc_store, rc_name)
                    if method == "POST":
                        return state._modify_item(rc_store, rc_name, body)
                    if method == "DELETE":
                        return state._delete_item(rc_store, rc_name)
                    return _json_response({}, 405)

                return _json_response({}, 404)

            # /tenants/{T}/namespaces/{N}/protocols[/{P}]
            if ns_sub == "protocols":
                if n == 5:
                    if method == "GET":
                        return state.get_protocol(tenant, ns_name, None)
                    if method == "POST":
                        return state.update_protocol(tenant, ns_name, None, body)
                    return _json_response({}, 405)

                if n == 6:
                    proto = segments[5]
                    if method == "GET":
                        return state.get_protocol(tenant, ns_name, proto)
                    if method == "POST":
                        return state.update_protocol(tenant, ns_name, proto, body)
                    return _json_response({}, 405)

                return _json_response({}, 404)

            # /tenants/{T}/namespaces/{N}/cors
            if ns_sub == "cors" and n == 5:
                if method == "GET":
                    return state.get_ns_setting(tenant, ns_name, "cors")
                if method == "PUT":
                    return state.update_ns_setting(tenant, ns_name, "cors", body)
                if method == "DELETE":
                    return state.update_ns_setting(
                        tenant, ns_name, "cors", {"corsConfiguration": []}
                    )
                return _json_response({}, 405)

            # /tenants/{T}/namespaces/{N}/versioningSettings
            if ns_sub == "versioningSettings" and n == 5:
                if method == "GET":
                    return state.get_ns_setting(tenant, ns_name, "versioningSettings")
                if method == "POST":
                    return state.update_ns_setting(
                        tenant, ns_name, "versioningSettings", body
                    )
                if method == "DELETE":
                    return state.delete_ns_setting(
                        tenant, ns_name, "versioningSettings"
                    )
                return _json_response({}, 405)

            # /tenants/{T}/namespaces/{N}/statistics
            if ns_sub == "statistics" and n == 5:
                if method == "GET":
                    return _json_response(NS_STATISTICS)
                return _json_response({}, 405)

            # /tenants/{T}/namespaces/{N}/chargebackReport
            if ns_sub == "chargebackReport" and n == 5:
                if method == "GET":
                    return _json_response(NS_CHARGEBACK)
                return _json_response({}, 405)

            # /tenants/{T}/namespaces/{N}/{setting}
            if ns_sub in NS_SETTING_KEYS and n == 5:
                if method == "GET":
                    return state.get_ns_setting(tenant, ns_name, ns_sub)
                if method == "POST":
                    return state.update_ns_setting(tenant, ns_name, ns_sub, body)
                return _json_response({}, 405)

            return _json_response({}, 404)

        # ── /tenants/{T}/statistics ──────────────────────────────
        if resource == "statistics" and n == 3:
            if method == "GET":
                return _json_response(TENANT_STATISTICS)
            return _json_response({}, 405)

        # ── /tenants/{T}/chargebackReport ────────────────────────
        if resource == "chargebackReport" and n == 3:
            if method == "GET":
                return _json_response(TENANT_CHARGEBACK)
            return _json_response({}, 405)

        # ── /tenants/{T}/availableServicePlans ───────────────────
        if resource == "availableServicePlans":
            if n == 3 and method == "GET":
                return _json_response({"name": list(AVAILABLE_SERVICE_PLANS.keys())})
            if n == 4 and method == "GET":
                plan = AVAILABLE_SERVICE_PLANS.get(segments[3])
                if plan is None:
                    return _json_response({}, 404)
                return _json_response(plan)
            return _json_response({}, 405)

        # ── /tenants/{T}/cors ────────────────────────────────────
        if resource == "cors" and n == 3:
            if method == "GET":
                return state.get_tenant_setting(tenant, "cors")
            if method == "PUT":
                return state.update_tenant_setting(tenant, "cors", body)
            if method == "DELETE":
                return state.update_tenant_setting(
                    tenant, "cors", {"corsConfiguration": []}
                )
            return _json_response({}, 405)

        # ── /tenants/{T}/{setting} ───────────────────────────────
        if resource in TENANT_SETTING_KEYS and n == 3:
            if method == "GET":
                return state.get_tenant_setting(tenant, resource)
            if method == "POST":
                return state.update_tenant_setting(tenant, resource, body)
            return _json_response({}, 405)

        # ── Catch-all ────────────────────────────────────────────
        logger.warning("Unmatched MAPI route: %s %s", method, path)
        return _json_response({"message": "Not found"}, 404)

    return dispatcher


# ── Route setup ──────────────────────────────────────────────────────


def setup_mapi_routes(
    mock: respx.MockRouter, state: MockMapiState, hcp_base: str
) -> None:
    """Register a single catch-all respx route that dispatches to the state."""
    dispatcher = _make_mapi_dispatcher(state)
    mock.route(url__startswith=hcp_base).mock(side_effect=dispatcher)
