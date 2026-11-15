---
title: "Operating Guide"
description: "Administrator guide for operating fjord: deploying applications, typed wizard settings, stack lifecycles, names and HTTPS, health recovery policies, storage pools, and host checks."
---

# Operating Guide

`fjord` organizes container infrastructure operations across **App Store**, **Stacks**, **Networks**, **Volumes**, **System**, and **Settings**, alongside the built-in [`fjord` CLI](cli.md).

---

## 1. Deploying Stacks via the App Store

![The fjord App Store](img/store-dark.png#only-dark){ .glightbox }
![The fjord App Store](img/store-light.png#only-light){ .glightbox }

The **App Store** catalogs all container applications and multi-service stacks available across your configured catalogs, with **Cards** and **List** views and component-aware search (searching for a stack part surfaces its parent stack).

### OS &amp; Architecture Filtering
Applications incompatible with your host OS (FreeBSD vs. Linux) or CPU architecture (`amd64` vs. `arm64`) are automatically filtered from the primary view. A counter shows how many entries are hidden for your architecture, with a toggle to inspect them.

### The Deployment Wizard
Selecting an application opens a three-level install wizard (**Required**, **Options**, and **Advanced**):

- **Typed Settings &amp; Secrets**: Prompts render as switches (`bool`), bounded numbers (`int`), option pickers (`choice`), storage sizes (`size`), or generated secrets (created automatically at install unless you enter your own).
- **Install Choices**: Multi-database or modular stacks offer clean pickers (for example `SQLite`, `PostgreSQL`, or `External`) that adjust services, variables, and AppJail templates automatically.
- **Storage &amp; Folder Sets**: Map persistent libraries with one click via **Add folder set...** (`Media`, `Downloads`, `Photos`), or browse host paths directly. Apps that store no host state say so explicitly.
- **Per-Service Networking &amp; Names**: Multi-service stacks place the web frontend on your default or LAN network and keep databases/caches on an isolated private network. When paired with a [names provider](networking.md#names-and-local-https), you can assign a local HTTPS name (`radarr.apps.lan`) right in the wizard.
- **Release Channel &amp; Engine**: Pick `latest`, `pkg`, or `pkg-latest`, and choose `podman` or `appjail` (on FreeBSD).
- **Capability Review**: Before installing, the wizard highlights any elevated host capabilities requested by a catalog manifest (`privileged`, `cap_add`, `devices`, host namespaces, jail annotations, or bind mounts outside App Data and Folder Sets).

Before starting anything, `fjordd` runs **pre-flight checks**: if a default port is already held, the wizard starts on a free port and names what holds the default.

---

### Adopting Existing Containers &amp; Jails
**Adopt** on the Stacks overview (and during initial Setup) lists unmanaged Podman containers, external `podman-compose` projects, and AppJail jails running on the host. `fjord` reconstructs a standard `compose.yaml` (or AppJail director bundle) from the live runtime configuration and replaces it in place, keeping its image, mounts, network address, MAC, and name without moving data.

---

## 2. Stack Lifecycle, Health &amp; Names

![The stacks overview: every stack, its state, its update and where it answers](img/stacks-dark.png#only-dark){ .glightbox }
![The stacks overview: every stack, its state, its update and where it answers](img/stacks-light.png#only-light){ .glightbox }

![A stack page, Services tab](img/stack-dark.png#only-dark){ .glightbox }
![A stack page, Services tab](img/stack-light.png#only-light){ .glightbox }

The **Stacks** page supports both **Cards** and **List** views, displaying each stack's engine, health status, address or HTTPS name, and available updates (including **Update all** when updates are pending).

### Lifecycle &amp; Access Actions
- **Open (`▾` menu)**: Opens the web interface by its HTTPS name or direct IP:port, and lets you assign, change, or remove a stack's name on your [names provider](networking.md#names-and-local-https). If the app defines initial or generated credentials, **Sign in** beside **Open** displays them.
- **Start / Stop / Restart**: Runs inside `fjordd` and verifies the resulting container or jail state.
- **Update / Roll back / Change Version...**: Reviews SBOM package diffs, watches updated containers stay healthy, pins digests, or rolls back to the previous image. See [Updates](updates.md).
- **Delete**: Stops and removes the stack while keeping App Data on disk by default, with an explicit option to remove App Data after confirming the stack is down.

### Background Health Watch &amp; Recovery Policy
`fjordd` continuously monitors every running stack in the background (even with no browser open), checking restart counts, non-zero exit codes, container healthchecks, and empty AppJail jails (clean one-shot init containers are ignored). Under each stack's **Settings** tab you can configure:

- **Restart policy**: Boot and crash behavior (`always`, `unless-stopped`, `on-failure`, `no`).
- **Recovery policy**: What `fjordd` does when a service enters a failure loop (**do nothing**, **restart**, or **stop**), bounded by a maximum attempt count and cooldown window.

### Interactive Diagnostics Drawer
The bottom drawer on every stack page provides three live views:

1. **Output**: Durable record of engine runs (`podman-compose`, `appjail-director`), post-update health watches, and name registrations.
2. **Logs**: Real-time ANSI-color log streaming from the Libpod socket or jail log.
3. **Shell**: Interactive WebSocket terminal inside the running container or jail (closing the tab cleanly terminates background shell children).

---

## 3. Direct Specification Editing

`fjord` treats the files on disk in `/var/db/fjord/stacks/<stack>/` as the ground truth:

- **compose.yaml / Makejail**: Built-in CodeMirror editor with YAML anchor and merge-key awareness. Switching away with unsaved edits prompts before discarding.
- **.env &amp; Resources**: Structured editors for variables, ports, and mounts (including SELinux `:z` and mount options on Linux).

Clicking **Save** writes to disk without disrupting running containers; clicking **Apply** recreates only the services affected by your edits and runs a stay-up health check.

---

## 4. Volumes &amp; Storage

The **Volumes** page manages named volumes independently of individual stacks:

- **Local**: Named volumes managed by Podman.
- **Remote**: `nfs://server/export` (FreeBSD and Linux) and `smb://user@server/share` (Linux hosts) mounted as named container volumes.
- **Safety**: Volumes referenced by an installed stack cannot be deleted accidentally.

---

## 5. Host Conditions &amp; System Diagnostics

![Setup: what fjord does itself, and the commands it leaves to you](img/setup-dark.png#only-dark){ .glightbox }
![Setup: what fjord does itself, and the commands it leaves to you](img/setup-light.png#only-light){ .glightbox }

- **Conditions Banner**: Background host and engine checks run on a timer and whenever runtime state changes. Any problem (a stopped Podman socket, missing PF anchor, outdated `cni-epair` plugin, or unreachable names provider) appears in a top banner across every page and is re-verified automatically before clearing.
- **Setup &amp; System**: **Set up** configures plugins (`cni-epair` v1.2.1+, `cni-dnsname`), PF anchors, NAT rules, and `dnsmasq` bridge resolution on FreeBSD, or verifies `podman.socket`, `firewalld`/`ufw`, and SELinux on Linux. **Cleanup** prunes unused container layers, build caches, and orphaned resources safely.

---

## 6. Settings

- **Storage**: Configure default **App Data** roots (ZFS datasets or host directories) and reusable **Folder Sets** (`Media`, `Downloads`, `Photos`, `Backups`).
- **Plugins &amp; Names**: Choose the default engine (`podman` or `appjail`) and pair or link a [names provider](networking.md#names-and-local-https) (such as `daemonless/reverse-proxy`).
- **Catalogs**: Manage HTTPS catalog sources (or local LAN catalogs) and trigger manual refreshes.
- **Account**: View active 30-day browser sessions, sign out remote devices, and update your user name or password.
