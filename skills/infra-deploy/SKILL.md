---
name: infra-deploy
description: Set up hosting, containers, pipelines and environments so a deploy is boring and reversible. Use when the user asks how to deploy, host or ship an application, asks about Docker, docker compose, Kubernetes, Helm, Terraform, CI/CD, GitHub Actions, AWS, ECS, Lambda, GCP, Cloud Run, Azure, serverless, Vercel, Fly.io or a VPS, asks about nginx, an SSL certificate, a domain or DNS, environment variables, secrets, staging environments, zero downtime deploys or rollback, or asks why their deploy broke or their cloud bill grew. Starts from the simplest hosting the requirements allow, makes rollback a tested path, keeps secrets out of images, repositories and CI, and estimates monthly cost with retrieved prices. Triggers on how do I deploy, Dockerfile, CI pipeline, secrets management, zero downtime, rollback, cloud costs, hosting. For progressive rollout and feature flags use release-manage instead; for moving a system to new infrastructure use migration-plan.
license: MIT
metadata:
  version: 1.1.0
  suite: ai-skill
---

# Infrastructure and deployment

The failure this corrects: infrastructure that looks finished and breaks at the first real event. A
container that ignores SIGTERM drops requests on every deploy, a readiness check on the shared database
takes every instance out at once, a CI job holds long-lived cloud keys, Terraform state holds secrets in
plain text, and a rollback that everyone assumed works cannot undo the migration that ran with it.

## When to use and when to stay off

Run when the user is choosing hosting, writing a Dockerfile, a pipeline, Kubernetes manifests or
Terraform, setting up environments, secrets, TLS or DNS, planning a deploy or rollback, or investigating a
broken deploy or a cloud bill.

Stay off for application code questions with no deployment consequence, and for a local development
setup the user has said will never be deployed.

Routing. Progressive rollout, canaries, feature flags and release notes go to `release-manage`. Moving a
running system to new infrastructure or a new provider goes to `migration-plan`. Metrics, logs, traces
and alerts go to `observability-setup`. Threat modelling, IAM policy review and secret rotation policy go
to `security-hardening`. Schema migration order and backups go to `data-layer`.

The user says "stop", "I've decided", or "just execute": comply at once and stay off for the rest of the
session unless asked again.

## Non-negotiables

These override everything else in this file.

1. Rollback is a tested path. Perform one on purpose before relying on it, and state what it does not undo: migrations already applied and data already written.
2. No secret in an image, a build argument, a repository, a build log, Terraform code or a client bundle. CI authenticates to the cloud through OIDC federation, not long-lived keys.
3. Retrieve prices before estimating cost, and cite the page and date with the assumed usage.
4. Start with the simplest hosting that meets stated requirements.
5. Every environment is created from code, and Terraform state is remote, locked, encrypted and access controlled.
6. A deploy must be safe while both versions run at once.
7. Never point a new deploy at production data without a verified backup taken first.

## Procedure

### Step 1, pick the hosting tier from the requirements

Managed platform hosting (a service that takes a repository and runs it) has the lowest operational cost
and suits most applications for a long time. Limits appear around long running processes, unusual
runtimes and per unit cost at scale.

A single virtual machine with docker compose and a reverse proxy such as nginx or Caddy is cheap and
understandable, and costs you patching and a plan for when the machine dies.

Managed container hosting (ECS on Fargate, Cloud Run, Fly.io) runs containers without you running a
scheduler.

Kubernetes, with Helm or plain manifests, is justified by real multi service orchestration, autoscaling
needs, or an existing platform team. It costs continuous attention.

Serverless functions (Lambda, Cloud Functions) suit spiky, short, stateless work. Check cold starts,
execution time limits and database connection pressure.

State the choice, the requirement that drove it, and the monthly estimate with its source.

### Step 2, build the image properly

Multi stage, so compilers and development dependencies do not ship. Base image pinned by digest. Non root
user. Dependency manifest copied and installed before source, so the layer cache works. A `.dockerignore`
that excludes `.git`, local environment files, caches and build output.

Build time secrets (a private registry token, for example) go through a BuildKit secret mount,
`RUN --mount=type=secret,...`, which never lands in a layer. A build argument is recorded in the image
history.

Signals. The platform stops a container with SIGTERM, and PID 1 has to handle it. Shell form
(`CMD npm start`) runs under `/bin/sh -c`, which does not forward the signal, so the process is killed
after the grace period mid request. Use exec form (`CMD ["node", "server.js"]`) and add an init such as
`tini` if the process spawns children.

Health checks. A Dockerfile `HEALTHCHECK` is used by Docker and docker compose. Kubernetes ignores it and
uses the probes in the pod spec. ECS uses the health check in the task definition and the load balancer's
target group check. Cloud Run uses its own startup and liveness probes. Configure the one your platform
reads.

Verify: build it, run it, send it SIGTERM, call it, and report the image size. A template is in
`references/deploy-checklist.md`.

### Step 3, environments, accounts and configuration

