# Frontend Architecture

The SvelteKit frontend follows a reactive pattern with remote function abstractions and server-side RBAC:

```mermaid
graph TD
    subgraph "Pages"
        P["SvelteKit Routes<br/>+page.svelte"]
        L["Layout Server Load<br/>+layout.server.ts"]
        G["Route Guards<br/>+page.server.ts"]
    end

    subgraph "RBAC"
        HOOK["Server Hook<br/>Token extraction"]
        AL["Access Levels<br/>sys-admin · tenant-admin<br/>namespace-user"]
        GUARD["requireAdmin()<br/>Server-side redirect"]
    end

    subgraph "Components"
        UI["UI Components<br/>DataTable · FormDialog<br/>FileViewer · etc."]
        FEAT["Feature Components<br/>Namespace settings<br/>User management"]
        SIDE["Sidebar<br/>Role-conditional sections"]
    end

    subgraph "Data Layer"
        Q["query()<br/>GET requests with caching"]
        C["command()<br/>POST/PUT/DELETE mutations"]
        REM["Remote Functions<br/>*.remote.ts"]
    end

    subgraph "State"
        ST["$state<br/>Mutable reactive state"]
        DER["$derived<br/>Computed values"]
        EFF["$effect<br/>Side effects"]
    end

    HOOK -->|"JWT cookie"| L
    L -->|"fetch user profile"| REM
    L -->|"accessLevel"| AL
    AL --> G
    G -->|"namespace-user → /buckets"| GUARD
    L --> P
    P --> UI
    P --> FEAT
    SIDE -->|"isAdmin filter"| AL
    FEAT --> Q
    FEAT --> C
    Q --> REM
    C --> REM
    REM -->|"fetch()"| API2["FastAPI Backend"]
    P --> ST
    P --> DER
    P --> EFF
    C -->|".updates(queryData)"| Q
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

| Level | Condition | Access |
|-------|-----------|--------|
| **sys-admin** | No tenant in JWT | Full access to all routes |
| **tenant-admin** | Has `ADMINISTRATOR` role | Full access to tenant routes |
| **namespace-user** | Any other role set | Storage routes only (buckets, access control, analytics, settings) |

### Protected routes

These routes call `requireAdmin()` in their `+page.server.ts` and redirect non-admin users to `/buckets`:

- `/namespaces`, `/namespaces/[namespace]`
- `/users`, `/users/[username]`, `/users/groups/[groupname]`
- `/tenant-settings`
- `/search`
- `/content-classes`, `/content-classes/[name]`

### Sidebar filtering

The sidebar conditionally renders sections based on access level:

- **All users**: Storage (Buckets, Access Control), Analytics (Data Explorer)
- **Admins only**: Tenant (Namespaces, Users & Groups, Tenant Settings), Search & Indexing (Search, Content Classes)

## Patterns

- **Remote functions**: All API calls are defined in `*.remote.ts` files using `query()` for reads and `command()` for mutations.

- **Mutation refresh**: After a mutation, `command(...).updates(queryData)` automatically invalidates and refetches the relevant query data.

- **Svelte 5 runes**: Components use `$state` for mutable state, `$derived` for computed values, and `$effect` for async side effects with cancellation.
