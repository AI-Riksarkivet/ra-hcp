"""Stateful MAPI mock — generic helpers, state class, and URL dispatcher."""

from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any

import httpx
import respx
from httpx import Response as HttpxResponse

from .fixtures import (
    AVAILABLE_SERVICE_PLANS,
    CONTENT_CLASSES,
    GROUP_ACCOUNTS,
    MOCK_QUERY_OBJECTS,
    MOCK_QUERY_OPERATIONS,
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

# ── Response helpers ─────────────────────────────────────────────────


def _json(data: Any, status: int = 200) -> HttpxResponse:
    return HttpxResponse(status_code=status, json=data)


def _empty(status: int = 200) -> HttpxResponse:
    return HttpxResponse(status_code=status)


def _not_found() -> HttpxResponse:
    return _json({"message": "Not found"}, 404)


def _not_allowed() -> HttpxResponse:
    return _json({}, 405)


# ── Generic dispatch helpers ─────────────────────────────────────────


def _crud(
    store: dict | None,
    method: str,
    name: str | None,
    body: dict,
    name_field: str = "name",
    verbose: bool = False,
) -> HttpxResponse:
    """Handle standard CRUD on a ``{name: data}`` dict.

    *name=None* → collection-level (GET list, PUT create, POST bulk).
    *name=str*  → item-level (GET, HEAD, POST modify, DELETE).
    """
    if store is None:
        return _not_found()

    # ── Collection level ──
    if name is None:
        if method == "GET":
            if verbose:
                return _json(list(store.values()))
            return _json({name_field: list(store.keys())})
        if method == "PUT":
            item_name = body.get(name_field, "")
            if item_name in store:
                return _json({"message": f"{item_name} already exists"}, 409)
            body[name_field] = item_name
            store[item_name] = body
            return _empty()
        if method == "POST":
            return _empty()  # bulk operations (e.g. resetPasswords)
        return _not_allowed()

    # ── Item level ──
    if method == "GET":
        return _json(store[name]) if name in store else _not_found()
    if method == "HEAD":
        return _empty(200 if name in store else 404)
    if method == "POST":
        if name not in store:
            return _not_found()
        store[name].update(body)
        return _empty()
    if method == "DELETE":
        if name not in store:
            return _not_found()
        del store[name]
        return _empty()
    return _not_allowed()


def _setting(settings: dict, key: str, method: str, body: dict) -> HttpxResponse:
    """Handle GET/POST on a settings sub-resource."""
    if method == "GET":
        return _json(settings.get(key, {}))
    if method == "POST":
        settings[key] = body
        return _empty()
    return _not_allowed()


def _cors(settings: dict, method: str, body: dict) -> HttpxResponse:
    """Handle GET/PUT/DELETE on a CORS sub-resource."""
    if method == "GET":
        return _json(settings.get("cors", {}))
    if method == "PUT":
        settings["cors"] = body
        return _empty()
    if method == "DELETE":
        settings["cors"] = {"corsConfiguration": []}
        return _empty()
    return _not_allowed()


def _protocol(
    settings: dict, method: str, protocol: str | None, body: dict
) -> HttpxResponse:
    """Handle GET/POST on protocol settings (default or named)."""
    protocols = settings.setdefault("protocols", {})
    key = protocol or "default"
    if method == "GET":
        return _json(protocols.get(key, {}))
    if method == "POST":
        protocols[key] = body
        return _empty()
    return _not_allowed()


def _static_get(data: dict, method: str) -> HttpxResponse:
    """Handle a read-only GET endpoint."""
    return _json(data) if method == "GET" else _not_allowed()


# ── Resource & settings registries ───────────────────────────────────

# CRUD resources under /tenants/{T}/{resource}  →  (state_attr, name_field)
CRUD_RESOURCES: dict[str, tuple[str, str]] = {
    "userAccounts": ("user_accounts", "username"),
    "groupAccounts": ("group_accounts", "groupname"),
    "contentClasses": ("content_classes", "name"),
}

# Which CRUD resources support account sub-resources (depth 5)
ACCOUNT_TYPES: dict[str, str] = {
    "userAccounts": "user",
    "groupAccounts": "group",
}

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


# ── MockMapiState ────────────────────────────────────────────────────


class MockMapiState:
    """In-memory state for all MAPI resources.

    Only contains lifecycle methods (create/delete) that initialise or
    clean up sub-collections.  Generic CRUD is handled by standalone
    helpers above.
    """

    def __init__(self) -> None:
        self.tenants: dict[str, dict] = {}
        self.namespaces: dict[str, dict[str, dict]] = {}
        self.user_accounts: dict[str, dict[str, dict]] = {}
        self.group_accounts: dict[str, dict[str, dict]] = {}
        self.content_classes: dict[str, dict[str, dict]] = {}
        self.retention_classes: dict[tuple, dict[str, dict]] = {}
        self.tenant_settings: dict[str, dict[str, dict]] = {}
        self.ns_settings: dict[tuple, dict[str, dict]] = {}
        self.data_access_perms: dict[tuple, dict] = {}
        # Cross-reference to S3 service for namespace ↔ bucket sync
        self._s3_service: Any = None

    # ── Lazy initialisation ────────────────────────────────────

    def ensure_tenant(self, name: str) -> None:
        """Ensure all sub-stores exist for *name* (no-op if already present)."""
        self.tenants.setdefault(name, {"name": name})
        self.namespaces.setdefault(name, {})
        self.user_accounts.setdefault(name, {})
        self.group_accounts.setdefault(name, {})
        self.content_classes.setdefault(name, {})
        self.tenant_settings.setdefault(name, default_tenant_settings())

    # ── Tenant lifecycle ─────────────────────────────────────────

    def create_tenant(self, name: str, body: dict) -> HttpxResponse:
        if name in self.tenants:
            return _json({"message": f"{name} already exists"}, 409)
        body["name"] = name
        self.tenants[name] = body
        self.namespaces.setdefault(name, {})
        self.user_accounts.setdefault(name, {})
        self.group_accounts.setdefault(name, {})
        self.content_classes.setdefault(name, {})
        self.tenant_settings.setdefault(name, default_tenant_settings())
        return _empty()

    def delete_tenant(self, name: str) -> HttpxResponse:
        if name not in self.tenants:
            return _not_found()
        for ns in list(self.namespaces.get(name, {})):
            self.retention_classes.pop((name, ns), None)
            self.ns_settings.pop((name, ns), None)
        self.tenants.pop(name)
        self.namespaces.pop(name, None)
        self.user_accounts.pop(name, None)
        self.group_accounts.pop(name, None)
        self.content_classes.pop(name, None)
        self.tenant_settings.pop(name, None)
        for key in [k for k in self.data_access_perms if k[0] == name]:
            del self.data_access_perms[key]
        return _empty()

    # ── Namespace lifecycle ──────────────────────────────────────

    def create_namespace(self, tenant: str, name: str, body: dict) -> HttpxResponse:
        ns_map = self.namespaces.get(tenant)
        if ns_map is None:
            return _not_found()
        if name in ns_map:
            return _json({"message": f"{name} already exists"}, 409)
        body["name"] = name
        ns_map[name] = body
        self.retention_classes.setdefault((tenant, name), {})
        self.ns_settings.setdefault((tenant, name), default_ns_settings())
        # Sync: also create as S3 bucket
        self._sync_create_bucket(name)
        return _empty()

    def delete_namespace(self, tenant: str, name: str) -> HttpxResponse:
        ns_map = self.namespaces.get(tenant)
        if ns_map is None or name not in ns_map:
            return _not_found()
        del ns_map[name]
        self.retention_classes.pop((tenant, name), None)
        self.ns_settings.pop((tenant, name), None)
        # Sync: also remove S3 bucket
        self._sync_delete_bucket(name)
        return _empty()

    # ── Auto-grant helpers ─────────────────────────────────────────────

    _ALL_PERMS = ["BROWSE", "READ", "READ_ACL", "WRITE", "WRITE_ACL", "DELETE"]

    def _grant_user_ns_access(self, tenant: str, username: str, ns_name: str) -> None:
        """Grant a single user full data access to a namespace.

        Per HCP S3 docs, creating a bucket grants the *creator* browse,
        read, readACL, write, writeACL, and delete permissions.
        """
        key = (tenant, "user", username)
        perms = self.data_access_perms.get(key, {})
        ns_perms = perms.get("namespacePermission", [])
        if any(p.get("namespaceName") == ns_name for p in ns_perms):
            return
        ns_perms.append(
            {
                "namespaceName": ns_name,
                "permissions": {"permission": list(self._ALL_PERMS)},
            }
        )
        perms["namespacePermission"] = ns_perms
        self.data_access_perms[key] = perms

    # ── Namespace ↔ bucket sync helpers ─────────────────────────────────

    def _sync_create_bucket(self, name: str) -> None:
        """Create an S3 bucket when a namespace is created via MAPI."""
        s3 = self._s3_service
        if s3 is None:
            return
        if name not in s3._buckets:
            from datetime import datetime, timezone

            s3._buckets[name] = {"CreationDate": datetime.now(timezone.utc).isoformat()}
            s3._objects[name] = {}

    def _sync_delete_bucket(self, name: str) -> None:
        """Remove the S3 bucket when a namespace is deleted via MAPI."""
        s3 = self._s3_service
        if s3 is None:
            return
        s3._buckets.pop(name, None)
        s3._objects.pop(name, None)
        s3._versioning.pop(name, None)
        s3._bucket_acls.pop(name, None)


# ── Seed ─────────────────────────────────────────────────────────────


def seed_mapi_state(state: MockMapiState) -> None:
    """Copy fixture data into the state and initialise default settings."""
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
    # Seed: grant all users access to all namespaces for dev convenience
    for tenant_name in state.namespaces:
        users = state.user_accounts.get(tenant_name, {})
        for ns_name in state.namespaces[tenant_name]:
            for username in users:
                state._grant_user_ns_access(tenant_name, username, ns_name)

    # Sync: ensure every MAPI namespace also exists as an S3 bucket
    if state._s3_service is not None:
        for ns_map in state.namespaces.values():
            for ns_name in ns_map:
                state._sync_create_bucket(ns_name)


# ── Sub-resource handlers ────────────────────────────────────────────


def _handle_account_sub(
    state: MockMapiState,
    tenant: str,
    acct_type: str,
    name: str,
    sub: str,
    method: str,
    body: dict,
) -> HttpxResponse:
    """Handle /tenants/{T}/(user|group)Accounts/{name}/(changePassword|dataAccessPermissions)."""
    if sub == "changePassword" and method == "POST":
        return _empty()
    if sub == "dataAccessPermissions":
        key = (tenant, acct_type, name)
        if method == "GET":
            return _json(state.data_access_perms.get(key, {}))
        if method == "POST":
            state.data_access_perms[key] = body
            return _empty()
    return _not_found()


def _handle_namespaces(
    state: MockMapiState,
    tenant: str,
    method: str,
    segments: list[str],
    body: dict,
) -> HttpxResponse:
    """Handle all /tenants/{T}/namespaces/... routes."""
    n = len(segments)
    ns_map = state.namespaces.get(tenant)
    if ns_map is None:
        return _not_found()

    # /tenants/{T}/namespaces
    if n == 3:
        if method == "PUT":
            return state.create_namespace(tenant, body.get("name", ""), body)
        if method == "GET":
            return _json({"name": list(ns_map.keys())})
        return _not_allowed()

    ns_name = segments[3]

    # /tenants/{T}/namespaces/{N}
    if n == 4:
        if method == "DELETE":
            return state.delete_namespace(tenant, ns_name)
        return _crud(ns_map, method, ns_name, body)

    ns_sub = segments[4]
    ns_settings = state.ns_settings.setdefault((tenant, ns_name), {})

    # retentionClasses — standard CRUD (depth 5–6)
    if ns_sub == "retentionClasses":
        rc_store = state.retention_classes.get((tenant, ns_name))
        rc_name = segments[5] if n >= 6 else None
        return _crud(rc_store, method, rc_name, body) if n <= 6 else _not_found()

    # protocols (depth 5 = default, depth 6 = named protocol)
    if ns_sub == "protocols":
        proto = segments[5] if n == 6 else None
        return _protocol(ns_settings, method, proto, body) if n <= 6 else _not_found()

    # Everything below is depth-5 only
    if n != 5:
        return _not_found()

    if ns_sub == "cors":
        return _cors(ns_settings, method, body)
    if ns_sub == "versioningSettings":
        if method == "DELETE":
            ns_settings.pop("versioningSettings", None)
            return _empty()
        return _setting(ns_settings, "versioningSettings", method, body)
    if ns_sub == "statistics":
        return _static_get(NS_STATISTICS, method)
    if ns_sub == "chargebackReport":
        return _static_get(NS_CHARGEBACK, method)
    if ns_sub in NS_SETTING_KEYS:
        return _setting(ns_settings, ns_sub, method, body)

    return _not_found()


# ── Dispatcher ───────────────────────────────────────────────────────


def _parse_body(request: httpx.Request) -> dict:
    if request.content:
        try:
            return json.loads(request.content)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def _make_mapi_dispatcher(state: MockMapiState):
    """Return a ``side_effect`` callable that routes all MAPI requests."""

    def dispatcher(request: httpx.Request) -> HttpxResponse:
        method = request.method
        path = request.url.path
        rest = path.removeprefix("/mapi/").strip("/")

        if not rest:
            return _not_found()

        segments = rest.split("/")
        n = len(segments)
        logger.info("%s %s", method, path)

        if segments[0] != "tenants":
            return _not_found()

        body = _parse_body(request) if method in ("PUT", "POST") else {}

        # /tenants
        if n == 1:
            if method == "PUT":
                return state.create_tenant(body.get("name", ""), body)
            if method == "GET":
                return _json({"name": list(state.tenants.keys())})
            return _not_allowed()

        tenant = segments[1]
        state.ensure_tenant(tenant)

        # /tenants/{T}
        if n == 2:
            if method == "DELETE":
                return state.delete_tenant(tenant)
            return _crud(state.tenants, method, tenant, body)

        resource = segments[2]
        item = segments[3] if n >= 4 else None

        # ── CRUD resources (userAccounts, groupAccounts, contentClasses) ──
        if resource in CRUD_RESOURCES:
            attr, name_field = CRUD_RESOURCES[resource]
            store = getattr(state, attr).get(tenant)
            if n == 5 and item and resource in ACCOUNT_TYPES:
                return _handle_account_sub(
                    state,
                    tenant,
                    ACCOUNT_TYPES[resource],
                    item,
                    segments[4],
                    method,
                    body,
                )
            verbose = request.url.params.get("verbose", "false") == "true"
            return (
                _crud(store, method, item, body, name_field, verbose=verbose)
                if n <= 4
                else _not_found()
            )

        # ── Namespaces (CRUD + deep sub-resources) ──
        if resource == "namespaces":
            return _handle_namespaces(state, tenant, method, segments, body)

        # ── Tenant-level leaf endpoints (depth 3 only) ──
        if n == 3:
            if resource == "statistics":
                return _static_get(TENANT_STATISTICS, method)
            if resource == "chargebackReport":
                return _static_get(TENANT_CHARGEBACK, method)
            if resource == "cors":
                return _cors(state.tenant_settings.setdefault(tenant, {}), method, body)
            if resource in TENANT_SETTING_KEYS:
                return _setting(
                    state.tenant_settings.setdefault(tenant, default_tenant_settings()),
                    resource,
                    method,
                    body,
                )

        # ── availableServicePlans (depth 3–4) ──
        if resource == "availableServicePlans":
            if n == 3 and method == "GET":
                return _json({"name": list(AVAILABLE_SERVICE_PLANS.keys())})
            if n == 4 and method == "GET":
                plan = AVAILABLE_SERVICE_PLANS.get(segments[3])
                return _json(plan) if plan else _not_found()
            return _not_allowed()

        logger.warning("Unmatched MAPI route: %s %s", method, path)
        return _not_found()

    return dispatcher


# ── Metadata Query handlers ───────────────────────────────────────────

_NS_PATTERN = re.compile(r'namespace:"([^"]+)"')


def _handle_object_query(body: dict) -> HttpxResponse:
    """Handle an object metadata query request."""
    obj = body.get("object", {})
    query_expr = obj.get("query", "*:*")
    count = obj.get("count", 100)
    offset = obj.get("offset", 0)
    verbose = obj.get("verbose", False)

    results = list(MOCK_QUERY_OBJECTS)

    # Filter by namespace if query contains namespace:"xxx"
    ns_match = _NS_PATTERN.search(query_expr)
    if ns_match:
        ns = ns_match.group(1)
        results = [r for r in results if r.get("namespace") == ns]

    total = len(results)
    page = results[offset : offset + count]

    if not verbose:
        page = [
            {
                "urlName": r["urlName"],
                "operation": r.get("operation", ""),
                "changeTimeMilliseconds": r.get("changeTimeMilliseconds"),
                "changeTimeString": r.get("changeTimeString"),
                "version": r.get("version"),
            }
            for r in page
        ]

    return _json(
        {
            "status": {
                "totalResults": total,
                "results": len(page),
                "code": "COMPLETE",
            },
            "resultSet": page,
        }
    )


def _handle_operation_query(body: dict) -> HttpxResponse:
    """Handle an operation metadata query request."""
    op = body.get("operation", {})
    count = op.get("count", 100)
    verbose = op.get("verbose", False)
    sys_meta = op.get("systemMetadata", {})

    results = list(MOCK_QUERY_OPERATIONS)

    # Filter by time range
    time_from = sys_meta.get("changeTimeFrom")
    time_to = sys_meta.get("changeTimeTo")
    if time_from:
        results = [r for r in results if r.get("changeTimeString", "") >= time_from]
    if time_to:
        results = [r for r in results if r.get("changeTimeString", "") <= time_to]

    # Filter by namespace list
    namespaces = sys_meta.get("namespaces")
    if namespaces:
        results = [r for r in results if r.get("namespace") in namespaces]

    # Filter by transaction types
    txns = sys_meta.get("transactions", {})
    tx_list = txns.get("transaction") if txns else None
    if tx_list:
        tx_upper = {t.upper() for t in tx_list}
        results = [r for r in results if r.get("operation", "").upper() in tx_upper]

    total = len(results)
    page = results[:count]

    if not verbose:
        page = [
            {
                "urlName": r["urlName"],
                "operation": r.get("operation", ""),
                "changeTimeMilliseconds": r.get("changeTimeMilliseconds"),
                "changeTimeString": r.get("changeTimeString"),
                "version": r.get("version"),
            }
            for r in page
        ]

    return _json(
        {
            "status": {
                "totalResults": total,
                "results": len(page),
                "code": "COMPLETE",
            },
            "resultSet": page,
        }
    )


def _make_query_dispatcher():
    """Return a ``side_effect`` callable that routes query requests."""

    def dispatcher(request: httpx.Request) -> HttpxResponse:
        logger.info("QUERY %s %s", request.method, request.url)
        if request.method != "POST":
            return _not_allowed()

        body = _parse_body(request)
        if "object" in body:
            return _handle_object_query(body)
        if "operation" in body:
            return _handle_operation_query(body)
        return _json({"message": "Invalid query request"}, 400)

    return dispatcher


# ── Route setup ──────────────────────────────────────────────────────


def setup_mapi_routes(
    mock: respx.MockRouter, state: MockMapiState, hcp_base: str
) -> None:
    """Register catch-all respx routes for MAPI and Query APIs."""
    mock.route(url__startswith=hcp_base).mock(side_effect=_make_mapi_dispatcher(state))

    # Query API: https://*.*/query
    mock.route(method="POST", url__regex=r"https://[^/]+/query$").mock(
        side_effect=_make_query_dispatcher()
    )
