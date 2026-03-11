# Architecture

This page describes the overall design of the HCP application, how the backend and frontend work together, and the key architectural decisions.

## System Overview

```mermaid
graph TB
    subgraph "Browser"
        FE["SvelteKit Frontend<br/>:5173"]
    end

    subgraph "Backend Server"
        API["FastAPI Backend<br/>:8000"]
        MW["Middleware Stack<br/>CORS · GZip · RequestID"]
        AUTH["JWT Auth<br/>OAuth2 Password Flow"]
    end

    subgraph "Services Layer"
        MAPI["MapiService<br/>HCP Management API"]
        S3["StorageProtocol<br/>Backend-agnostic S3"]
        QUERY["QueryService<br/>Metadata Query"]
        CACHE["CacheService<br/>Redis (optional)"]
    end

    subgraph "External Systems"
        HCP["HCP System<br/>Management API :9090"]
        S3EP["HCP S3 Endpoint<br/>Object Storage"]
        REDIS["Redis<br/>(optional)"]
    end

    FE -->|"REST API<br/>JWT Bearer"| API
    API --> MW --> AUTH
    AUTH --> MAPI
    AUTH --> S3
    AUTH --> QUERY
    MAPI --> CACHE
    S3 --> CACHE
    QUERY --> CACHE
    MAPI -->|"HTTPS :9090"| HCP
    S3 -->|"S3 Protocol"| S3EP
    QUERY -->|"HTTPS"| HCP
    CACHE -->|"Redis Protocol"| REDIS
```

## Request Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant F as SvelteKit
    participant A as FastAPI
    participant M as Middleware
    participant S as Service Layer
    participant H as HCP System

    B->>F: User action (click, form submit)
    F->>A: HTTP request + JWT token
    A->>M: RequestID + GZip + CORS
    M->>M: Decode JWT → extract credentials
    M->>S: Forward with HCP credentials

    alt Cache hit (Redis enabled)
        S-->>M: Return cached response
    else Cache miss or no Redis
        S->>H: MAPI/S3 request with credentials
        H-->>S: HCP response
        S->>S: Cache response (if Redis enabled)
        S-->>M: Return response
    end

    M-->>A: Add X-Request-ID header
    A-->>F: JSON response
    F-->>B: Update UI reactively
```
