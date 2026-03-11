# Architecture

This page describes the overall design of the HCP application, how the backend and frontend work together, and the key architectural decisions.

## System Overview

```mermaid
graph TB
    subgraph "Browser"
        FE["SvelteKit Frontend<br/>:5173"]
    end

    subgraph "Backend"
        API["FastAPI<br/>:8000"]
        SVC["Services<br/>MAPI · S3 · Query · Cache"]
    end

    subgraph "External"
        HCP["HCP System<br/>:9090"]
        S3EP["S3 Endpoint"]
        REDIS["Redis (optional)"]
    end

    FE -->|"REST + JWT"| API
    API --> SVC
    SVC -->|"HTTPS"| HCP
    SVC -->|"S3"| S3EP
    SVC --> REDIS
```

## Request Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant F as SvelteKit
    participant A as FastAPI
    participant S as Services
    participant H as HCP System

    B->>F: User action
    F->>A: HTTP + JWT
    A->>A: Decode JWT → credentials
    A->>S: Forward request

    alt Cache hit
        S-->>A: Cached response
    else Cache miss
        S->>H: MAPI/S3 request
        H-->>S: Response
        S-->>A: Cache + return
    end

    A-->>F: JSON response
    F-->>B: Update UI
```
