---
title: "Architecture & Core Concepts"
description: "How fjord models FreeBSD container orchestration: stacks on disk, engine-agnostic abstraction (Podman and AppJail), catalog manifests, storage boundaries, and pre-flight diagnostics."
---

# Architecture &amp; Core Concepts

fjord is designed around a single architectural philosophy: **the filesystem is the source of truth**. Rather than encapsulating container definitions in an internal database or proprietary configuration format, fjord manages native FreeBSD jails by reading and writing standard compose specifications and environment files directly on disk.

```
/var/db/fjord/stacks/<stack-id>/
├── compose.yaml            # Podman engine specification
├── appjail-director.yml    # AppJail director orchestration spec
├── Makejail                # AppJail build recipe
├── .env                    # User configuration & environment variables
└── state.json              # Stack metadata (engine binding, status, channel)
```

Because fjord maintains zero private state locks, administrators can inspect, version, or modify stack files directly with standard shell tools (`vi`, `git`, etc.). Running `podman-compose` or `appjail-director` inside a stack directory yields the exact same behavior as triggering actions through fjord's web interface.

---

## 1. Stacks

A **stack** represents a cohesive application deployment. A stack may encompass a single service (such as Radarr or Caddy) or an interconnected multi-container architecture (such as Immich with its PostgreSQL and Redis sidecars).

When a stack is deployed:

