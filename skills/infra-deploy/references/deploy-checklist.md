# Deploy checklist

## Dockerfile template

A Node service as the example. The shape carries to other runtimes: build stage, slim runtime stage,
non root user, exec form start command.

```
# syntax=docker/dockerfile:1
FROM node:22-slim@sha256:<digest> AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM node:22-slim@sha256:<digest>
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist
USER node
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "dist/server.js"]
```

Replace `<digest>` with the digest from `docker buildx imagetools inspect node:22-slim`, and pick the
current supported runtime version from its release schedule. Build with the secret supplied at build
time only:

```
DOCKER_BUILDKIT=1 docker build --secret id=npmrc,src=$HOME/.npmrc -t app:$(git rev-parse --short HEAD) .
```

`.dockerignore` at minimum:

```
.git
.env*
node_modules
dist
coverage
*.log
```

Check the result:

```
docker history --no-trunc app:TAG | grep -i -E 'token|secret|password'   # expect nothing
docker run -d --name app app:TAG && docker stop app && docker logs app     # expect a clean shutdown line
```

## Probe semantics

| Probe | Question it answers | On failure | Check | Never check |
|---|---|---|---|---|
| Liveness | Is this process stuck beyond recovery? | Container restarted | The process can serve a trivial request; event loop or worker threads not wedged | Databases, caches, other services |
| Readiness | Should this instance get traffic now? | Removed from load balancing, not restarted | Warm-up finished, local resources ready, not shutting down | A dependency every instance shares, since all instances fail together |
| Startup | Has the process finished booting? | Restarted after the threshold; liveness and readiness wait until it passes | Same endpoint as liveness, with a longer allowance | Anything that makes boot depend on another service being up |

Kubernetes reads these from the pod spec and ignores the Dockerfile `HEALTHCHECK`. On readiness failure
during shutdown, return failure as soon as SIGTERM arrives, so the instance drains.

## Pipeline hardening

```
permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write          # OIDC token for this job only
    steps:
      - uses: actions/checkout@<full-40-character-commit-sha>   # vX.Y.Z
      - uses: aws-actions/configure-aws-credentials@<full-40-character-commit-sha>   # vX.Y.Z
        with:
          role-to-assume: arn:aws:iam::<account-id>:role/deploy-main
          aws-region: <region>
```

Fill the angle bracket values with real ones; the version comment lets Renovate or Dependabot update the
SHA. Restrict the cloud role's trust policy to this repository and the default branch (the OIDC `sub`
claim), so a fork or another branch cannot assume it. Use the equivalent workload identity federation on
GCP and federated credentials on Azure.

Other checks:

- No `pull_request_target` workflow checks out or runs pull request code.
- Deploy jobs run in a protected environment that requires approval for production.
- Secrets are never echoed; masked output is not a guarantee, so do not print derived values.
- Third party images in the pipeline are pinned by digest.

## Cost line items to retrieve

Retrieve each from the provider's pricing page for the region in use, and record the date. Do not reuse
figures from memory or from this file.

- Compute: instance or vCPU and memory hours, including idle non-production environments.
- NAT gateway: hourly charge per gateway and per GB processed. Traffic from private subnets to the internet or to the provider's own services without a VPC endpoint passes through it.
- Data transfer between availability zones, charged per GB and often in both directions. Chatty services spread across zones pay it on every call.
- Internet egress per GB, and CDN egress if used.
- Load balancers: hourly charge plus capacity units, including ones left running for old environments.
- Managed databases: instance hours, storage, IOPS, backups beyond the free allowance, and replicas.
- Log ingestion and retention, and metrics with high cardinality.
- Container registry storage and image pulls across regions.
- Public IPv4 addresses, where the provider charges for them.
- Secrets manager, KMS keys and API calls.