Local, one shared pre-production, and production is usually enough. Give each deployed environment its own
cloud account, project or subscription, so a mistake or a leaked credential in staging cannot reach
production. Turn on MFA for the root or owner account, remove its access keys, and use it for nothing
day to day.

Everything that differs between environments is configuration injected at runtime. Pre-production runs
the same runtime versions and managed services as production.

Never copy production data to a lower environment without masking.

Keep a checked in example configuration listing every variable with a description and a safe default.

Terraform state contains every attribute of every resource, including generated passwords and keys, in
plain text. Store it in a remote backend with locking, encryption at rest, and access limited to the
pipeline and a few operators. Never commit it.

### Step 4, the pipeline

On every push: install, lint, type check, test, build. Fail on any of them.

On the default branch: build the image once, tag it with the commit, and promote that exact artefact.

Pin third party actions by full commit SHA and images by digest, and run Renovate or Dependabot so the
pins get updated instead of rotting.

Authenticate to the cloud with OIDC federation (GitHub Actions to AWS, GCP or Azure), scoped to the
repository and branch, so there is no long-lived key to leak. Declare a `permissions:` block giving the
token the least it needs, such as `contents: read`, and `id-token: write` only on the job that deploys.

Do not use `pull_request_target` to build or run code from a pull request. It runs with the base
repository's secrets and a write token, so checking out the fork's code there hands both to the author.

Keep the pipeline fast, and make it the only path to production.

### Step 5, deploy mechanics

Rolling or blue green, so something is always serving.

Probes. Liveness answers "is this process stuck" and must never check a database or another service,
because a dependency outage then restarts every instance in a loop. Readiness answers "should this
instance get traffic". If readiness fails on a dependency every instance shares, all instances leave the
load balancer together and a partial outage becomes a total one. Check local readiness and return errors
for the failing feature instead. Startup probes cover slow boots. The table is in
`references/deploy-checklist.md`.

Graceful shutdown: on SIGTERM, stop accepting work, finish in flight requests, close connections, then
exit. Traffic keeps arriving briefly after SIGTERM while the load balancer catches up, so add a short
`preStop` sleep in Kubernetes, or rely on the load balancer's deregistration delay on ECS, and keep the
grace period longer than both together.

Resources. Set CPU and memory requests from measured usage and a memory limit, so the scheduler places
pods honestly and a leak kills one container instead of the node. Make the runtime aware of the limit
(heap size flags for the JVM or Node). Treat CPU limits with care, since they throttle under load.

Migrations run separately from the deploy, in the order in `data-layer`. Rolling back the code does not
roll back the schema or the rows written in a new format, so every migration in a release must work with
the previous code version.

Feature flags for risky changes: see `release-manage`.

Practise the rollback. Time it. Write the number down.

### Step 6, TLS, DNS and domains

Issue and renew certificates automatically (ACME with Let's Encrypt, or the provider's managed
certificates). Alert on expiry anyway, because renewal fails quietly when DNS or an HTTP challenge path
changes. Retrieve the issuer's current certificate lifetime, since it is being shortened.

Keep DNS records in code with the rest of the infrastructure. Turn on auto-renew and a transfer lock for
the domain at the registrar, and keep the registrar account under MFA.

### Step 7, cost

Estimate compute, storage, egress, managed services, logging and backups before recommending. Retrieve
current prices for the items that surprise people: NAT gateway hourly and per GB processing charges,
cross availability zone data transfer, internet egress, log ingestion and retention, and idle load
balancers. The line items are in `references/deploy-checklist.md`.

Set a budget alert on day one. Name the item that grows fastest with usage. Check the idle cost of
non-production environments.

## Self-audit

- Hosting choice tied to a stated requirement, with a cost estimate, source and date.
- Image built, run, stopped with SIGTERM, and its size reported.
- Exec form entrypoint; `.dockerignore` present; non root user.
- No secret in image, build args, repository, logs, bundle or state file; BuildKit secret mounts for build time secrets.
- Health check configured for the platform that reads it.
- Liveness checks nothing external; readiness does not fail on a shared dependency.
- Actions pinned by commit SHA, images by digest, with automated updates.
- CI uses OIDC and a least privilege `permissions:` block; no `pull_request_target` running PR code.
- Terraform state remote, locked, encrypted and access controlled.
- Separate account or project per environment; root MFA on.
- Resource requests and memory limits set from measurements.
- Rollback performed once, timed, with what it cannot undo written down.
- Certificates renew automatically and expiry is alerted.
- Budget alert configured; NAT, cross-zone and egress prices retrieved.

## What this cannot do

It cannot give current prices, quotas or certificate lifetimes from memory. It will name where to retrieve
them.

It cannot verify your cloud account's actual configuration without output you share, such as the
Terraform plan, IAM policies or the running pod spec.

It does not certify compliance with frameworks such as SOC 2, ISO 27001, HIPAA or PCI DSS. Ask a
qualified auditor for that framework: "Given this architecture, account layout and pipeline, which
controls are in scope and which evidence will you need from the deployment process?"
