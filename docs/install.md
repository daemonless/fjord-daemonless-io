---
title: "Installation & Service Setup"
description: "How to install and run fjord on FreeBSD: package installation, starting the daemon, host setup, and configuration."
---

# Installation &amp; Service Setup

Installing `sysutils/fjord` from official FreeBSD binary packages automatically installs `fjordd`, its `rc.d` service script, both container engines (Podman and AppJail), and all required networking plugins.

---

## 1. Quick Install (FreeBSD Package)

Install `sysutils/fjord` and start the daemon:

```sh
pkg install -y fjord

sysrc fjordd_enable=YES
service fjordd start
```

### Enabling Podman

If you plan to deploy stacks using the Podman engine, enable and start the Podman API service socket:

```sh
sysrc podman_service_enable=YES
service podman_service start
```

### Accessing the Web Interface

Open your browser to:

```text
http://<host-ip>:3567
```

On first visit, the setup wizard will verify your host environment, ask where App Data goes, and initialize the application catalog.

!!! tip "Automated Diagnostics & Fixes"
    `fjordd` automatically audits your FreeBSD host environment. If any kernel parameters, Packet Filter (PF) firewall anchors, or sockets require attention, the setup wizard and the **System** dashboard will highlight them with copy-paste shell remediation commands.

---

## 2. Alternative Installation Methods

??? "Release binary"

    Every [release](https://github.com/daemonless/fjord/releases) ships static `fjordd` binaries for FreeBSD amd64 and arm64 with the web UI embedded:

    ```sh
    fetch https://github.com/daemonless/fjord/releases/latest/download/fjordd-freebsd-$(uname -m)
    fetch https://github.com/daemonless/fjord/releases/latest/download/fjordd.rc
    install -m 755 fjordd-freebsd-* /usr/local/sbin/fjordd
    install -m 755 fjordd.rc /usr/local/etc/rc.d/fjordd

    sysrc fjordd_enable=YES
    service fjordd start
    ```

??? "FreeBSD Port"

    Build from the FreeBSD ports tree:

    ```sh
    cd /usr/ports/sysutils/fjord && make install clean

    sysrc fjordd_enable=YES
    service fjordd start
    ```

    `make config` allows selecting which engine dependencies (`PODMAN`, `APPJAIL`) are included.

??? "Build from Source (git clone)"

    Requires `go` and `npm`:

    ```sh
    pkg install -y git go npm
    git clone https://github.com/daemonless/fjord && cd fjord
    (cd ui && npm ci && npm run build)
    go build -o fjordd ./cmd/fjordd
    install -m 755 fjordd /usr/local/sbin/fjordd
    install -m 755 packaging/fjordd.rc /usr/local/etc/rc.d/fjordd

    sysrc fjordd_enable=YES
    service fjordd start
    ```

---

## 3. Configuration &amp; Environment

Storage locations, folder sets, catalogs, and default engine choices are managed directly through the web UI and saved to `/var/db/fjord/settings.json`.

Network listen addresses and directory roots can be overridden via `rc.conf`:

```sh
# Example: Bind fjord to localhost on port 3567
sysrc fjordd_env="FJORD_LISTEN=127.0.0.1:3567"
```

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `FJORD_LISTEN` | `:3567` | TCP listen address and port for the HTTP server. |
| `FJORD_STACKS_DIR` | `/var/db/fjord/stacks` | Directory where stack definitions and compose files reside. |
| `FJORD_STORAGE_BASE` | `/var/db/fjord/containers` | Default App Data location for application state and databases. |
| `FJORD_ENGINE` | `podman` | Default engine assigned to new stacks (`podman` or `appjail`). |
| `FJORD_PODMAN_SOCKET` | `/var/run/podman/podman.sock` | Path to the Libpod API Unix socket. |
| `FJORD_HOST_ADDR` | `127.0.0.1` | Host address probed during pre-flight port conflict detection. |
| `FJORD_CATALOG_URL` | *(unset)* | Custom catalog URL loaded on initial install if replacing the default. |

---

## 4. Security &amp; Network Access

`fjordd` executes with administrative privileges to manage jail lifecycles, configure ZFS datasets, and communicate with container sockets.

!!! warning "Local Trusted Mode"
    fjord operates in local trusted mode without an integrated authentication barrier. Anyone with network access to port `3567` can control containers on the host with root equivalence.

For production or remote hosts:

1. **Bind to loopback**: Set `FJORD_LISTEN=127.0.0.1:3567` in `fjordd_env`.
2. **Access via SSH tunnel**:
   ```sh
   ssh -L 3567:127.0.0.1:3567 user@freebsd-host
   ```
3. **Or access via VPN**: Place the host on a private WireGuard or Tailscale network and bind fjord to the VPN interface address.
