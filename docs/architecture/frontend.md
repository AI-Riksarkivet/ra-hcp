# Frontend Architecture

The SvelteKit frontend follows a reactive pattern with remote function abstractions and server-side RBAC:

```mermaid
graph TD
    HOOK["hooks.server.ts<br/>extract JWT cookie"] --> LAYOUT["+layout.server.ts<br/>fetch user profile · set accessLevel"]
    LAYOUT --> GUARD["+page.server.ts<br/>requireAdmin() · route guards"]
    GUARD --> PAGE["+page.svelte<br/>components · reactive state"]

    PAGE --> Q["query()<br/>GET with caching"]
    PAGE --> C["command()<br/>mutations"]
    C -->|".updates(queryData)"| Q

    Q --> REM["*.remote.ts"]
    C --> REM
    REM -->|"fetch()"| API["FastAPI Backend"]
```

## RBAC

The frontend enforces role-based access control entirely on the server side, making it impossible to bypass via client-side manipulation.

```mermaid
sequenceDiagram
    participant B as Browser
    participant H as hooks.server.ts
    participant L as +layout.server.ts
    participant G as +page.server.ts
    participant A as FastAPI Backend

    B->>H: Request /tenant-settings
    H->>H: Extract hcp_token cookie
    H->>L: event.locals.token

    alt No token
        L-->>B: Redirect → /login
    else Has token
        L->>L: Parse JWT (username, tenant)
        L->>A: GET /userAccounts/{username}?verbose=true
        A-->>L: { roles: [ADMINISTRATOR, ...], userGUID }
        L->>L: getAccessLevel(tenant, roles)

        alt sys-admin (no tenant)
            L-->>G: accessLevel = "sys-admin"
        else tenant-admin (has ADMINISTRATOR role)
            L-->>G: accessLevel = "tenant-admin"
        else namespace-user (other roles)
            L-->>G: accessLevel = "namespace-user"
        end

        G->>G: requireAdmin(accessLevel)

        alt namespace-user on admin route
            G-->>B: Redirect → /buckets
        else admin or sys-admin
            G-->>B: Render page
        end
    end
```

### Access levels

| Level | Condition | Visible sidebar sections | Protected routes (redirects to `/buckets`) |
|-------|-----------|--------------------------|---------------------------------------------|
| **sys-admin** | No tenant in JWT | All sections | None — full access |
| **tenant-admin** | Has `ADMINISTRATOR` role | All sections | None — full access to tenant |
| **namespace-user** | Any other role set | Storage, Analytics | `/namespaces`, `/users`, `/tenant-settings`, `/search`, `/content-classes` |
