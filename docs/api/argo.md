# Argo Workflows with HCP S3

[Argo Workflows](https://argoproj.github.io/workflows/) can use HCP as an S3-compatible artifact store. This enables pipelines to read input data from and write results back to HCP namespaces. The examples below show how to configure Argo to work with the HCP API's S3 credentials endpoint and presigned URLs.

All examples are provided in both **YAML** (native Argo manifests) and **[Hera](https://github.com/argoproj-labs/hera)** (Python SDK for Argo Workflows).

## Configuring HCP S3 credentials for Argo

First, retrieve the S3 credentials from the API and create a Kubernetes Secret that Argo can reference:

=== "curl"

    ```bash
    BASE="http://localhost:8000/api/v1"
    TOKEN="<your-token>"

    # Fetch S3 credentials from the HCP API
    CREDS=$(curl -s "$BASE/credentials" -H "Authorization: Bearer $TOKEN")

    ACCESS_KEY=$(echo "$CREDS" | jq -r .access_key_id)
    SECRET_KEY=$(echo "$CREDS" | jq -r .secret_access_key)
    ENDPOINT=$(echo "$CREDS" | jq -r .endpoint_url)

    # Create Kubernetes Secret for Argo
    kubectl create secret generic hcp-s3-credentials \
      --from-literal=accessKey="$ACCESS_KEY" \
      --from-literal=secretKey="$SECRET_KEY" \
      -n argo
    ```

=== "Python"

    ```python
    import httpx
    import subprocess

    BASE = "http://localhost:8000/api/v1"

    async def create_argo_s3_secret(token: str, namespace: str = "argo"):
        """Fetch HCP S3 credentials and create a Kubernetes Secret for Argo."""
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
            resp = await c.get("/credentials")
            resp.raise_for_status()
            creds = resp.json()

        subprocess.run(
            [
                "kubectl", "create", "secret", "generic", "hcp-s3-credentials",
                f"--from-literal=accessKey={creds['access_key_id']}",
                f"--from-literal=secretKey={creds['secret_access_key']}",
                "-n", namespace,
                "--dry-run=client", "-o", "yaml",
            ],
            check=True,
        )
    ```

### Python container image

The Python-based Argo templates below use `httpx` for HTTP calls. Since `python:3.13-slim` does not include httpx, build a small custom image:

```dockerfile
FROM python:3.13-slim
RUN pip install --no-cache-dir httpx
```

```bash
docker build -t my-registry/python-httpx:3.13 .
docker push my-registry/python-httpx:3.13
```

All examples below reference this image as **`my-registry/python-httpx:3.13`** -- replace with your actual registry path.

### Installing Hera

[Hera](https://github.com/argoproj-labs/hera) lets you define Argo Workflows entirely in Python instead of YAML. Install it with:

```bash
uv add hera
```

---

## ETL pipeline with HCP S3 artifacts

A workflow that reads a dataset from HCP, processes it, and writes results back:

=== "YAML"

    ```yaml
    apiVersion: argoproj.io/v1alpha1
    kind: Workflow
    metadata:
      generateName: hcp-etl-
    spec:
      entrypoint: etl-pipeline
      activeDeadlineSeconds: 1800        # workflow-level timeout: 30 min
      artifactGC:
        strategy: OnWorkflowDeletion
      templates:
        - name: etl-pipeline
          dag:
            tasks:
              - name: extract
                template: extract-data
              - name: transform
                template: transform-data
                dependencies: [extract]
              - name: load
                template: load-results
                dependencies: [transform]

        - name: extract-data
          retryStrategy:
            limit: 3
            backoff:
              duration: "5s"
              factor: 2
              maxDuration: "1m"
          container:
            image: python:3.13-slim
            command: [python, -c]
            args:
              - |
                from pathlib import Path
                import json
                # Read the input artifact (mounted by Argo from HCP S3)
                data = json.loads(Path("/tmp/input/manifest.json").read_text())
                print(f"Loaded {len(data['files'])} files from manifest")
                # Write output for next step
                Path("/tmp/output/extracted.json").write_text(json.dumps(data))
          inputs:
            artifacts:
              - name: input-manifest
                path: /tmp/input/manifest.json
                s3:
                  endpoint: hcp-s3.example.com
                  bucket: datasets
                  key: manifests/latest.json
                  accessKeySecret:
                    name: hcp-s3-credentials
                    key: accessKey
                  secretKeySecret:
                    name: hcp-s3-credentials
                    key: secretKey
                  insecure: false
          outputs:
            artifacts:
              - name: extracted
                path: /tmp/output/extracted.json

        - name: transform-data
          retryStrategy:
            limit: 3
            backoff:
              duration: "5s"
              factor: 2
              maxDuration: "1m"
          container:
            image: python:3.13-slim
            command: [python, -c]
            args:
              - |
                from pathlib import Path
                import json
                data = json.loads(Path("/tmp/input/extracted.json").read_text())
                results = {"processed": len(data.get("files", [])), "status": "ok"}
                Path("/tmp/output/results.json").write_text(json.dumps(results))
          inputs:
            artifacts:
              - name: extracted
                path: /tmp/input/extracted.json
          outputs:
            artifacts:
              - name: results
                path: /tmp/output/results.json

        - name: load-results
          retryStrategy:
            limit: 3
            backoff:
              duration: "5s"
              factor: 2
              maxDuration: "1m"
          container:
            image: python:3.13-slim
            command: [python, -c]
            args:
              - |
                from pathlib import Path
                data = Path("/tmp/input/results.json").read_text()
                print(f"Results uploaded to HCP: {data}")
          inputs:
            artifacts:
              - name: results
                path: /tmp/input/results.json
          outputs:
            artifacts:
              - name: final-results
                path: /tmp/input/results.json
                s3:
                  endpoint: hcp-s3.example.com
                  bucket: results
                  key: "etl/{{workflow.name}}/results.json"
                  accessKeySecret:
                    name: hcp-s3-credentials
                    key: accessKey
                  secretKeySecret:
                    name: hcp-s3-credentials
                    key: secretKey
    ```

=== "Hera"

    ```python
    from hera.workflows import (
        DAG,
        Artifact,
        S3Artifact,
        Workflow,
        models as m,
        script,
    )

    HCP_S3 = m.S3Artifact(
        endpoint="hcp-s3.example.com",
        bucket="datasets",
        access_key_secret=m.SecretKeySelector(name="hcp-s3-credentials", key="accessKey"),
        secret_key_secret=m.SecretKeySelector(name="hcp-s3-credentials", key="secretKey"),
        insecure=False,
    )

    RETRY = m.RetryStrategy(
        limit="3",
        backoff=m.Backoff(duration="5s", factor=2, max_duration="1m"),
    )


    @script(image="python:3.13-slim", retry_strategy=RETRY)
    def extract_data(manifest: Artifact) -> Artifact:
        """Read input from HCP S3, write extracted data."""
        from pathlib import Path
        import json

        data = json.loads(Path("/tmp/input/manifest.json").read_text())
        print(f"Loaded {len(data['files'])} files from manifest")
        Path("/tmp/output/extracted.json").write_text(json.dumps(data))


    @script(image="python:3.13-slim", retry_strategy=RETRY)
    def transform_data(extracted: Artifact) -> Artifact:
        """Process the extracted data."""
        from pathlib import Path
        import json

        data = json.loads(Path("/tmp/input/extracted.json").read_text())
        results = {"processed": len(data.get("files", [])), "status": "ok"}
        Path("/tmp/output/results.json").write_text(json.dumps(results))


    @script(image="python:3.13-slim", retry_strategy=RETRY)
    def load_results(results: Artifact) -> Artifact:
        """Upload results back to HCP S3."""
        from pathlib import Path

        data = Path("/tmp/input/results.json").read_text()
        print(f"Results uploaded to HCP: {data}")


    with Workflow(
        generate_name="hcp-etl-",
        entrypoint="etl-pipeline",
        active_deadline_seconds=1800,
        artifact_gc=m.ArtifactGC(strategy="OnWorkflowDeletion"),
    ) as w:
        with DAG(name="etl-pipeline"):
            ext = extract_data(
                name="extract",
                arguments=[
                    S3Artifact(
                        name="manifest",
                        path="/tmp/input/manifest.json",
                        **HCP_S3.dict() | {"key": "manifests/latest.json"},
                    ),
                ],
            )
            trn = transform_data(
                name="transform",
                arguments=[ext.get_artifact("extracted").with_name("extracted")],
            )
            ld = load_results(
                name="load",
                arguments=[trn.get_artifact("results").with_name("results")],
            )
            ext >> trn >> ld

    w.create()  # submit to the Argo server
    ```

---

## Presigned URL pipeline

For cases where you cannot mount S3 credentials into every pod, use the HCP API to generate presigned URLs and pass them as parameters:

=== "YAML"

    ```yaml
    apiVersion: argoproj.io/v1alpha1
    kind: Workflow
    metadata:
      generateName: hcp-presign-
    spec:
      entrypoint: presigned-pipeline
      activeDeadlineSeconds: 900         # workflow-level timeout: 15 min
      arguments:
        parameters:
          - name: hcp-api-base
            value: "http://hcp-api.default.svc:8000/api/v1"
          - name: hcp-token
            value: "<your-token>"
          - name: bucket
            value: "datasets"
      templates:
        - name: presigned-pipeline
          steps:
            - - name: generate-urls
                template: presign
            - - name: process
                template: process-with-urls
                arguments:
                  parameters:
                    - name: download-url
                      value: "{{steps.generate-urls.outputs.parameters.download-url}}"
                    - name: upload-url
                      value: "{{steps.generate-urls.outputs.parameters.upload-url}}"

        - name: presign
          retryStrategy:
            limit: 3
            backoff:
              duration: "5s"
              factor: 2
          script:
            image: curlimages/curl:latest
            command: [sh]
            source: |
              BASE="{{workflow.parameters.hcp-api-base}}"
              TOKEN="{{workflow.parameters.hcp-token}}"
              BUCKET="{{workflow.parameters.bucket}}"

              # Get download URL for input
              DL=$(curl -s -X POST "$BASE/presign" \
                -H "Authorization: Bearer $TOKEN" \
                -H "Content-Type: application/json" \
                -d "{\"bucket\":\"$BUCKET\",\"key\":\"input/data.csv\",\"method\":\"get_object\",\"expires_in\":3600}")
              echo "$DL" | grep -o '"url":"[^"]*"' | cut -d'"' -f4 > /tmp/download-url

              # Get upload URL for output
              UL=$(curl -s -X POST "$BASE/presign" \
                -H "Authorization: Bearer $TOKEN" \
                -H "Content-Type: application/json" \
                -d "{\"bucket\":\"$BUCKET\",\"key\":\"output/result.csv\",\"method\":\"put_object\",\"expires_in\":3600}")
              echo "$UL" | grep -o '"url":"[^"]*"' | cut -d'"' -f4 > /tmp/upload-url
          outputs:
            parameters:
              - name: download-url
                valueFrom:
                  path: /tmp/download-url
              - name: upload-url
                valueFrom:
                  path: /tmp/upload-url

        - name: process-with-urls
          retryStrategy:
            limit: 2
            backoff:
              duration: "10s"
              factor: 2
          inputs:
            parameters:
              - name: download-url
              - name: upload-url
          script:
            image: my-registry/python-httpx:3.13
            command: [python]
            source: |
              import httpx
              from pathlib import Path

              # Download input via presigned URL (no credentials needed)
              resp = httpx.get("{{inputs.parameters.download-url}}")
              resp.raise_for_status()
              Path("/tmp/data.csv").write_bytes(resp.content)

              # Process...
              Path("/tmp/result.csv").write_text("processed,data\n")

              # Upload result via presigned URL
              data = Path("/tmp/result.csv").read_bytes()
              httpx.put("{{inputs.parameters.upload-url}}", content=data).raise_for_status()
              print("Done: input downloaded and result uploaded via presigned URLs")
    ```

=== "Hera"

    ```python
    from hera.workflows import (
        Parameter,
        Steps,
        Workflow,
        models as m,
        script,
    )

    HCP_BASE = "http://hcp-api.default.svc:8000/api/v1"

    RETRY = m.RetryStrategy(
        limit="3",
        backoff=m.Backoff(duration="5s", factor=2),
    )


    @script(image="curlimages/curl:latest", retry_strategy=RETRY)
    def generate_presigned_urls(
        hcp_api_base: str,
        hcp_token: str,
        bucket: str,
    ):
        """Generate download and upload presigned URLs from the HCP API."""
        import subprocess, json

        def presign(key: str, method: str) -> str:
            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST", f"{hcp_api_base}/presign",
                    "-H", f"Authorization: Bearer {hcp_token}",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps({
                        "bucket": bucket, "key": key,
                        "method": method, "expires_in": 3600,
                    }),
                ],
                capture_output=True, text=True, check=True,
            )
            return json.loads(result.stdout)["url"]

        dl = presign("input/data.csv", "get_object")
        ul = presign("output/result.csv", "put_object")

        # Write outputs for Argo parameter extraction
        from pathlib import Path
        Path("/tmp/download-url").write_text(dl)
        Path("/tmp/upload-url").write_text(ul)


    @script(
        image="my-registry/python-httpx:3.13",
        retry_strategy=m.RetryStrategy(limit="2", backoff=m.Backoff(duration="10s", factor=2)),
    )
    def process_with_urls(download_url: str, upload_url: str):
        """Download input, process, and upload result via presigned URLs."""
        import httpx
        from pathlib import Path

        resp = httpx.get(download_url)
        resp.raise_for_status()
        Path("/tmp/data.csv").write_bytes(resp.content)

        Path("/tmp/result.csv").write_text("processed,data\n")

        data = Path("/tmp/result.csv").read_bytes()
        httpx.put(upload_url, content=data).raise_for_status()
        print("Done: input downloaded and result uploaded via presigned URLs")


    with Workflow(
        generate_name="hcp-presign-",
        entrypoint="presigned-pipeline",
        active_deadline_seconds=900,
        arguments=[
            Parameter(name="hcp-api-base", value=HCP_BASE),
            Parameter(name="hcp-token", value="<your-token>"),
            Parameter(name="bucket", value="datasets"),
        ],
    ) as w:
        with Steps(name="presigned-pipeline"):
            urls = generate_presigned_urls(
                name="generate-urls",
                arguments={
                    "hcp_api_base": "{{workflow.parameters.hcp-api-base}}",
                    "hcp_token": "{{workflow.parameters.hcp-token}}",
                    "bucket": "{{workflow.parameters.bucket}}",
                },
            )
            process_with_urls(
                name="process",
                arguments={
                    "download_url": urls.get_parameter("download-url"),
                    "upload_url": urls.get_parameter("upload-url"),
                },
            )

    w.create()
    ```

---

## Running Hera workflows

```bash
# Submit directly from a script
uv run --with hera python etl_workflow.py

# Or export to YAML and submit with Argo CLI
uv run --with hera python -c "
from etl_workflow import w
print(w.to_yaml())
" | argo submit -

# Useful during development: validate without submitting
uv run --with hera python -c "
from etl_workflow import w
print(w.to_yaml())
" | argo lint -
```

---

## Batch processing -- fan-out over HCP objects

A common pattern: list objects from an HCP bucket, process each one in parallel (fan-out), then aggregate results (fan-in).

=== "YAML"

    ```yaml
    apiVersion: argoproj.io/v1alpha1
    kind: Workflow
    metadata:
      generateName: hcp-batch-
    spec:
      entrypoint: batch-pipeline
      arguments:
        parameters:
          - name: hcp-api-base
            value: "http://hcp-api.default.svc:8000/api/v1"
          - name: hcp-token
            value: "<your-token>"
          - name: bucket
            value: "datasets"
          - name: prefix
            value: "incoming/"
      templates:
        # ── Orchestrator DAG ─────────────────────────────────────────
        - name: batch-pipeline
          dag:
            tasks:
              - name: discover
                template: list-objects
              - name: process
                template: fan-out
                dependencies: [discover]
                arguments:
                  parameters:
                    - name: object-keys
                      value: "{{tasks.discover.outputs.parameters.keys}}"
              - name: summarize
                template: aggregate
                dependencies: [process]

        # ── Step 1: List objects from HCP via the API ────────────────
        - name: list-objects
          retryStrategy:
            limit: 3
            backoff:
              duration: "5s"
              factor: 2
          script:
            image: curlimages/curl:latest
            command: [sh]
            source: |
              BASE="{{workflow.parameters.hcp-api-base}}"
              TOKEN="{{workflow.parameters.hcp-token}}"
              BUCKET="{{workflow.parameters.bucket}}"
              PREFIX="{{workflow.parameters.prefix}}"

              RESP=$(curl -s -f "$BASE/s3/buckets/$BUCKET/objects?prefix=$PREFIX&max_keys=100" \
                -H "Authorization: Bearer $TOKEN")

              # Extract object keys as a JSON array
              echo "$RESP" | jq '[.objects[].key]' > /tmp/keys.json
              echo "Found $(echo "$RESP" | jq '.objects | length') objects"
              cat /tmp/keys.json
          outputs:
            parameters:
              - name: keys
                valueFrom:
                  path: /tmp/keys.json

        # ── Step 2: Fan out — one pod per object ─────────────────────
        - name: fan-out
          inputs:
            parameters:
              - name: object-keys
          steps:
            - - name: process-object
                template: process-single
                arguments:
                  parameters:
                    - name: key
                      value: "{{item}}"
                withParam: "{{inputs.parameters.object-keys}}"

        - name: process-single
          retryStrategy:
            limit: 2
            backoff:
              duration: "10s"
              factor: 2
          inputs:
            parameters:
              - name: key
          script:
            image: my-registry/python-httpx:3.13
            command: [python]
            source: |
              import httpx, json, os
              from pathlib import Path

              BASE = "{{workflow.parameters.hcp-api-base}}"
              TOKEN = "{{workflow.parameters.hcp-token}}"
              BUCKET = "{{workflow.parameters.bucket}}"
              KEY = "{{inputs.parameters.key}}"
              headers = {"Authorization": f"Bearer {TOKEN}"}

              # Get a presigned download URL from the HCP API
              resp = httpx.post(
                  f"{BASE}/s3/presign",
                  json={"bucket": BUCKET, "key": KEY, "method": "get_object", "expires_in": 600},
                  headers=headers,
              )
              url = resp.json()["url"]

              # Download and process the object
              resp = httpx.get(url)
              resp.raise_for_status()
              Path("/tmp/data").write_bytes(resp.content)
              size = os.path.getsize("/tmp/data")
              result = {"key": KEY, "size": size, "status": "processed"}
              print(json.dumps(result))

              # Upload result back via presigned PUT
              result_key = KEY.replace("incoming/", "processed/") + ".result.json"
              resp = httpx.post(
                  f"{BASE}/s3/presign",
                  json={"bucket": BUCKET, "key": result_key, "method": "put_object", "expires_in": 600},
                  headers=headers,
              )
              upload_url = resp.json()["url"]
              httpx.put(upload_url, content=json.dumps(result).encode()).raise_for_status()
              print(f"Result uploaded to {result_key}")

        # ── Step 3: Fan in — aggregate results ───────────────────────
        - name: aggregate
          retryStrategy:
            limit: 2
          script:
            image: curlimages/curl:latest
            command: [sh]
            source: |
              BASE="{{workflow.parameters.hcp-api-base}}"
              TOKEN="{{workflow.parameters.hcp-token}}"
              BUCKET="{{workflow.parameters.bucket}}"

              # List all processed results
              RESULTS=$(curl -s -f "$BASE/s3/buckets/$BUCKET/objects?prefix=processed/&max_keys=1000" \
                -H "Authorization: Bearer $TOKEN")

              COUNT=$(echo "$RESULTS" | jq '.objects | length')
              SUMMARY="{\"workflow\":\"{{workflow.name}}\",\"objects_processed\":$COUNT,\"status\":\"complete\"}"
              echo "$SUMMARY"

              # Upload summary via presigned URL
              PRESIGN=$(curl -s -X POST "$BASE/s3/presign" \
                -H "Authorization: Bearer $TOKEN" \
                -H "Content-Type: application/json" \
                -d "{\"bucket\":\"$BUCKET\",\"key\":\"summaries/{{workflow.name}}.json\",\"method\":\"put_object\",\"expires_in\":600}")
              UPLOAD_URL=$(echo "$PRESIGN" | jq -r '.url')
              curl -s -X PUT "$UPLOAD_URL" -d "$SUMMARY"
              echo "Summary uploaded"
    ```

=== "Hera"

    ```python
    from hera.workflows import (
        DAG,
        Parameter,
        Steps,
        Workflow,
        models as m,
        script,
    )

    HCP_BASE = "http://hcp-api.default.svc:8000/api/v1"

    RETRY = m.RetryStrategy(
        limit="3",
        backoff=m.Backoff(duration="5s", factor=2),
    )


    @script(image="curlimages/curl:latest", retry_strategy=RETRY)
    def list_objects(hcp_api_base: str, hcp_token: str, bucket: str, prefix: str):
        """List objects from HCP and output their keys as a JSON array."""
        import subprocess, json

        result = subprocess.run(
            [
                "curl", "-s", "-f",
                f"{hcp_api_base}/s3/buckets/{bucket}/objects?prefix={prefix}&max_keys=100",
                "-H", f"Authorization: Bearer {hcp_token}",
            ],
            capture_output=True, text=True, check=True,
        )
        objects = json.loads(result.stdout)["objects"]
        keys = [obj["key"] for obj in objects]
        print(f"Found {len(keys)} objects")

        from pathlib import Path
        Path("/tmp/keys.json").write_text(json.dumps(keys))


    @script(
        image="my-registry/python-httpx:3.13",
        retry_strategy=m.RetryStrategy(limit="2", backoff=m.Backoff(duration="10s", factor=2)),
    )
    def process_single(hcp_api_base: str, hcp_token: str, bucket: str, key: str):
        """Download an object via presigned URL, process it, upload the result."""
        import httpx, json, os
        from pathlib import Path

        headers = {"Authorization": f"Bearer {hcp_token}"}

        # Presign download
        resp = httpx.post(
            f"{hcp_api_base}/s3/presign",
            json={"bucket": bucket, "key": key, "method": "get_object", "expires_in": 600},
            headers=headers,
        )
        url = resp.json()["url"]

        # Download and process
        resp = httpx.get(url)
        resp.raise_for_status()
        Path("/tmp/data").write_bytes(resp.content)
        size = os.path.getsize("/tmp/data")
        result = {"key": key, "size": size, "status": "processed"}
        print(json.dumps(result))

        # Presign upload and write result
        result_key = key.replace("incoming/", "processed/") + ".result.json"
        resp = httpx.post(
            f"{hcp_api_base}/s3/presign",
            json={"bucket": bucket, "key": result_key, "method": "put_object", "expires_in": 600},
            headers=headers,
        )
        upload_url = resp.json()["url"]
        httpx.put(upload_url, content=json.dumps(result).encode()).raise_for_status()
        print(f"Result uploaded to {result_key}")


    @script(image="curlimages/curl:latest", retry_strategy=RETRY)
    def aggregate(hcp_api_base: str, hcp_token: str, bucket: str):
        """List processed results and upload a summary."""
        import subprocess, json

        result = subprocess.run(
            [
                "curl", "-s", "-f",
                f"{hcp_api_base}/s3/buckets/{bucket}/objects?prefix=processed/&max_keys=1000",
                "-H", f"Authorization: Bearer {hcp_token}",
            ],
            capture_output=True, text=True, check=True,
        )
        count = len(json.loads(result.stdout)["objects"])
        summary = json.dumps({"objects_processed": count, "status": "complete"})
        print(summary)

        # Upload summary via presigned URL
        presign = subprocess.run(
            [
                "curl", "-s", "-X", "POST", f"{hcp_api_base}/s3/presign",
                "-H", f"Authorization: Bearer {hcp_token}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "bucket": bucket,
                    "key": "summaries/batch-result.json",
                    "method": "put_object", "expires_in": 600,
                }),
            ],
            capture_output=True, text=True, check=True,
        )
        upload_url = json.loads(presign.stdout)["url"]
        subprocess.run(["curl", "-s", "-X", "PUT", upload_url, "-d", summary], check=True)


    WF_PARAMS = {
        "hcp_api_base": "{{workflow.parameters.hcp-api-base}}",
        "hcp_token": "{{workflow.parameters.hcp-token}}",
        "bucket": "{{workflow.parameters.bucket}}",
    }

    with Workflow(
        generate_name="hcp-batch-",
        entrypoint="batch-pipeline",
        arguments=[
            Parameter(name="hcp-api-base", value=HCP_BASE),
            Parameter(name="hcp-token", value="<your-token>"),
            Parameter(name="bucket", value="datasets"),
            Parameter(name="prefix", value="incoming/"),
        ],
    ) as w:
        with DAG(name="batch-pipeline"):
            # Step 1: Discover objects
            disc = list_objects(
                name="discover",
                arguments={**WF_PARAMS, "prefix": "{{workflow.parameters.prefix}}"},
            )
            # Step 2: Fan out — process each object in parallel
            with Steps(name="fan-out") as fan:
                process_single(
                    name="process-object",
                    arguments={
                        **WF_PARAMS,
                        "key": "{{item}}",
                    },
                    with_param=disc.get_parameter("keys"),
                )
            # Step 3: Aggregate results
            agg = aggregate(name="summarize", arguments=WF_PARAMS)

            disc >> fan >> agg

    w.create()
    ```

!!! tip "Which approach to use?"
    - **S3 artifacts** (YAML or Hera DAG): Best when Argo has direct network access to HCP S3. Argo handles download/upload automatically. Requires the S3 credentials Secret.
    - **Presigned URLs** (YAML or Hera Steps): Best when pods cannot reach HCP directly or you want to avoid distributing S3 credentials. The HCP API generates short-lived URLs that anyone can use.
    - **Batch fan-out**: Use `withParam` (YAML) or `with_param` (Hera) to process N objects in parallel. Argo handles scheduling and concurrency limits.
    - **YAML vs Hera**: Use YAML for simple workflows or when non-Python teams maintain them. Use Hera when you want type safety, IDE autocompletion, and Python-native DAG composition (`>>` operator).

---

## Related pages

- [API Workflows](workflows.md) -- curl and Python examples for authentication, S3 operations, tenant/namespace management, and more.
- [Error Handling](error-handling.md) -- Retries, exit handlers, ACID patterns, and Argo-native retry/timeout configuration.
