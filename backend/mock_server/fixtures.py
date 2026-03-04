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
            "roles": {"role": ["ADMINISTRATOR", "SECURITY", "MONITOR", "COMPLIANCE"]},
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
            "roles": {"role": ["ADMINISTRATOR", "MONITOR"]},
        },
    },
    "mock": {
        "admin": {
            "username": "admin",
            "fullName": "Mock Admin",
            "description": "Mock tenant administrator",
            "localAuthentication": True,
            "enabled": True,
            "roles": {"role": ["ADMINISTRATOR", "SECURITY", "MONITOR", "COMPLIANCE"]},
        },
        "analyst": {
            "username": "analyst",
            "fullName": "Data Analyst",
            "description": "Read-only data analyst",
            "localAuthentication": True,
            "enabled": True,
            "roles": {"role": ["MONITOR"]},
        },
        "developer": {
            "username": "developer",
            "fullName": "App Developer",
            "description": "Application developer",
            "localAuthentication": True,
            "enabled": True,
            "roles": {"role": ["MONITOR"]},
        },
    },
}

# ── Group accounts (tenant -> groupname -> data) ─────────────────────

GROUP_ACCOUNTS: dict[str, dict[str, dict]] = {
    "default": {
        "admins": {
            "groupname": "admins",
            "description": "Administrator group",
            "roles": {"role": ["ADMINISTRATOR", "SECURITY"]},
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
            "roles": {"role": ["ADMINISTRATOR"]},
        },
    },
    "mock": {
        "administrators": {
            "groupname": "administrators",
            "description": "Tenant administrators",
            "roles": {"role": ["ADMINISTRATOR", "SECURITY"]},
        },
        "developers": {
            "groupname": "developers",
            "description": "Application developers",
            "roles": {"role": ["MONITOR"]},
        },
        "analysts": {
            "groupname": "analysts",
            "description": "Data analysts with read-only access",
            "roles": {"role": ["MONITOR"]},
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
    "chargebackData": [
        {
            "namespaceName": "finance-records",
            "objectCount": 750,
            "ingestedVolume": 32212254720,
            "storageCapacityUsed": 34359738368,
            "bytesIn": 8589934592,
            "bytesOut": 4294967296,
            "reads": 15230,
            "writes": 3420,
            "deletes": 85,
            "valid": True,
        },
        {
            "namespaceName": "compliance-archive",
            "objectCount": 320,
            "ingestedVolume": 16106127360,
            "storageCapacityUsed": 17179869184,
            "bytesIn": 2147483648,
            "bytesOut": 1073741824,
            "reads": 4870,
            "writes": 980,
            "deletes": 12,
            "valid": True,
        },
        {
            "namespaceName": "dev-sandbox",
            "objectCount": 164,
            "ingestedVolume": 2147483648,
            "storageCapacityUsed": 2147483648,
            "bytesIn": 1073741824,
            "bytesOut": 536870912,
            "reads": 2340,
            "writes": 1560,
            "deletes": 230,
            "valid": True,
        },
    ],
}

NS_CHARGEBACK: dict = {
    "chargebackData": [
        {
            "objectCount": 500,
            "bytesIn": 10737418240,
            "bytesOut": 5368709120,
            "reads": 8200,
            "writes": 2100,
            "deletes": 45,
            "valid": True,
        },
    ],
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
