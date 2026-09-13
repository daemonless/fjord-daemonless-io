---
title: "Installation & Service Setup"
description: "How to install and configure fjord on FreeBSD: host prerequisites, Podman and AppJail engine toolchains, rc.d service management, and environment configuration."
---

# Installation &amp; Service Setup

fjord runs as a standalone daemon (`fjordd`) managed by an `rc.d` service script. It interacts with your host's container engines—Podman, AppJail, or both—via local Unix sockets and standard CLI utilities.

---

## 1. Host Prerequisites

Follow the directions to set up [Podman](https://daemonless.io/guides/quick-start/#podman) and/or [AppJail](https://daemonless.io/guides/quick-start/#appjail) in the Daemonless Quick Start guide for packages, kernel settings, and PF firewall anchors. That guide is the single source of truth for host setup; this page only adds what fjord needs on top of it:

- **Podman**: fjord talks to Podman over `/var/run/podman/podman.sock` (requires `ocijail` 0.6.0 or newer). Enable and start `podman_service`:

    ```sh
    sysrc podman_service_enable=YES
    service podman_service start
    ```

- **AppJail**: fjord drives `appjail-director` instead of calling `appjail` directly (requires AppJail 5.5.0 or newer). Install `py-director`:

    ```sh
    pkg install -y sysutils/py-director
    ```

fjord is verified on FreeBSD 15.1 (amd64 and arm64).

!!! tip "Automated Diagnostics"
    If you install `fjordd` before configuring all prerequisites, the first-run wizard and the **System** dashboard will identify missing packages, dead sockets, or unconfigured PF anchors and display exact shell remediation commands.

---

## 2. Installing fjord

=== "Release binary"

    Every [release](https://github.com/daemonless/fjord/releases) ships static `fjordd` binaries for FreeBSD amd64 and arm64 with the UI embedded, the rc script, and a source tarball (vendored modules, prebuilt UI):

    ```sh
    fetch https://github.com/daemonless/fjord/releases/latest/download/fjordd-freebsd-$(uname -m)
    fetch https://github.com/daemonless/fjord/releases/latest/download/fjordd.rc
    install -m 755 fjordd-freebsd-* /usr/local/sbin/fjordd
    install -m 755 fjordd.rc /usr/local/etc/rc.d/fjordd
    ```

=== "Port"

    The port from the [daemonless ports overlay](https://github.com/daemonless/freebsd-ports) installs `fjordd` and its rc script; its options pull in the engines (`PODMAN`: podman, podman-compose, catatonit — `APPJAIL`: appjail, appjail-director; both on by default, `make config` to change). Install those from packages first, or `make` builds each of them from source. It builds against the ports tree in `/usr/ports`.

    ```sh
    pkg install -y git podman sysutils/podman-compose catatonit appjail sysutils/py-director
    git clone https://github.com/daemonless/freebsd-ports
    cd freebsd-ports/sysutils/fjord && make install clean
    ```

    For the AppJail engine add `pkg install -y appjail sysutils/py-director`.

=== "git clone"

    Needs `go` and `npm`:

    ```sh
    pkg install -y git go npm
    git clone https://github.com/daemonless/fjord && cd fjord
    (cd ui && npm ci && npm run build)
    go build -o fjordd ./cmd/fjordd
    install -m 755 fjordd /usr/local/sbin/fjordd
    install -m 755 packaging/fjordd.rc /usr/local/etc/rc.d/fjordd
    ```

---

## 3. Starting the Service

Enable and start the `fjordd` daemon via FreeBSD's `service` framework:

```sh
sysrc fjordd_enable=YES
service fjordd start
```

Verify service execution:

```sh
service fjordd status
```

Open `http://<host-ip>:3567` in your browser. The initial setup wizard will verify your host readiness, prompt for your default App Data storage directory, and load the default application catalog.

---

??? note "Configuration Reference (Environment Variables)"

    Application-level options—including App Data datasets, custom Folder Sets, catalog feeds, and default engine selections—are configured through the web interface and persisted to `/var/db/fjord/settings.json`.

    Daemon network endpoints and storage paths are controlled via environment variables passed through `rc.conf`:

    ```sh
    # Example: Bind fjord to localhost on port 3567
    sysrc fjordd_env="FJORD_LISTEN=127.0.0.1:3567"
    ```

    | Environment Variable | Default Value | Description |
    | :--- | :--- | :--- |
    | `FJORD_LISTEN` | `:3567` | TCP listen address and port for the HTTP/WebSocket server. |
    | `FJORD_STACKS_DIR` | `/var/db/fjord/stacks` | Filesystem path where stack directories and compose files are maintained. |
    | `FJORD_STORAGE_BASE` | `/var/db/fjord/containers` | Default App Data location for container state until explicitly changed in Settings. |
    | `FJORD_ENGINE` | `podman` | Default engine assigned to new stack deployments (`podman` or `appjail`). |
    | `FJORD_PODMAN_SOCKET` | `/var/run/podman/podman.sock` | Path to the Libpod API Unix socket. |
    | `FJORD_HOST_ADDR` | `127.0.0.1` | Host address probed during pre-flight port conflict detection. |
    | `FJORD_CATALOG_URL` | *(unset)* | Custom catalog URL loaded on initial installation if replacing the default. |

??? warning "Security &amp; Network Exposure (Production Hosts)"

    `fjordd` executes with administrative privileges in order to interact with `/var/run/podman/podman.sock`, create ZFS datasets, and launch FreeBSD jails.

    **No authentication yet**: fjord currently operates in local trusted mode without an integrated authentication layer. Anyone with network access to the HTTP port can create, modify, and delete container workloads with host root equivalence.

    For production or remote hosts:

    1. **Bind to localhost**: Set `FJORD_LISTEN=127.0.0.1:3567` in `fjordd_env`.
    2. **Access via Encrypted Tunnel**: Route traffic to fjord using an SSH local port forward:
       ```sh
       ssh -L 3567:127.0.0.1:3567 user@freebsd-host
       ```
    3. **VPN / Overlay Mesh**: Place the host on a private WireGuard or Tailscale network and bind fjord to the VPN interface IP.