1. **Workspace Allocation**: fjord creates an isolated directory in `/var/db/fjord/stacks/<id>`.
2. **Template Synthesis**: The chosen catalog manifest generates the engine specification files (`compose.yaml` or `appjail-director.yml`).
3. **Environment Generation**: Configured variables, port bindings, and storage mounts are written to `.env`.
4. **Pre-flight**: The daemon creates missing data folders (owned by the app's PUID/PGID) and verifies host port availability.
5. **Engine Invocation**: The target orchestrator launches the container workload natively on the FreeBSD kernel.

---

## 2. Container Engines

fjord is architecturally engine-agnostic, decoupling compose specifications from the underlying execution runtime. It currently supports two container backends on FreeBSD, allowing administrators to choose the runtime best suited for each workload:

| Characteristic | Podman Engine | AppJail Engine |
| :--- | :--- | :--- |
| **Specification Format** | `compose.yaml` | `appjail-director.yml` + `Makejail` |
| **CLI Orchestrator** | `podman-compose` | `appjail-director` |
| **OCI Runtime** | `ocijail` | Native `jail(8)` via AppJail OCI |
| **Networking Model** | CNI bridge (`cni-rdr`), host, LAN address via `cni-epair` (DHCP or pool) — see [Networking](networking.md) | Virtual bridge (`appjail-nat`), host network |
| **Remote Volumes** | Native NFS and SMB named volumes | Host-mounted paths |
| **Jail Annotation Mapping** | `annotations:` in `compose.yaml` | Jail parameters in director spec |

### Engine Coexistence
Configured engines can run concurrently on a single FreeBSD host. Engine selection is configured on a per-stack basis during initial deployment and preserved in `state.json`.

### Jail Parameter Translation
FreeBSD container images often require specific kernel jail parameters (for example, .NET applications like Sonarr/Radarr require `allow.mlock=true`, while database servers may require `allow.sysvipc=true`). In the Podman engine, these requirements are declared as OCI annotations (`org.freebsd.jail.*`) in `compose.yaml` and translated by `ocijail`. In the AppJail engine they ride in the jail template of the dbuild-generated bundle that fjord materializes for director.

---

## 3. Catalogs &amp; Manifests

The fjord App Store consumes static, decoupled **catalogs**. A catalog is simply an HTTP-accessible endpoint publishing three components:

1. `catalog.json`: Fleet-wide metadata, categories, architectures, and available app entries.
2. `manifests/<app>.yaml`: Per-application deployment schemas, required vs. optional ports, environment parameters, and default values.
3. `icons/`: SVG and PNG brand icons for user interface display.

### Default Catalog &amp; Custom Sources
fjord ships with [catalog.daemonless.io](https://catalog.daemonless.io) enabled by default, which is continuously generated from FreeBSD-native images in the Daemonless fleet. Administrators can configure private or secondary catalog URLs in **Settings**; fjord merges all active catalogs into a unified store, tagging each application with its origin repository.

### Release Channels
Catalog manifests define release channels corresponding to image tag families:

- `latest`: Tracks official upstream application releases (default for most workloads).
- `pkg`: Tracks stable FreeBSD Quarterly binary packages.
- `pkg-latest`: Tracks bleeding-edge FreeBSD Latest binary packages.

### CPU Architecture Filtering
Manifests specify supported host architectures (`amd64`, `arm64`). fjord knows the architecture it was built for (amd64 or arm64) and filters incompatible applications from view, whichever way round the mismatch is, preventing runtime architecture errors.

---

## 4. Storage Architecture

fjord enforces a strict architectural boundary between internal application state and external user data pools:

```
Storage Layout
├── App Data Root (/var/db/fjord/containers/ or ZFS dataset)
│   ├── radarr/
│   │   └── config/      <-- Application config, SQLite databases, logs
│   └── immich/
│       ├── postgres/    <-- Relational database files
│       └── machine-learning/
└── User Data Pools (ZFS pools / NFS / SMB)
    ├── /tank/media/movies/     <-- Persistent media library
    ├── /tank/media/tv/
    └── /tank/downloads/
```

### App Data
App Data encompasses the internal operational state of containers: configurations, databases, caches, and socket locks. Administrators configure one or more App Data roots in **Settings** (typically pointing to dedicated ZFS datasets such as `zroot/data/fjord`). fjord provisions application subdirectories automatically upon deployment.

### Folder Sets
Folder Sets represent your actual user data assets (media libraries, photo collections, document repositories, backups). Rather than re-entering absolute paths or connection URIs for every stack, administrators declare reusable **Folder Sets** once in **Settings**. When launching or editing a stack, choosing a folder set automatically maps the corresponding paths into the container specification.

Folder Sets support:
- Local filesystem paths and ZFS datasets.
- NFS endpoints (`nfs://server/export`).
- SMB shares (`smb://user@server/share`, supported on Linux hosts; on FreeBSD, NFS or local mount points are recommended due to SMB kernel protocol compatibility).

---

## 5. Pre-flight and Readiness Checks

Two layers keep a stack from failing for host reasons:

**Pre-flight** runs before every start and install:

1. **Port collisions**: every published port — and, for `network_mode: host` services, every port the image exposes — is probed. A port held by another container is reported by that container's name; a port held by a host process is reported as in use.
2. **Data folders**: missing bind-mount sources are created and chowned to the stack's `PUID`/`PGID`, so a sidecar never crashes on a root-owned cache directory.

If pre-flight fails, the stack configuration is saved to disk without launching, so you can change a port or free it and start again.

**Readiness checks** run on the System page (and in the first-run wizard) and cover the host itself: the libpod socket, `conmon`/`ocijail` and their versions, pf anchors (`cni-rdr/*` for podman, `appjail-nat/*` for AppJail), the AppJail toolchain and the fjord data root — each with *why* it matters and a copy-paste fix.

---

## 6. Lifecycle

What fjord does today at each stage. The [FJORD Specification](spec.md) describes the fuller contract this is growing toward; its status table says which parts exist.

- **Install**: resolves the catalog manifest, computes the App data folders under `<App data>/<stack>/…`, runs pre-flight, provisions and chowns the folders, writes `.env` and the engine spec, then hands the stack to the engine.
- **Delete**: stops the stack and removes it from fjord. Bind-mounted data always stays on disk; there is no purge option yet.
- **Update**: pulls the newest image for the stack's release channel and recreates the containers or jails. Values already in `.env` are kept; a manifest that gained new variables is not diffed yet (see the roadmap).
