---
title: "FJORD Specification"
description: "FreeBSD Jail Orchestration Runtime Descriptor — A vendor-neutral standard for packaging, distributing, and orchestrating OCI container applications on FreeBSD."
---

# FJORD Specification (v1.0.0-Draft)

**FreeBSD Jail Orchestration Runtime Descriptor**<br>
**Status**: Draft — a proposal. The [implementation status](#implementation-status) table says what exists today.<br>
**Scope**: Standardized Metadata and Orchestration for OCI Containers on FreeBSD<br>
**Author**: Michael Johnson (`michaeljohnson@ahze.net`)

---

## 1. Overview

The FJORD specification defines an open, vendor-neutral standard for packaging, distributing, and installing OCI container applications on FreeBSD. The objective is to deliver a frictionless, "one-click" app store experience while preserving 100% upstream compatibility with standard OCI images and the Compose specification.

Standard container tooling is inherently Linux-centric. FJORD extends standard Compose files with native FreeBSD host hints and isolation capabilities—including **Jails**, **ZFS datasets**, **VNET networking**, and **devfs hardware rulesets**—without breaking upstream compatibility.

### 1.1 Problem Statement: Horizontal Standard vs. Vertical Appliance

Installing self-hosted OCI applications on FreeBSD historically required manual, host-level provisioning:
- Creating tuned ZFS datasets (recordsize, compression).
- Configuring devfs hardware passthrough rules (e.g. `/dev/drm/*` for GPU acceleration).
- Setting up VNET network bridges and Packet Filter (PF) redirection anchors.
- Assigning specific kernel jail parameters (e.g. `allow.mlock`, `allow.sysvipc`).

None of these host requirements can be expressed in a standard upstream `compose.yaml`.

In the Linux ecosystem, platforms such as CasaOS, TrueNAS SCALE, and Umbrel solved this UX friction by constructing **vertical silos**: they deliver a smooth "one-click" experience, but only by locking the administrator into a proprietary operating system distribution, a captive UI, and an opinionated orchestrator.

FreeBSD already possesses superior kernel primitives for container isolation and storage. **FreeBSD does not need a proprietary vertical appliance; it needs an open horizontal standard.**

FJORD defines a vendor-neutral schema for host-level hints and UI orchestration. By decoupling the application definition from the execution client, FJORD enables any compliant tool—whether a web UI like `fjordd`, a management platform like Sylve, or a headless CLI—to deliver automated container management on native FreeBSD.

### 1.2 Goals

- **Vendor-Neutrality**: Establish an open, horizontal specification that any UI, CLI, or orchestration tool can adopt.
- **Frictionless UX**: Enable a streamlined app-store experience without requiring a dedicated appliance OS.
- **Upstream Compatibility**: Build upon standard OCI formats and the Compose specification. Maintainers append extension metadata; they do not rewrite deployment logic.
- **Native Primitive Integration**: Expose FreeBSD Jails, ZFS, VNET, and devfs declaratively within the app manifest.
- **Declarative Host Provisioning**: Shift host provisioning (ZFS dataset creation, UID/GID permission mapping, devfs rules) into an automated pre-flight phase, eliminating fragile in-container init scripts.

### 1.3 Non-Goals

- **Mandating an Execution Client**: FJORD is strictly a metadata and orchestration specification. It does not dictate the implementation language or user interface of tools implementing the spec.
- **Creating a New Container Runtime**: The standard relies entirely on existing OCI runtimes (`ocijail`, `runj`) and container engines (`podman`, `appjail`).
- **Replacing Custom Jail Managers**: FJORD targets containerized application workloads. It does not replace raw jail managers (such as Bastille or standard AppJail) for users constructing manual FreeBSD environments from source.
- **Defining Container Internal Architecture**: FJORD dictates how an application interfaces with the host system, not how internal services or databases are structured.

### 1.4 Security &amp; Threat Mitigation

FJORD mitigates host execution risks by remaining **strictly declarative**. The specification explicitly forbids arbitrary shell commands, scripts, or execution hooks inside the application manifest. Execution clients interact with the host exclusively through strongly-typed variables and execute internal, heavily sanitized routines for dataset provisioning and permissions.

### 1.5 System Assumptions

A compliant FJORD host environment provides:

- **FreeBSD 15+**: Required for modern jail parameters and OCI jail runtimes.
- **ZFS**: Required for declarative dataset provisioning and property tuning.
- **OCI-Compliant Runtime**: An engine capable of pulling OCI images and applying FreeBSD jail annotations (e.g. Podman with `ocijail`, or AppJail).
- **VNET Support**: Kernel VNET support (`if_epair` module loaded) for network-isolated workloads.
- **Privilege Escalation**: Administrative access (`doas` or `sudo`) for pre-flight dataset creation and devfs rule application.

---

## Implementation status

What fjord and the daemonless catalog implement today versus what this draft proposes. Proposed items are open for discussion and contribution; nothing depends on them yet.

| Area | Implemented today | Proposed |
| :--- | :--- | :--- |
| `x-fjord.info` | `name`, `description`, `category`, `class` (`service`, `stack`), `icon`, `version`, `architectures`, `web_url` / `web_port` for the Open link | `requires`, `health_url`, classes `cli` / `agent` / `gui` |
| `x-fjord.variables` | types `port`, `string`, `secret`, `path`, `zfs_dataset` (a folder under App data + `host_permissions`), `optional`, `label` | `network_interface`, real ZFS datasets with `zfs_properties` |
| `x-fjord.host` | — | `vnet_required`, `vnet_bridge`, `devfs_rules`, `min_freebsd_version` |
| Jail annotations | `org.freebsd.jail.*` in `annotations:` (podman via ocijail; AppJail via the bundle's jail template) | — |
| Catalog | `catalog.json` + `manifests/<app>.yaml` + `icons/`, multiple catalogs merged in one store | `catalog_version`, `maintainer`, `generated`, `updated` |
| Install | manifest → App data folders → pre-flight (ports, folders) → `.env` → engine | `min_freebsd_version` and VNET checks, `zfs create`, devfs rules |
| Teardown | stop + remove from fjord; bind data always kept | preserve / purge prompt |
| Update | pull for the channel, recreate; `.env` kept | delta wizard for new variables |

---

## 2. Application Manifest (`compose.yaml`)

FJORD uses the standard Compose Specification as its foundation. All application definitions MUST be valid Compose files.

FreeBSD-specific metadata, UI wizard definitions, and host requirements reside entirely within a reserved root extension block: **`x-fjord`**.

```yaml
services:
  plex:
    image: ghcr.io/daemonless/plex:latest
    ports:
      - "${WEB_PORT}:32400"
    volumes:
      - ${CONFIG_DATA}:/config
      - ${MEDIA_PATH}:/media:ro
    environment:
      - PLEX_CLAIM=${PLEX_TOKEN}
    annotations:
      org.freebsd.jail.param.allow.raw_sockets: "1"
    restart: unless-stopped

x-fjord:
  version: "1.0"
  info:
    name: "Plex Media Server"
    description: "Stream personal media collections via native FreeBSD Jails."
    category: "Media"
    class: "service"
    icon: "https://daemonless.io/icons/plex.png"

  host:
    vnet_required: true
    vnet_bridge: "${NETWORK_IFACE}"
    min_freebsd_version: "15.0"
    devfs_rules:
      - "add path 'drm/*' unhide"

  variables:
    - name: NETWORK_IFACE
      label: "Network Bridge Interface"
      type: network_interface
      default: "bridge0"

    - name: WEB_PORT
      label: "External Web Port"
      type: port
      default: "32400"

    - name: CONFIG_DATA
      label: "Configuration Storage Dataset"
      type: zfs_dataset
      default: "config"
      zfs_properties:
        recordsize: "16K"
        compression: "lz4"
      host_permissions:
        uid: 972
        gid: 972
        mode: "755"

    - name: MEDIA_PATH
      label: "Media Library Path"
      type: path
      default: ""

    - name: PLEX_TOKEN
      label: "Plex Claim Token"
      type: secret
```

---

### 2.1 The `x-fjord` Extension Block

#### `info` (Application Metadata)

| Field | Required | Description |
| :--- | :--- | :--- |
| `name` | Yes | Human-readable application title. |
| `description` | Yes | Summary of the application's functionality. |
| `category` | Yes | Categorization group (e.g. `Media`, `Storage`, `Network`). |
| `class` | Yes | Application execution class (`service`, `cli`, `agent`, `gui`). |
| `icon` | Yes | URL to a 1:1 aspect ratio PNG, WebP, or SVG icon. |
| `version` | No | Application release version string. |
| `architectures` | No | List of architectures the image is built for (e.g. `["amd64"]`). |
| `requires` | No | Array of application dependencies (`id`, `optional`, `reason`). |
| `health_url` | No | Relative HTTP path used to probe status and link the "Open" button. |

#### Application Classes (`class`)

- **`service`**: Runs persistently and exposes a web interface or network service. The UI displays live status and an **Open** button linking to `health_url`.
- **`cli`**: A run-once command-line utility. The UI displays an execution snippet rather than a persistent service card.
- **`agent`**: A background daemon without a user-facing HTTP endpoint. The UI shows running/stopped state without an Open link.
- **`gui`**: Reserved for desktop/graphical applications.

#### Icon Specifications &amp; Caching Contract

To guarantee uniform UI rendering:
1. **Aspect Ratio**: Must be exactly 1:1 (square).
2. **Dimensions**: Minimum 256x256 px, maximum 512x512 px for raster formats (PNG, WebP). Vector SVGs must include a 1:1 `viewBox`.
3. **File Size**: Target < 50 KB (maximum 250 KB).
4. **No Baked Shadows**: Icons must omit drop shadows or glows; UIs render theme-aware shadows dynamically.
5. **Catalog Mirroring**: Catalog builders should fetch and mirror upstream icons to local static storage during index generation to prevent external link rot.

---

### 2.2 `host` (Host Prerequisites &amp; Hints)

Declarative instructions for preparing the FreeBSD host environment before container execution:

| Field | Type | Description |
| :--- | :--- | :--- |
| `vnet_required` | boolean | If true, the container must be isolated in a dedicated VNET jail with its own network stack. |
| `vnet_bridge` | string | Variable reference (e.g. `"${NETWORK_IFACE}"`) resolving to the host network bridge interface (defaults to `bridge0`). |
| `devfs_rules` | list | List of devfs rules required for hardware passthrough (e.g. GPU `/dev/drm/*` or DVB tuner devices). |
| `min_freebsd_version` | string | Minimum required FreeBSD base version (e.g. `"15.0"`). |

---

### 2.3 `variables` (UI Prompts &amp; Injection)

FJORD uses standard Compose variable interpolation (`${VARIABLE_NAME}`) to inject user configuration. Variables declared in `x-fjord.variables` map directly to UI input widgets. The client writes collected values to a local `.env` file without mutating `compose.yaml`.

#### Prompt Types

| Type | UI Representation | Behavior |
| :--- | :--- | :--- |
| `path` | Host Path Picker | Selects an existing host directory. If `default` is empty, the client prompts for an absolute path ("Bring Your Own Data"). |
| `zfs_dataset` | Dataset Selector | Selects or provisions a dedicated ZFS dataset. If `default` is relative, it resolves under the app's base storage path. |
| `port` | Numeric Port Input | Validates against host port collisions during pre-flight. |
| `network_interface`| Interface Dropdown | Discovers and selects available host network interfaces and bridges. |
| `secret` | Masked Input | Masked text field stored securely in `.env`. |
| `string` | Plain Input | General configuration text. |

#### Storage &amp; Dataset Tuning (`zfs_properties` &amp; `host_permissions`)

When `type: zfs_dataset` is declared, the manifest can define native ZFS dataset properties and filesystem ownership:

```yaml
zfs_properties:
  recordsize: "16K"       # Tuned for database workloads
  compression: "lz4"
host_permissions:
  uid: 972                # Numeric UID for in-container user
  gid: 972                # Numeric GID
  mode: "755"             # Octal permissions mode
```

---

### 2.4 FreeBSD Jail Annotations

Privileges required by containerized workloads are declared natively within the service's `annotations:` block:

| Annotation | Description | Common Use Case |
| :--- | :--- | :--- |
| `org.freebsd.jail.allow.mlock` | Permits physical page memory locking. | .NET runtimes (Sonarr, Radarr, Jellyfin). |
| `org.freebsd.jail.allow.sysvipc` | Enables System V IPC primitives. | PostgreSQL shared memory segment allocation. |
| `org.freebsd.jail.param.allow.raw_sockets` | Grants raw socket access. | Ping, traceroute, and network diagnostic tools. |

---

## 3. Catalog Distribution Schema (`catalog.json`)

fjord App Stores load catalog indices as static JSON files published via standard HTTP/HTTPS endpoints.

```json
{
  "catalog_name": "Daemonless Official Apps",
  "catalog_version": "1.0.0",
  "maintainer": "https://daemonless.io",
  "generated": "2026-06-11T00:00:00Z",
  "apps": [
    {
      "id": "plex",
      "name": "Plex Media Server",
      "description": "Stream personal media collections.",
      "category": "Media",
      "icon": "https://daemonless.io/icons/plex.png",
      "class": "service",
      "health_url": "/web",
      "manifest_url": "manifests/plex.yaml",
      "image": "ghcr.io/daemonless/plex:latest",
      "version": "1.40.2",
      "updated": "2026-06-11T00:00:00Z",
      "architectures": ["amd64"],
      "variants": [
        {
          "id": "latest",
          "label": "Latest Release",
          "default": true,
          "image": "ghcr.io/daemonless/plex:latest",
          "version": "1.40.2"
        }
      ]
    }
  ]
}
```

---

## 4. Execution, UI, &amp; Lifecycle Contract

Execution clients (UIs, CLI tools, or background daemons) implement the following lifecycle stages:

### 4.1 Deployment (Install) Contract

1. **Catalog Resolution**: Download `catalog.json` and retrieve the requested application's `compose.yaml`.
2. **Base Storage Resolution**: Determine the application's base dataset path (e.g. `/tank/apps/<app_id>`).
   - Relative `zfs_dataset` paths resolve automatically against the base storage path.
   - Empty `path` prompts require an absolute host path from the user ("Bring Your Own Data").
3. **Pre-flight Host Preparation**:
   - Verify `min_freebsd_version`.
   - Validate port availability via non-blocking socket test.
   - If `vnet_required` is true, verify the target network bridge (`vnet_bridge` or `bridge0`).
   - If `zfs_dataset` is specified, execute `zfs create` and apply declared `zfs_properties`.
   - Apply `host_permissions` via sanitized `chown` and `chmod`.
   - Apply any declared `devfs_rules`.
4. **Environment Generation**: Write collected user variables to `.env` in the stack directory.
5. **Execution**: Pass the final configuration to the designated OCI orchestrator (`podman-compose` or `appjail-director`).

### 4.2 Teardown (Uninstall) Contract

1. **Stop Workload**: Signal the container engine to terminate running jail instances and tear down virtual networks.
2. **Preserve Data Prompt**: Prompt the user whether to preserve or destroy associated ZFS datasets. The default action is to preserve user datasets.
3. **Cleanup**: Remove instance-specific devfs rules and release network interfaces.

### 4.3 Update Contract

1. **State Diffing**: Compare the updated manifest's `x-fjord.variables` block against the existing `.env` configuration.
2. **Delta Wizard**: If the upstream maintainer introduced new variables, present a targeted prompt capturing the missing parameters before triggering deployment.
3. **Reconciliation**: Pull the updated OCI image and command the engine to recreate container workloads against the updated state.
