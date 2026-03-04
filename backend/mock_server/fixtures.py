"""Static fixture data for the mock MAPI server.

All dicts are keyed by resource name for O(1) lookups in the stateful mock.
"""

from __future__ import annotations

# ── Tenants ──────────────────────────────────────────────────────────

TENANTS: dict[str, dict] = {
    "default": {
        "name": "default",
        "systemVisibleDescription": "Default tenant",
        "hardQuota": "100 GB",
        "softQuota": 90,
        "namespaceQuota": "10",
        "authenticationTypes": {"authenticationType": ["LOCAL"]},
        "tags": {"tag": []},
    },
    "research": {
        "name": "research",
        "systemVisibleDescription": "Research tenant",
        "hardQuota": "500 GB",
        "softQuota": 85,
        "namespaceQuota": "20",
        "authenticationTypes": {"authenticationType": ["LOCAL"]},
        "tags": {"tag": []},
    },
    "mock": {
        "name": "mock",
        "systemVisibleDescription": "Mock development tenant",
        "hardQuota": "250 GB",
        "softQuota": 90,
        "namespaceQuota": "15",
        "authenticationTypes": {"authenticationType": ["LOCAL"]},
        "servicePlan": "Default",
        "tags": {"tag": []},
    },
}

# ── Namespaces (tenant -> ns_name -> data) ───────────────────────────

NAMESPACES: dict[str, dict[str, dict]] = {
    "default": {
        "default-ns": {
            "name": "default-ns",
            "nameIDNA": "default-ns",
            "hardQuota": "50 GB",
            "softQuota": 90,
            "description": "Default namespace",
            "versioningSettings": {"enabled": False},
            "hashScheme": "SHA-256",
            "searchEnabled": True,
        },
        "shared": {
            "name": "shared",
            "nameIDNA": "shared",
            "hardQuota": "30 GB",
            "softQuota": 85,
            "description": "Shared data namespace",
            "versioningSettings": {"enabled": True},
            "hashScheme": "SHA-256",
            "searchEnabled": False,
        },
    },
    "research": {
        "experiments": {
            "name": "experiments",
            "nameIDNA": "experiments",
            "hardQuota": "200 GB",
            "softQuota": 90,
            "description": "Experiment data",
            "versioningSettings": {"enabled": True},
            "hashScheme": "SHA-256",
            "searchEnabled": True,
        },
    },
    "mock": {
        "documents": {
            "name": "documents",
            "nameIDNA": "documents",
            "hardQuota": "100 GB",
            "softQuota": 90,
            "description": "General documents",
            "versioningSettings": {"enabled": False},
            "hashScheme": "SHA-256",
            "searchEnabled": True,
        },
        "archives": {
            "name": "archives",
            "nameIDNA": "archives",
            "hardQuota": "50 GB",
            "softQuota": 90,
            "description": "Archived data",
            "versioningSettings": {"enabled": False},
            "hashScheme": "SHA-256",
            "searchEnabled": False,
        },
        "logs": {
            "name": "logs",
            "nameIDNA": "logs",
            "hardQuota": "25 GB",
            "softQuota": 85,
            "description": "Application logs",
            "versioningSettings": {"enabled": False},
            "hashScheme": "SHA-256",
            "searchEnabled": True,
        },
    },
}

# ── User accounts (tenant -> username -> data) ───────────────────────

USER_ACCOUNTS: dict[str, dict[str, dict]] = {
    "default": {
        "admin": {
            "username": "admin",
            "fullName": "Admin User",
            "description": "Tenant administrator",
            "localAuthentication": True,
            "enabled": True,
            "roles": {"role": ["ADMIN", "SECURITY", "MONITOR", "COMPLIANCE"]},
        },
        "user1": {
            "username": "user1",
            "fullName": "Regular User",
            "description": "Standard user",
            "localAuthentication": True,
            "enabled": True,
            "roles": {"role": ["MONITOR"]},
        },
    },
    "research": {
        "researcher": {
            "username": "researcher",
            "fullName": "Research User",
            "description": "Research tenant admin",
            "localAuthentication": True,
            "enabled": True,
            "roles": {"role": ["ADMIN", "MONITOR"]},
        },
    },
    "mock": {
        "admin": {
            "username": "admin",
            "fullName": "Mock Admin",
            "description": "Mock tenant administrator",
            "localAuthentication": True,
            "enabled": True,
            "roles": {"role": ["ADMIN", "SECURITY", "MONITOR", "COMPLIANCE"]},
        },
    },
}

# ── Group accounts (tenant -> groupname -> data) ─────────────────────

