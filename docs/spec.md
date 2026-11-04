---
title: "FJORD Specification"
description: "FreeBSD Jail Orchestration Runtime Descriptor — A vendor-neutral standard for packaging, distributing, and orchestrating OCI container applications on FreeBSD and Linux."
---

# FJORD Specification (Draft)

**FreeBSD Jail Orchestration Runtime Descriptor**<br>
**Status**: Draft. Manifests and catalogs on the wire say format version `0.1`; the [implementation status](#implementation-status) table says what fjord 0.4 and the daemonless catalog implement, and what is still a proposal.<br>
**Scope**: Standardized Metadata and Orchestration for OCI Containers on FreeBSD and Linux<br>
**Author**: Michael Johnson (`michaeljohnson@ahze.net`)

---

## 1. Overview

The FJORD specification defines an open, vendor-neutral standard for packaging, distributing, and installing OCI container applications on FreeBSD and Linux. The objective is to deliver a frictionless, "one-click" app store experience while preserving 100% upstream compatibility with standard OCI images and the Compose specification.

Standard container tooling is inherently Linux-centric. FJORD extends standard Compose files with FreeBSD jail parameters, AppJail bundles, per-service stack networking, typed install variables, and install-time choices, with declarative ZFS dataset properties and devfs rulesets proposed in [§2.9](#29-host-proposed), without breaking upstream compatibility.

### 1.1 Problem Statement: Horizontal Standard vs. Vertical Appliance

Installing self-hosted OCI applications on FreeBSD historically required manual, host-level provisioning:
- Creating tuned ZFS datasets (recordsize, compression).
- Configuring devfs hardware passthrough rules (e.g. `/dev/drm/*` for GPU acceleration).
- Setting up VNET network bridges and Packet Filter (PF) redirection anchors.
- Assigning specific kernel jail parameters (e.g. `allow.mlock`, `allow.sysvipc`).

None of these host requirements can be expressed in a standard upstream `compose.yaml`.

In the Linux ecosystem, platforms such as CasaOS, TrueNAS SCALE, and Umbrel solved this UX friction by constructing **vertical silos**: they deliver a smooth "one-click" experience, but only by locking the administrator into a proprietary operating system distribution, a captive UI, and an opinionated orchestrator.

FreeBSD already possesses superior kernel primitives for container isolation and storage. **FreeBSD does not need a proprietary vertical appliance; it needs an open horizontal standard.**

FJORD defines a vendor-neutral schema for host-level hints and UI orchestration. By decoupling the application definition from the execution client, FJORD enables any compliant tool, whether a web UI like `fjordd`, a management platform like Sylve, or a headless CLI, to deliver automated container management on native FreeBSD and Linux.

### 1.2 Goals

- **Vendor-Neutrality**: Establish an open, horizontal specification that any UI, CLI, or orchestration tool can adopt.
- **Frictionless UX**: Enable a streamlined app-store experience without requiring a dedicated appliance OS.
- **Upstream Compatibility**: Build upon standard OCI formats and the Compose specification. Maintainers append extension metadata; they do not rewrite deployment logic.
- **Native Primitive Integration**: Expose FreeBSD Jails, ZFS, VNET, and devfs declaratively within the app manifest.
- **Declarative Host Provisioning**: Shift host provisioning (ZFS dataset creation, UID/GID permission mapping, devfs rules) into an automated pre-flight phase, eliminating fragile in-container init scripts.

### 1.3 Non-Goals

- **Mandating an Execution Client**: FJORD is strictly a metadata and orchestration specification. It does not dictate the implementation language or user interface of tools implementing the spec.
- **Creating a New Container Runtime**: The standard relies entirely on existing OCI runtimes (`ocijail`, `runj`, `crun`, `runc`) and container engines (`podman`, `appjail`).
- **Replacing Custom Jail Managers**: FJORD targets containerized application workloads. It does not replace raw jail managers (such as Bastille or standard AppJail) for users constructing manual FreeBSD environments from source.
- **Defining Container Internal Architecture**: FJORD dictates how an application interfaces with the host system, not how internal services or databases are structured.

### 1.4 Security &amp; Threat Mitigation

`x-fjord` adds no execution hooks of its own: it is declarative metadata and typed variables, and clients create folders and apply permissions through their own routines rather than running scripts from `x-fjord`. A manifest is still a Compose file (and may carry an [AppJail bundle](#210-appjail-the-appjail-bundle)), so it runs what its images, Compose services, and Makejail say — adding a catalog means trusting it.

### 1.5 System Assumptions

A compliant FJORD host environment provides:

- **FreeBSD 15+ or Linux**: FreeBSD 15+ for modern jail parameters and OCI jail runtimes (`ocijail`, `appjail`), or Linux with rootful Podman.
- **ZFS**: Recommended on FreeBSD. Today a `zfs_dataset` variable is a folder under the client's app data location; creating a real dataset with tuned properties is proposed.
- **OCI-Compliant Runtime**: An engine capable of pulling OCI images and, on FreeBSD, applying jail annotations (e.g. Podman with `ocijail`, or AppJail).
- **VNET / Bridge / Macvlan Support**: Kernel VNET support (`if_epair` on FreeBSD) or macvlan/bridge networking (on Linux) for network-isolated workloads.
- **Privilege Escalation**: Administrative access for pre-flight folder creation, network setup, and permission application.

---

## Implementation status

What fjord 0.4 and the daemonless catalog implement today, and what this draft still proposes. Proposed items are open for discussion; nothing published depends on them.

| Area | Implemented | Proposed |
| :--- | :--- | :--- |
| [`info`](#21-info-application-metadata) | `id`, `name`, `description`, `category`, `class` (`service`, `stack`, `part`), `icon`, `version`, `upstream_url`, `web_url`, `web_port` / `web_https` (the Open link), `own_origin`, `name_env`, `only_for_archs` | `requires`, `health_url`, classes `agent` / `gui` |
| [`variables`](#22-variables-install-prompts) | types `port`, `string`, `secret`, `path`, `zfs_dataset`, `image_tag`, `public_url`; `label`, `default`, `optional`, `level`, `generate`, `host_permissions`, `image`; required secrets are generated (64 hex chars, or 20 unambiguous letters and digits for `login.password`) | `network_interface`; real ZFS datasets with `zfs_properties` |
| [`variants`](#23-variants-image-tags) | the image's tags to pick from (`id`, `label`, `default`, `version`, `aliases`); the client asks the registry what each tag is built for | — |
| [`networking`, `hostnames`](#24-networking-and-hostnames-stacks) | per service `default` or `private`, `*` for the rest; the variable each service is found by | — |
| [`choices`](#25-choices-questions-at-install) | a database (`sqlite`, `postgres`, `mariadb`, `external`) or a part, with everything each answer adds, drops, sets and asks for | — |
| [`login`](#26-login-app-sign-in) | `user`, `password` (a literal default or `${VAR}`), and `note`, shown beside Open so the person knows how to sign in | — |
| [`provides.names`](#27-providesnames-names-and-https) | `port`, `key`, `setup_token`, `client_url`, `client_id`, `client_name` on a reverse-proxy stack that gives other apps names and HTTPS | — |
| [`appjail`](#210-appjail-the-appjail-bundle) | the AppJail bundle (`director`, `makejail`, `template_conf`, `env_defaults`, `extras`), run as-is by `appjail-director`; each choice option carries its AppJail form | — |
| [Jail annotations](#28-freebsd-jail-annotations) | `org.freebsd.jail.*` in a service's `annotations:` | — |
| [`host`](#29-host-proposed) | — | `vnet_required`, `vnet_bridge`, `devfs_rules`, `min_freebsd_version` |
| [Catalog](#3-catalog-distribution) | per catalog `catalog.json` (with `os` and stack `parts`), `manifests/<id>.yaml`, `icons/`, plus `sources.json` published by the catalog builder; several catalogs merged in one store by base URL, filtered by what the host OS can run | `catalog_version`, per-app `updated` |
| [Install](#41-install) | manifest → choices → app data folders → generated secrets → pre-flight (ports, folders, the tag's architecture) → networks → `.env` → engine → stay-up check and optional name | `min_freebsd_version` and VNET checks, `zfs create`, devfs rules |
| [Teardown](#42-teardown) | stop and remove; app data kept unless the user asks to delete it; a private network goes with its stack | — |
| [Update](#43-update) | per service or across all behind stacks (**Update all**): the change in words (patch, minor, major, a new build) with the package diff; recreate, a 30 s health watch, roll back; `.env` kept | a prompt for variables a new manifest adds |

---

## 2. Application Manifest

A manifest is a Compose file with one extra top-level block, **`x-fjord`**. Everything outside `x-fjord` is ordinary Compose and MUST stay valid Compose: `podman-compose` runs it with the values from `.env`.

This is radarr's manifest as the daemonless catalog publishes it, shortened:

```yaml title="manifests/radarr.yaml"
name: radarr
services:
  radarr:
    image: ghcr.io/daemonless/radarr:latest # (1)
    restart: unless-stopped
    annotations:
      org.freebsd.jail.allow.mlock: "true" # (2)
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=${TZ}
    volumes:
      - ${CONFIG_DATA}:/config # (3)
      - ${MOVIES_PATH}:/movies
    ports:
      - ${WEB_PORT}:7878

x-fjord:
  version: "0.1" # (4)
  info:
    id: radarr
    name: Radarr
    description: Automated movie collection manager.
    category: Media Management
    class: service
    icon: icons/radarr.svg # (5)
    web_port: ${WEB_PORT} # (6)
    upstream_url: https://github.com/Radarr/Radarr
    web_url: https://radarr.video/
  variables:
    - name: WEB_PORT
      label: Web UI
      type: port
      default: "7878"
    - name: CONFIG_DATA
      label: Configuration directory
      type: zfs_dataset
      default: config # (7)
      host_permissions:
        uid: 1000
        gid: 1000
        mode: "755"
    - name: MOVIES_PATH
      label: Movie library
      type: path
      default: ""
      optional: true
    - name: PUID
      label: User ID for the application process
      type: string
      default: "1000"
    # PGID, TZ: the same shape
  variants:
    - id: latest
      label: Latest
      default: true
    - id: pkg
      label: FreeBSD quarterly packages
  appjail: # (8)
    director: "..."
    makejail: "..."
    template_conf: "..."
    env_defaults: "..."
```

1.  **Image**: a standard OCI reference. In a FreeBSD catalog it points to a FreeBSD-native image; in a Linux catalog it points to a Linux image.
2.  **Jail annotation**: passed by ocijail to `jail_set(2)`. See [2.8](#28-freebsd-jail-annotations).
3.  **Variable references**: `${NAME}` in the compose is filled from `.env`, which the client writes from the `variables` answers. The compose itself is never edited.
4.  **Format version**: `"0.1"` for everything this page describes.
5.  **Icon**: a path relative to the catalog, see [3](#3-catalog-distribution).
6.  **Web port**: the host side of the port the web UI is published on, so the client can link to it.
7.  **App data**: a relative default is a folder under the client's app data location, made with `host_permissions`.
8.  **AppJail bundle**: the same app for AppJail, rendered by the catalog. See [2.10](#210-appjail-the-appjail-bundle).

The top-level `name` is the app id. A client names the project after the stack it installs instead, and drops `container_name`, so the same app can be installed twice.

---

### 2.1 `info` (Application Metadata)

| Field | Required | Description |
| :--- | :--- | :--- |
| `id` | Yes | The app id: lowercase letters, digits, `.`, `_`, `-`. Matches the catalog entry and the manifest's file name. |
| `name` | Yes | Human-readable title. |
| `description` | Yes | One or two sentences on what the app does. |
| `category` | Yes | A grouping for the store (`Media`, `Storage`, `Network`, ...). |
| `class` | Yes | `service`, `stack` or `part` (see below). |
| `icon` | No | Path to the icon, relative to the catalog (`icons/<id>.svg` or `.png`). |
| `version` | No | The upstream version of the default tag. |
| `upstream_url` | No | The upstream project (source repository). |
| `web_url` | No | The upstream project's website. |
| `web_port` | No | The host port of the web UI: a literal (`"8096"`) or a variable reference (`${WEB_PORT}`). Gives the app an **Open** link. |
| `web_https` | No | `true` when the web UI answers over HTTPS. |
| `own_origin` | No | `true` when the app checks `Origin` and `Referer` against its own address (e.g. UniFi), so a names provider forwards those headers as the backend's own origin. |
| `name_env` | No | A map of `VAR: template` filled when a names provider gives the app a name (`{name}` for the primary name, `{names}` for all of its names comma-separated), for apps that check a host allowlist (e.g. SABnzbd) or require a public URL in `.env`. |
| `only_for_archs` | No | The architectures the image is built for, in FreeBSD `uname -p` spelling (`amd64`, `aarch64`), when it is not built for every one. The catalog entry's `architectures` normalizes them to Go/OCI spelling (`amd64`, `arm64`). |

Two additional `info` fields are proposed but not implemented yet: `requires` (an array of `{id, optional, reason}` application dependencies) and `health_url` (a relative HTTP path to probe and open instead of `/`).

#### Application classes (`class`)

- **`service`**: one container that runs and serves. The client shows its state and, with `web_port`, an **Open** link.
- **`stack`**: several services that make one application (an app with its database, cache, or worker). The compose holds all of them; [`networking` and `hostnames`](#24-networking-and-hostnames-stacks) say where each goes and how the others find it.
- **`part`**: a component image built to run as part of a `stack` (for example `immich-server` inside `immich`, or `weavestream-api` and `weavestream-worker` inside `weavestream`). Catalogs omit `part` repos from the top-level `apps` list and record them in their stack's `parts` array instead, so searching a part's name in the store finds its stack.
- **`cli`**: a run-once tool. Catalogs leave these out; a client never installs one.
- **`agent`**, **`gui`**: reserved (proposed): a daemon with no web UI, and a graphical app.

#### Icons

1. **Square**: 1:1. A vector SVG has a square `viewBox`.
2. **Size**: raster icons 256×256 to 512×512 px. **At most 64 KB**.
3. **Format**: PNG, WebP or SVG. An SVG holds no scripts and loads nothing (deciding the format from the bytes rather than the file extension is proposed).
4. **No baked shadows**: clients draw their own.
5. **Cached locally**: the catalog copies repo icons into `icons/<id>.<ext>`, and the client fetches and caches each app's `icon` (relative or URL) when refreshing a catalog so the store never depends on external links at render time.

---

### 2.2 `variables` (Install Prompts)

Each variable is a prompt in the install wizard and a line in `.env`. The compose reads it as `${NAME}`.

| Field | Required | Description |
| :--- | :--- | :--- |
| `name` | Yes | The environment variable name. Unique in the manifest. |
| `type` | Yes | One of the types below. An unknown type is treated as `string`. |
| `default` | No | The value offered. Always a string; `""` when omitted. |
| `label` | No | The prompt shown to the user. |
| `optional` | No | `true`: may be left empty. Default `false`. |
| `level` | No | Where the wizard shows it: `primary` (up front), `options` (changed sometimes) or `advanced` (rarely). When absent, the client decides from the type. |
| `generate` | No | Secrets only. `false`: a value only its owner has (a tunnel token, an API key), which the user MUST type. See below. |
| `host_permissions` | No | `zfs_dataset` only: `uid`, `gid` and octal `mode` for the folder the client makes. Default `1000`, `1000`. |
| `image` | `image_tag` only | The image whose tag this variable picks (`ghcr.io/daemonless/immich-server`). |

#### Types

| Type | Prompt | Behavior |
| :--- | :--- | :--- |
| `string` | Text field | Any text. |
| `secret` | Masked field | A password or key. See **Secrets** below. |
| `port` | Port number | 1–65535. Checked for a clash with ports in use before install. |
| `path` | Host folder picker | An absolute host path. An empty default asks for the user's own folder (a media library); with `optional: true` it may stay empty. |
| `zfs_dataset` | App data folder | A folder the client makes for the app. A relative default resolves under the client's app data location and the stack's own folder; the client applies `host_permissions`. |
| `image_tag` | Tag picker | The tag of the image named by `image`, in a stack that runs several images. It follows the tag picked for the stack unless the user changes it; the client lists the tags the registry publishes for that image. |
| `public_url` | Address field | The address the app is opened at (links in mail it sends, sign-up checks). `http://` or `https://` with a host, optionally a port and path. The client suggests one from where the install puts the app. |

#### Secrets

A secret's `default` is a placeholder (`changeme`, `your-encryption-key-here`), never a value to install: every install that kept it would share the same password.

- A **required** secret (`optional` not `true`) that the user leaves empty MUST be generated by the client: fjord generates 64 random hex characters (or 20 unambiguous letters and digits when [`login.password`](#26-login-app-sign-in) points at the variable) and names the variable in its output.
- With **`generate: false`** the value cannot be made up (a tunnel token from a provider's dashboard). The client asks for it and does not install without it.
- An **optional** secret left empty stays empty: for some apps empty means "off".
- On a reinstall over kept app data, the client SHOULD reuse the secrets the data was set up with; new ones would lock the app out of its own database.

#### Path placeholders

Host paths, and the defaults a [choice](#25-choices-questions-at-install) seeds, may contain:

- `{{base}}` or `{{appdata}}`: the client's app data location.
- `{{stack}}`: the stack's own folder name, so two installs of one app never share a folder.

---

### 2.3 `variants` (Image Tags)

The tags an image is published under, for the user to pick one at install.

```yaml
variants:
  - id: latest
    label: Latest
    default: true
  - id: pkg
    label: FreeBSD quarterly packages
  - id: pkg-latest
    label: FreeBSD latest packages
```

| Field | Description |
| :--- | :--- |
| `id` | The tag. |
| `label` | What the wizard shows. |
| `default` | `true` on the tag installed when the user picks none. |
| `version` | The upstream version of this tag, when set in the manifest. |
| `aliases` | Other tags that are the same build. |

The catalog entry repeats the list with each variant's `image` and `version` filled in. Before install the client asks the registry which architectures the chosen tag is built for, and refuses a tag with no build for the host.

---

### 2.4 `networking` and `hostnames` (Stacks)

A stack knows which of its services people open and which are its database and cache. The person installing it should not have to say.

```yaml
x-fjord:
  networking:
    immich-server: default     # the network the install was told to use
    immich-public-proxy: default
    "*": private               # a segment only this stack's services reach
  hostnames:
    database: DB_HOSTNAME      # the variable the others read to find it
    redis: REDIS_HOSTNAME
    immich-machine-learning: IMMICH_ML_HOST
```

- **`networking`** maps a service to `default` (the network the user picked for the install), `private` (a segment only this stack's services reach), or a network name used as it stands. `"*"` stands for every service not named.
- **`hostnames`** maps a service to the variable that carries its host name. With container DNS a service is reachable at its own name, so the client sets the variable to the service name. Nothing is allocated, and nothing is written back.

---

### 2.5 `choices` (Questions at Install)

A stack may ask a question at install: which database, or whether to run a part. **The compose as published is the default answer**: a client that ignores `choices` installs the default and gets a working app.

```yaml
x-fjord:
  choices:
    - id: database
      kind: database
      label: Database
      default: sqlite
      options:
        - id: sqlite
          label: SQLite
          env:
            GITEA__database__DB_TYPE: sqlite3
        - id: postgres
          label: PostgreSQL
          env:
            GITEA__database__DB_TYPE: postgres
            GITEA__database__HOST: postgres
          defaults:
            DATABASE_LOCATION: "{{base}}/{{stack}}/postgres"
          secrets: [GITEA__database__PASSWD]
          services: |
            postgres:
              image: ghcr.io/daemonless/postgres:17
              restart: always
              ...
          depends_on:
            gitea: [postgres]
          hostnames:
            postgres: GITEA__database__HOST
          appjail:
            director: "..."
    - id: machine_learning
      kind: part
      label: Machine learning
      default: "on"
      options:
        - id: "on"
        - id: "off"
          env:
            IMMICH_ML_ENABLED: "false"
          drop: [immich-machine-learning]
```

| Field | Description |
| :--- | :--- |
| `id` | The choice's id. |
| `kind` | `database` (which database the app uses) or `part` (a service to run or not). |
| `label`, `doc` | The question, and a sentence of help. |
| `default` | The id of the option the published compose already is. |
| `options` | The answers, each with the fields below. |

An option says what picking it changes. Every field is optional:

| Option field | Description |
| :--- | :--- |
| `id`, `label`, `doc` | The answer and its help text. |
| `env` | Variables to set. |
| `defaults` | Variables the added services need, as defaults the user may change. May use [path placeholders](#path-placeholders). |
| `secrets` | Variables to treat as required secrets (generated when left empty). |
| `services` | A compose fragment: services to add. |
| `depends_on` | Per existing service, the added services it waits for. |
| `drop` | Services to remove. |
| `hostnames` | The added services' share of [`hostnames`](#24-networking-and-hostnames-stacks). |
| `ask` | Values the user MUST give when this option is picked (a database they already run): `name`, `label`, `type` (`string` or `secret`), `default`, and `values` (allowed value → label) for a pick list. |
| `appjail` | The option's AppJail form: `director` (services to add to the director file), `files` (files they reference beside it), `hostnames` (director service → variable). |

---

### 2.6 `login` (App Sign-In)

When an app has a built-in default login or takes its initial credentials from environment variables, `x-fjord.login` declares them so the client can show how to sign in beside **Open**:

```yaml
x-fjord:
  login:
    user: admin
    password: ${ADMIN_PASSWORD}
    note: "Shown on the first-run screen if you change it later."
```

| Field | Description |
| :--- | :--- |
| `user` | A literal username (the app's built-in default) or a `${VAR}` reference resolved from `.env`. |
| `password` | A literal password or a `${VAR}` reference resolved from `.env`. When it points at a generated secret, fjord generates 20 unambiguous letters and digits (no `0`/`O`/`1`/`l`/`I`) so a person can type it. |
| `note` | Optional note shown with the login (for example, where the app writes a token or how first-run sign-in works). |

---

### 2.7 `provides.names` (Names and HTTPS)

An app that serves as a reverse proxy and local certificate authority for other stacks declares `x-fjord.provides.names`:

```yaml
x-fjord:
  provides:
    names:
      port: 8443
      key: ${RP_PAIRING_KEY}
      setup_token: ${RP_SETUP_TOKEN}
      client_url: ${RP_PAIRING_URL}
      client_id: ${RP_PAIRING_ID}
      client_name: ${RP_PAIRING_NAME}
```

| Field | Description |
| :--- | :--- |
| `port` | The container port of the provider's HTTPS management API. |
| `key` | The `${VAR}` holding the bearer key the client authenticates with (generated by the client at install). |
| `setup_token` | Optional `${VAR}` holding the one-time token opened as `#token=<value>` on the provider's first-run setup page. |
| `client_url` | Optional `${VAR}` filled with the URL the client itself was opened at when installing the provider, so the provider can link back to it. |
| `client_id` | Optional `${VAR}` filled with the client's permanent instance ID, so the provider can tell several clients apart. |
| `client_name` | Optional `${VAR}` filled with the client's display name (for example `"fjord on myhost"`). |

---

### 2.8 FreeBSD Jail Annotations

Jail parameters a service needs go in its `annotations:` block. ocijail passes them to `jail_set(2)`; on AppJail the bundle's jail template carries the same parameters.

| Annotation | Grants | Used by |
| :--- | :--- | :--- |
| `org.freebsd.jail.allow.mlock` | Locking memory pages. | .NET apps (Sonarr, Radarr, Jellyfin). |
| `org.freebsd.jail.allow.sysvipc` | System V IPC. | PostgreSQL shared memory. |
| `org.freebsd.jail.allow.raw_sockets` | Raw sockets. | Ping and other network diagnostics. |
| `org.freebsd.jail.vnet` | `new`: a VNET jail with its own network stack. | Apps that manage their own interfaces (a WireGuard client). |

---

### 2.9 `host` (Proposed)

Not implemented by any client yet. Proposed host preparation before install:

| Field | Type | Description |
| :--- | :--- | :--- |
| `vnet_required` | boolean | The service must run in its own VNET jail. |
| `vnet_bridge` | string | A variable reference (`${NETWORK_IFACE}`) naming the host bridge, with a `network_interface` variable to pick it. |
| `devfs_rules` | list | devfs rules for hardware passthrough (`add path 'drm/*' unhide` for a GPU). |
| `min_freebsd_version` | string | The oldest FreeBSD release the app runs on (`"15.0"`). |

With them, two proposed additions to [`variables`](#22-variables-install-prompts): a `network_interface` type (pick a host interface or bridge), and `zfs_properties` on a `zfs_dataset` (`recordsize`, `compression`) for a real ZFS dataset instead of a folder.

---

### 2.10 `appjail` (The AppJail Bundle)

The same app for [AppJail](https://appjail.readthedocs.io/), rendered by the catalog (daemonless's dbuild) from the image's own metadata, and run as-is by `appjail-director`. Every field is a whole file, as text:

| Field | Written as | Description |
| :--- | :--- | :--- |
| `director` | `appjail-director.yml` | The project: one AppJail service per compose service. |
| `makejail` | `Makejail` | The build recipe the director file refers to. |
| `template_conf` | `template.conf` | The jail parameters (the annotations' AppJail form). |
| `env_defaults` | `.env` | The variables with their defaults. The client fills them from the same answers as the compose. |
| `extras` | under their own names | Further files, such as a sidecar's own template. |

A manifest without `appjail` cannot be installed on AppJail. A client that does not run AppJail ignores the block.

---

## 3. Catalog Distribution

A catalog is static files (`catalog.json`, `manifests/<id>.yaml`, `icons/`) served over HTTPS at a base URL. When a host publishes one or more catalogs under subdirectories, the catalog builder also writes `sources.json` at the root as an index:

```json title="sources.json"
[
  { "name": "daemonless", "catalog": "daemonless/catalog.json", "apps": 122 }
]
```

Clients are configured with each catalog's base URL (for example `https://catalog.daemonless.io/v1/daemonless`) and fetch `catalog.json` relative to it. `manifest_url` and relative `icon` paths resolve against the directory `catalog.json` is in:

```json title="daemonless/catalog.json"
{
  "catalog_name": "Daemonless",
  "fjord_version": "0.1",
  "maintainer": "https://daemonless.io",
  "icon": "icons/catalog.svg",
  "os": ["freebsd"],
  "generated": "2026-11-04T19:00:00Z",
  "apps": [
    {
      "id": "immich",
      "name": "Immich",
      "description": "High performance self-hosted photo and video management solution.",
      "category": "Photos & Media",
      "class": "stack",
      "icon": "icons/immich.svg",
      "upstream_url": "https://github.com/immich-app/immich",
      "web_url": "https://immich.app/",
      "image": "ghcr.io/daemonless/immich-server",
      "manifest_url": "manifests/immich.yaml",
      "version": "v3.3.5",
      "architectures": ["amd64"],
      "variants": [],
      "parts": [
        {
          "id": "immich-server",
          "name": "Immich Server",
          "image": "ghcr.io/daemonless/immich-server"
        }
      ]
    },
    {
      "id": "radarr",
      "name": "Radarr",
      "description": "Automated movie collection manager.",
      "category": "Media Management",
      "class": "service",
      "icon": "icons/radarr.svg",
      "upstream_url": "https://github.com/Radarr/Radarr",
      "web_url": "https://radarr.video/",
      "image": "ghcr.io/daemonless/radarr",
      "manifest_url": "manifests/radarr.yaml",
      "version": "6.4.4.10685",
      "architectures": ["amd64"],
      "variants": [
        {
          "id": "latest",
          "label": "Latest",
          "default": true,
          "image": "ghcr.io/daemonless/radarr:latest",
          "version": "6.4.4.10685"
        }
      ]
    }
  ]
}
```

| Catalog field | Description |
| :--- | :--- |
| `catalog_name` | Shown in the store. |
| `fjord_version` | The format version, `"0.1"`. |
| `maintainer` | Who publishes it. |
| `icon` | The catalog's own icon, relative. |
| `os` | The target operating systems for entries in this catalog in OCI spelling (`["freebsd"]`, `["linux"]`), unless an entry sets its own `os`. A client hides entries whose OS cannot run on the host. |
| `generated` | When it was built (RFC 3339, UTC). |
| `apps` | One entry per installable app: the manifest's `info`, plus `image` (without a tag), `manifest_url`, `architectures` (in Go/OCI spelling: `amd64`, `arm64`), `variants` (with each `image`, `version` and optional `aliases`; `[]` for stacks that span multiple images), optional `os`, and for `class: stack` entries, `parts` (`[{id, name, image}]`, untagged) listing the sibling `class: part` component images the stack runs. |

Two additional catalog fields are proposed but not implemented yet: top-level `catalog_version` (a release version of the catalog's content, separate from the wire format's `fjord_version`) and per-app `updated` (RFC 3339 timestamp of when that app's entry last changed).

A client SHOULD refresh a catalog on its own, on a schedule (fjord: every 6 hours by default, set in Settings), and show when it last did. A catalog read only when someone clicks a button goes stale without anyone noticing. Catalogs leave out base images, `class: cli` tools, and `class: part` component images (which appear inside their stack's `parts` list instead).

---

## 4. Execution, UI & Lifecycle Contract

### 4.1 Install

1. **Resolve**: read the catalog entry and fetch its manifest.
2. **Choices**: apply the picked answer to each [choice](#25-choices-questions-at-install): add and drop services, set variables, collect the asks.
3. **App data**: pick the app data location. Relative `zfs_dataset` defaults resolve under it, in the stack's own folder; [path placeholders](#path-placeholders) expand.
4. **Secrets**: reuse the secrets of kept app data; generate every required secret still empty ([rules](#secrets)).
5. **Pre-flight**: refuse before changing anything if a port is taken, a folder cannot be made, or the chosen tag has no build for the host's architecture.
6. **Folders**: make the app data folders and apply `host_permissions`.
7. **Networks**: put each service where [`networking`](#24-networking-and-hostnames-stacks) says; set [`hostnames`](#24-networking-and-hostnames-stacks) variables to service names.
8. **`.env`**: write every value beside the compose. The compose is not edited.
9. **Run**: hand it to the engine (`podman-compose` or, with the [bundle](#210-appjail-the-appjail-bundle), `appjail-director`), verify the containers stay up, and if a name was requested, register it with the names provider in the daemon.

### 4.2 Teardown

1. **Stop**: stop the services and remove their containers or jails.
2. **Data**: keep the app data unless the user asks to delete it.
3. **Networks**: remove a stack's private network with the stack.

### 4.3 Update

1. **Say what changes**: per service, the version change in words (patch, minor, major, or a new build of the same version) and the package diff.
2. **Pull and recreate**: pull the new image and recreate the service (or update every behind stack in sequence via **Update all**). `.env` stays as it is.
3. **Watch**: check that the service stays up for 30 seconds. If it does not, roll back to the image it ran before.
4. **New variables** (proposed): when a new manifest adds variables, ask for the missing ones before recreating.
