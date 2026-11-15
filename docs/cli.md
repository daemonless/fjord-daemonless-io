---
title: "CLI Reference"
description: "Command-line interface for fjord: install catalog apps, inspect stacks, stream logs, update all stacks, roll back, open shells, and manage credentials from the terminal."
---

# Command-Line Interface (`fjord`)

`fjord` ships inside the `fjordd` binary and drives the exact same daemon API as the web UI. Actions stream their live output to your terminal, exit status reflects the checked container or jail outcome (not just an engine exit code), and `--json` emits structured output for scripts and automation.

```sh
# Package installs create the symlink automatically; for manual binary installs:
ln -sf /usr/local/sbin/fjordd /usr/local/sbin/fjord
```

 Every subcommand also works when invoked as `fjordd <command>`.

---

## 1. Connecting &amp; Authentication

- **Local host (default)**: By default `fjord` connects over the root-only Unix domain socket at `/var/db/fjord/fjordd.sock` (or `$FJORD_SOCKET`). No password prompt is needed when running as `root` (or via `doas` / `sudo`) on the host.
- **Remote HTTP access**: Set `FJORD_URL` (for example `http://192.168.5.10:3567` or your reverse-proxy HTTPS URL) and `FJORD_SESSION` to a valid session token when driving a remote host.

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `FJORD_SOCKET` | `/var/db/fjord/fjordd.sock` | Local Unix socket used when `FJORD_URL` is unset. |
| `FJORD_STACKS_DIR` | `/var/db/fjord/stacks` | Stack root (its parent directory sets the default socket location). |
| `FJORD_URL` | *(unset)* | Target HTTP/HTTPS base URL instead of the local Unix socket. |
| `FJORD_SESSION` | *(unset)* | Session cookie value sent with remote `FJORD_URL` requests. |

---

## 2. Installing Applications

`fjord install` asks `fjordd` for the same default install plan the web wizard computes (App Data root, attached Folder Sets, free ports, default network, and generated secrets), applies your overrides, and streams the install and post-start health check:

```sh
# Install Radarr with host defaults (default engine, Folder Sets, free port)
fjord install radarr

# Install Gitea with PostgreSQL on a dedicated LAN network and local HTTPS name
fjord install gitea \
  --choice database=postgres \
  --network vlan5 \
  --ip 192.168.5.42 \
  --given-name gitea

# Install Jellyfin on the AppJail engine with an explicit tag and variable override
fjord install jellyfin \
  --engine appjail \
  --tag pkg-latest \
  --set TZ=America/New_York
```

### `fjord install` Flags

| Flag | Description |
| :--- | :--- |
| `--name <name>` | Stack name on disk and in the UI (defaults to the catalog app ID). |
| `--engine <podman\|appjail>` | Container runtime engine for this stack. |
| `--tag <tag>` | Image tag or release channel (`latest`, `pkg`, `pkg-latest`). |
| `--network <net>` | Attach the primary service to a named LAN network, `bridge`, `host`, or `none`. |
| `--ip <ipv4>` | Pin a specific IPv4 address on `--network`. |
| `--mac <mac>` | Pin a specific MAC address on `--network`. |
| `--given-name <label\|none>` | Register `<label>.<domain>` with your [names provider](networking.md#names-and-local-https), or `none` to skip naming. |
| `--app-data <path>` | Override the App Data root directory for this stack. |
| `--catalog <id>` | Select a specific catalog source when multiple catalogs offer the same app ID. |
| `--set KEY=VAL` | Set a manifest variable or host path (repeatable). |
| `--choice ID=OPTION` | Select an install-time choice such as `database=postgres` (repeatable). |

---

## 3. Stack Lifecycle &amp; Inspection

Flags and positional arguments can appear in either order (`fjord status radarr --json` or `fjord status --json radarr`).

```sh
# List all stacks, engine, state, and address
fjord ls
fjord ls --json

# Detailed service and container status for one stack
fjord status immich
fjord status immich --json

# Start, stop, or restart a stack
fjord up radarr
fjord down radarr
fjord restart radarr

# Stream container logs (all services or specific services)
fjord logs -f --tail 100 immich
fjord logs -f immich server

# Open an interactive terminal inside a running container or jail
fjord exec radarr
fjord exec immich database
```

---

## 4. Updates &amp; Rollback

Updates run inside `fjordd` with the same 30-second stay-up check and rollback recording as the web UI (see [Updates](updates.md)):

```sh
# Update one stack (all services, or only named services)
fjord update radarr
fjord update immich server machine-learning

# Update every stack that currently has an available image update, one at a time
fjord update --all

# Roll back to the previous recorded image (all services or specific services)
fjord rollback radarr
fjord rollback immich server
```

---

## 5. Removal, Catalogs, Pruning &amp; Account Management

```sh
# Stop and remove a stack (keeps App Data on disk by default)
fjord delete radarr

# Non-interactive removal including the stack's App Data folders
fjord delete --purge-data --yes radarr

# Refresh all configured App Store catalogs immediately
fjord catalog refresh

# Reclaim unused containers, networks, build cache, and dangling images
fjord prune
fjord prune --all-images --volumes --engine podman

# Create or reset the web UI sign-in account (signs out existing browser sessions)
fjordd passwd
fjordd passwd --user admin
printf '%s\n' "$NEW_PASSWORD" | fjordd passwd --user admin --password-stdin
```

---

## 6. Command Summary

| Command | Summary |
| :--- | :--- |
| `fjord ls [--json]` | List stacks and their runtime status. |
| `fjord status <stack> [--json]` | Show detailed stack, service, and container status. |
| `fjord up <stack>` | Bring a stack up. |
| `fjord down <stack>` | Stop and tear down a stack. |
| `fjord restart <stack>` | Restart a stack in place. |
| `fjord update <stack\|--all> [svc...]` | Pull and recreate a stack (or every stack with updates). |
| `fjord logs [-f] [--tail N] <stack> [svc...]` | Stream container or jail logs. |
| `fjord rollback <stack> [svc...]` | Roll back services to their previous image. |
| `fjord delete [--purge-data] [--yes] <stack>` | Stop and remove a stack (optionally deleting App Data). |
| `fjord install <app> [flags]` | Install an application from the catalog. |
| `fjord catalog refresh` | Re-fetch all configured catalogs. |
| `fjord prune [--engine E] [--all-images] [--volumes]` | Reclaim unused container, image, and volume disk space. |
| `fjord exec <stack> [svc]` | Open an interactive shell inside a running service. |
| `fjordd passwd [--user NAME] [--password-stdin]` | Set or reset the web UI user name and password. |