GROUP_ACCOUNTS: dict[str, dict[str, dict]] = {
    "default": {
        "admins": {
            "groupname": "admins",
            "description": "Administrator group",
            "roles": {"role": ["ADMIN", "SECURITY"]},
        },
        "users": {
            "groupname": "users",
            "description": "Regular users group",
            "roles": {"role": ["MONITOR"]},
        },
    },
    "research": {
        "researchers": {
            "groupname": "researchers",
            "description": "Research group",
            "roles": {"role": ["ADMIN"]},
        },
    },
}

# ── Content classes (tenant -> cc_name -> data) ──────────────────────

CONTENT_CLASSES: dict[str, dict[str, dict]] = {
    "default": {
        "document": {
            "name": "document",
            "description": "General documents",
            "contentProperties": [],
        },
    },
    "research": {
        "dataset": {
            "name": "dataset",
            "description": "Research datasets",
            "contentProperties": [],
        },
    },
}

# ── Retention classes ((tenant, ns) -> rc_name -> data) ──────────────

RETENTION_CLASSES: dict[tuple[str, str], dict[str, dict]] = {
    ("default", "default-ns"): {
        "standard": {
            "name": "standard",
            "description": "Standard retention",
            "value": 365,
            "autoDelete": False,
        },
    },
}

# ── Static fixtures (read-only) ─────────────────────────────────────

TENANT_STATISTICS: dict = {
    "objectCount": 1234,
    "bytesUsed": "53687091200",
    "customMetadataObjectCount": 100,
    "shredObjectCount": 0,
    "namespacesUsed": 3,
}

NS_STATISTICS: dict = {
    "objectCount": 500,
    "bytesUsed": "21474836480",
    "customMetadataObjectCount": 50,
    "shredObjectCount": 0,
}

TENANT_CHARGEBACK: dict = {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z",
    "granularity": "total",
    "namespaceChargebackData": [],
}

NS_CHARGEBACK: dict = {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z",
    "granularity": "total",
    "objectCount": 500,
    "bytesIn": "10737418240",
    "bytesOut": "5368709120",
}

AVAILABLE_SERVICE_PLANS: dict[str, dict] = {
    "Default": {
        "name": "Default",
        "description": "Default service plan",
        "tags": {"tag": []},
    },
}

# ── Settings factories ───────────────────────────────────────────────


def default_tenant_settings() -> dict[str, dict]:
    """Return a fresh dict of default tenant-level settings sub-resources."""
    return {
        "consoleSecurity": {
            "ipAddressAllowlist": [],
            "ipAddressDenylist": [],
        },
        "contactInfo": {
            "name": "",
            "email": "",
            "phone": "",
        },
        "emailNotification": {
            "enabled": False,
            "smtpServer": "",
            "smtpPort": 25,
            "senderAddress": "",
        },
        "namespaceDefaults": {
            "hardQuota": "1 GB",
            "softQuota": 90,
            "optimizedFor": "cloud",
            "hashScheme": "SHA-256",
            "searchEnabled": False,
            "versioningEnabled": False,
        },
        "searchSecurity": {
            "ipAddressAllowlist": [],
            "ipAddressDenylist": [],
        },
        "permissions": {
            "namespaceCreateAllowed": True,
            "namespaceDeleteAllowed": True,
            "replicationAllowed": True,
            "searchAllowed": True,
            "complianceAllowed": True,
        },
    }


def default_ns_settings() -> dict[str, dict]:
    """Return a fresh dict of default namespace-level settings sub-resources."""
    return {
        "complianceSettings": {
            "enabledModes": ["enterprise"],
            "allowDisablingCompliance": True,
        },
        "protocols": {
            "default": {
                "httpEnabled": True,
                "httpsEnabled": True,
                "cifsEnabled": False,
                "nfsEnabled": False,
                "smtpEnabled": False,
            },
            "http": {
                "enabled": True,
                "httpsRequired": False,
                "hsIncludedPaths": [],
                "hsExcludedPaths": [],
                "allowOrigins": [],
                "exposeHeaders": [],
                "allowHeaders": [],
            },
            "cifs": {
                "enabled": False,
                "caseSensitiveNamespaces": False,
            },
            "nfs": {
                "enabled": False,
                "uid": 0,
                "gid": 0,
            },
            "smtp": {
                "enabled": False,
                "emailDomain": "",
            },
        },
        "permissions": {
            "readAllowed": True,
            "writeAllowed": True,
            "deleteAllowed": True,
            "purgeAllowed": False,
            "searchAllowed": True,
            "readAclAllowed": True,
            "writeAclAllowed": True,
        },
        "cors": {
            "corsConfiguration": [],
        },
        "customMetadataIndexingSettings": {
            "indexingEnabled": False,
        },
        "replicationCollisionSettings": {
            "dispositionAction": "log",
        },
        "versioningSettings": {
            "enabled": False,
            "pruneDaysAfterDelete": 0,
        },
    }
