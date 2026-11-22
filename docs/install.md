---
title: "Installation & Service Setup"
description: "Install and configure fjord on FreeBSD (Podman and AppJail) and Linux (Podman): packages, first-boot sign-in, daemon configuration, and security."
---

# Installation &amp; Service Setup

`fjord` ships as a single static Go binary (`fjordd`) embedding both its web interface and the [`fjord` CLI](cli.md). It runs natively on **FreeBSD 15+** (driving Podman with `ocijail` and AppJail side by side) and on **Linux** (Fedora, Debian, and Ubuntu with rootful Podman).

---

## 1. Quick Install

=== "FreeBSD (Default)"

    Installing `sysutils/fjord` from official FreeBSD packages pulls in `fjordd`, the `fjord` CLI symlink, its `rc.d` service script, both container engines (Podman and AppJail), and the required networking plugins (`cni-epair`, `cni-dnsname`):

    ```sh
    pkg install -y fjord

    sysrc podman_service_enable=YES fjordd_enable=YES
    service podman_service start
    service fjordd start
    ```

    Open `http://<host>:3567` and claim the host using the one-time setup code printed in `/var/db/fjord/setup-code`:

    ```sh
    cat /var/db/fjord/setup-code
    ```

    ??? "Alternative FreeBSD methods (Release binary, Port, Source)"

        **Release binary (`v0.4.5`):**

        Every [GitHub release](https://github.com/daemonless/fjord/releases) publishes static FreeBSD `amd64` and `arm64` binaries plus `SHA256SUMS`:

        ```sh
        pkg install -y podman sysutils/podman-compose conmon ocijail
        fetch -o /usr/local/sbin/fjordd https://github.com/daemonless/fjord/releases/latest/download/fjordd-freebsd-$(uname -m)
        fetch -o /usr/local/etc/rc.d/fjordd https://github.com/daemonless/fjord/releases/latest/download/fjordd.rc
        chmod 755 /usr/local/sbin/fjordd /usr/local/etc/rc.d/fjordd
        ln -sf fjordd /usr/local/sbin/fjord

        sysrc podman_service_enable=YES fjordd_enable=YES
        service podman_service start
        service fjordd start
        ```

        **FreeBSD Port:**

        ```sh
        cd /usr/ports/sysutils/fjord && make install clean
        sysrc fjordd_enable=YES
        service fjordd start
        ```

        `make config` selects which engine dependencies (`PODMAN`, `APPJAIL`) are pulled in.

        **Build from Source:**

        ```sh
        pkg install -y git go npm
        git clone https://github.com/daemonless/fjord && cd fjord
        (cd ui && npm ci && npm run build)
        go build -o fjordd ./cmd/fjordd
        install -m 755 fjordd /usr/local/sbin/fjordd
        ln -sf fjordd /usr/local/sbin/fjord
        install -m 755 packaging/fjordd.rc /usr/local/etc/rc.d/fjordd

        sysrc fjordd_enable=YES
        service fjordd start
        ```

=== "Linux (.deb / .rpm / Script)"

    Each release ships native `.rpm` and `.deb` packages (`amd64` and `arm64`) that pull in `podman` and `podman-compose`, enable `podman.socket` and `fjordd.service`, install the `fjord` CLI symlink, and print the URL to open:

    ```sh
    V=0.4.5 A=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')

    # Fedora / RHEL-compatible
    sudo dnf install -y https://github.com/daemonless/fjord/releases/download/v$V/fjord-$V-linux-$A.rpm

    # Debian / Ubuntu
    curl -fsSLO https://github.com/daemonless/fjord/releases/download/v$V/fjord-$V-linux-$A.deb
    sudo apt install -y ./fjord-$V-linux-$A.deb
    ```

    Upgrading runs the same command with the new version: `fjordd` restarts cleanly while running stacks stay up. Uninstalling the package preserves `/var/db/fjord` and all stack data.

    **Or install with `install-linux.sh`:**

    ```sh
    # Ensure podman and podman-compose are installed first, then:
    curl -fsSL https://github.com/daemonless/fjord/releases/latest/download/install-linux.sh | sudo sh
    ```

    Then read the one-time setup code and open `http://<host>:3567`:

    ```sh
    sudo cat /var/db/fjord/setup-code
    ```

    - **App Store catalog on Linux**: Fresh Linux installs enable the verified Linux catalog (180+ tested LinuxServer.io applications plus multi-OS Daemonless appliances such as `reverse-proxy` and `pkg-cache`), filtering out FreeBSD-only jail images automatically.
    - **Host firewall &amp; SELinux**: On Fedora Server (`firewalld`) or Ubuntu (`ufw`), **Setup** and **System** check whether port `3567` is open on your LAN and provide the exact command to allow it. With SELinux enforcing, `fjord` automatically labels App Data directories it creates and prompts to add `:z` when mounting custom host paths.

!!! tip "Automated Setup &amp; Host Checks"
    On first visit, **Setup** verifies your container sockets, Packet Filter (PF) anchors (`cni-rdr` / `appjail-nat`), `cni-epair` (v1.2.1+), `cni-dnsname`, firewall rules, and storage paths. Anything `fjordd` can configure safely gets a one-click **Set up** button; host-level edits show exact copyable commands.

---

## 2. Signing In &amp; Account Management

`fjord` protects the web UI and HTTP API with a built-in administrator account:

- **First-boot claim**: On a fresh host with no account, `fjordd` writes a random setup code to `/var/db/fjord/setup-code` (`0600`, root-readable only). The browser prompts for that code to create your user name and password, ensuring only an administrator with root on the host can claim the instance.
- **Unattended / Ansible provisioning**: Pre-create the account before starting `fjordd` to skip the setup prompt completely:
  ```sh
  printf '%s\n' "$ADMIN_PASSWORD" | fjordd passwd --user admin --password-stdin
  ```
- **Password reset**: Run `fjordd passwd` as root on the host at any time. Resetting the password invalidates all existing browser sessions.
- **Sessions**: Browser sessions last 30 days from last activity and persist across `fjordd` restarts and upgrades. Manage active sessions or change credentials in **Settings → Account**.
- **External SSO / Reverse Proxy Auth (`FJORD_AUTH=none`)**: If you place `fjord` behind your own authenticating proxy (Authelia, Pocket ID, or a private Tailscale proxy), set `FJORD_AUTH=none`. For safety, `fjordd` refuses `FJORD_AUTH=none` unless `FJORD_LISTEN` is bound to loopback (`127.0.0.1:3567`) or `FJORD_TRUSTED_PROXY` names the proxy's address or CIDR (rejecting all direct connections).

---

## 3. Configuration &amp; Environment

App Data roots, Folder Sets, catalogs, names providers, and default engine choices are configured in **Settings** and persisted to `/var/db/fjord/settings.json`.

Daemon startup flags can be set via environment variables (`sysrc fjordd_env="..."` on FreeBSD, or `/etc/default/fjordd` / systemd drop-in on Linux) or matching CLI flags on `fjordd`:

```sh
# Example (FreeBSD): listen on loopback only behind a local reverse proxy
sysrc fjordd_env="FJORD_LISTEN=127.0.0.1:3567 FJORD_TRUSTED_PROXY=127.0.0.1"
service fjordd restart
```

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `FJORD_LISTEN` | `:3567` | TCP listen address and port for the HTTP server. |
| `FJORD_STACKS_DIR` | `/var/db/fjord/stacks` | Directory holding stack definitions (`compose.yaml`, `.env`, `state.json`). Its parent directory is the `fjord` root. |
| `FJORD_STORAGE_BASE` | `/var/db/fjord/containers` | Default App Data location until configured in **Settings → Storage**. |
| `FJORD_ENGINE` | `podman` | Default engine for new deployments (`podman` or `appjail`) until set in **Settings**. |
| `FJORD_PODMAN_SOCKET` | `/var/run/podman/podman.sock` | Path to the Libpod API Unix socket (`/run/podman/podman.sock` on Linux). |
| `FJORD_HOST_ADDR` | `127.0.0.1` | Host address probed for pre-flight port conflicts and advertised to the UI. |
| `FJORD_CATALOG_URL` | *(unset)* | Bootstraps a custom App Store catalog URL on a fresh install. |
| `FJORD_ALLOWED_HOSTS` | *(unset)* | Comma-separated extra hostnames `fjordd` accepts when served behind a reverse proxy. |
| `FJORD_TRUSTED_PROXY` | *(unset)* | Comma-separated proxy IPs or CIDRs whose `X-Forwarded-For` / `X-Forwarded-Proto` headers are trusted (marks session cookies `Secure` over HTTPS). |
| `FJORD_AUTH` | `password` | `password` (built-in sign-in) or `none` (requires loopback `FJORD_LISTEN` or `FJORD_TRUSTED_PROXY`). |

---

## 4. Security &amp; Network Access

!!! warning "`fjordd` Has Root Authority on Its Host"
    Anyone signed in to `fjord` can mount host paths, join host networks, and open root shells inside containers and jails. Furthermore, `fjordd` speaks plain HTTP on `:3567` by default so credentials cross the wire unencrypted unless terminated by TLS.

For production and remote deployments:

1. **Never expose port `3567` directly to the public internet.** Keep `:3567` on a trusted management LAN/VLAN or private WireGuard/Tailscale network.
2. **Use HTTPS via a reverse proxy**: Pair `fjord` with the [Daemonless Reverse Proxy](networking.md#names-and-local-https) (or Caddy/Traefik) and set `FJORD_TRUSTED_PROXY` + `FJORD_ALLOWED_HOSTS` so traffic is encrypted and session cookies are marked `Secure`.
3. **Or bind strictly to loopback** (`FJORD_LISTEN=127.0.0.1:3567`) and connect over an SSH tunnel (`ssh -L 3567:127.0.0.1:3567 admin@host`) or run commands locally via the [`fjord` CLI](cli.md).
