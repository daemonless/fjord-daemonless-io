---
title: "Troubleshooting & Host Diagnostics"
description: "Diagnostics reference for fjord on FreeBSD and Linux: engine sockets, PF anchors, cni-epair DHCP hostnames, AppJail DNS, SELinux/firewalls, password resets, and storage locks."
---

# Troubleshooting &amp; Host Diagnostics

The **System** page and top **Conditions** banner continuously audit host readiness across FreeBSD and Linux. Below are root causes and copy-paste fixes for common host and runtime issues.

---

## 1. Host Readiness Checks

### Libpod API Socket (`podman.sock`)

- **Technical Role**: `fjordd` talks to Podman over `/var/run/podman/podman.sock` on FreeBSD (`/run/podman/podman.sock` on Linux) to inspect containers, stream logs, and open shells.
- **Symptom**: `fjord` reports the Podman engine is unavailable.
- **Remediation**:
    - **FreeBSD**:
      ```sh
      sysrc podman_service_enable=YES
      service podman_service restart
      ```
    - **Linux**:
      ```sh
      sudo systemctl enable --now podman.socket
      ```

    !!! note "Restarting `podman_service` on FreeBSD stops running Podman containers"
        On FreeBSD, containers started through the Libpod API socket stop when `podman_service` restarts. Bring your stacks back up with `fjord up <stack>` or from the **Stacks** page afterwards.

---

### `cni-epair` Version (`< 1.2.1`) &amp; Router Hostname Collisions (FreeBSD)

- **Symptom**: Every LAN container receives the FreeBSD host's own hostname in your router's DHCP table, or the host loses its DNS name.
- **Cause**: Versions of `cni-epair` prior to `v1.2.1` forwarded the host's hostname on container DHCP requests.
- **Remediation**: Click **Set up** on the **Setup** / **System** page (which installs `cni-epair v1.2.1+`), or upgrade via `pkg upgrade -y cni-epair`.

---

### OCI Jail Runtime (`ocijail` 0.6.0+) &amp; `conmon` (FreeBSD)

- **Symptom**: Unprivileged containers fail with permission errors on image files (`ocijail < 0.6.0` leaked host `umask`), or fail to start with a missing monitor error.
- **Remediation**:
  ```sh
  pkg install -y conmon ocijail
  pkg upgrade -y ocijail
  ```

---

### Packet Filter (PF) Anchors for Podman &amp; AppJail (FreeBSD)

- **Symptom**: Bridge-networked containers start cleanly, but inbound connections to published ports time out; or AppJail fails with `The nat command requires appjail-nat/jail/*` (exit code 78).
- **Remediation**: Click **Set up** on **Setup** / **System** to add the anchors automatically, or place them in `/etc/pf.conf` above filter rules (replacing `$ext_if` with your uplink interface) and reload with `pfctl -f /etc/pf.conf`:
  ```pf
  rdr-anchor "cni-rdr/*"
  nat-anchor "cni-rdr/*"
  nat-anchor "appjail-nat/jail/*"
  nat-anchor "appjail-nat/network/*"
  rdr-anchor "appjail-rdr/*"
  table <cni-nat>
  nat on $ext_if inet from <cni-nat> to any -> ($ext_if)
  ```

---

### AppJail Engine, Director &amp; Jail DNS (`dnsmasq`)

- **Symptom**: AppJail is unavailable, or multi-jail stacks cannot resolve sibling jail names on first boot.
- **Remediation**: Install `appjail` (5.5.0+), `sysutils/py-director`, and let **Setup → Set up** configure `dnsmasq` so bridge interfaces are answered dynamically as AppJail creates them:
  ```sh
  pkg install -y appjail sysutils/py-director dnsmasq
  service fjordd restart
  ```

---

### Linux Firewall (`firewalld` / `ufw`) &amp; SELinux Mount Labels

- **Symptom (Firewall)**: `fjordd` is running on Linux, but `http://<host>:3567` times out from another machine on your LAN.
- **Remediation (Firewall)**: Open port `3567/tcp` on your management LAN (`sudo firewall-cmd --add-port=3567/tcp --permanent && sudo firewall-cmd --reload` on Fedora, or `sudo ufw allow 3567/tcp` on Ubuntu). Published container ports are opened automatically by Podman.
- **Symptom (SELinux)**: Container logs report `Permission denied` on a custom host bind mount (such as `/srv/media`).
- **Remediation (SELinux)**: `fjord` labels App Data directories automatically; for custom host paths on enforcing SELinux systems, enable the `:z` mount option on the stack's **Resources** tab (or run `chcon -R -t container_file_t <dir>`).

---

## 2. Account &amp; Runtime Issues

### Locked Out or Forgot Web UI Password
Reset the administrator password as root on the host (this also signs out all active browser sessions):

```sh
fjordd passwd
```

### Port Conflict (`port X/tcp is already in use`)
`fjord`'s pre-flight detected a port collision and named the holding container (or reported a host process). Inspect host listeners with `sockstat -4 -l -p <port>` on FreeBSD (`ss -tlnp 'sport = :<port>'` on Linux), or pick another port on the stack's **Resources** tab.

### Storage Layer Busy (`Found incomplete layer ... pool or dataset is busy`)
A `containers-storage` layer is marked incomplete while an AppJail jail still has that layer nullfs-mounted:
1. Run `mount | grep <layer-id>` to see which jail holds the mount.
2. Stop that stack (`fjord down <stack>` or **Stop** in the UI) so `buildah` can release and clean the layer, then start it again (`fjord up <stack>`).

### Database `Access denied` After Editing `DB_PASSWORD` in `.env`
Database images initialize user credentials only when creating an empty data directory. Changing `DB_PASSWORD` in `.env` later updates the application container, not the existing database user. Restore the original password in `.env` or run `ALTER USER` inside the database (`fjord exec <stack> database`).

### Remote SMB Volume Refused on FreeBSD
FreeBSD's kernel `mount_smbfs` speaks SMB1 only, which modern NAS servers reject. Use NFS (`nfs://server/export`) on FreeBSD hosts; `smb://` named volumes are supported on Linux hosts.
