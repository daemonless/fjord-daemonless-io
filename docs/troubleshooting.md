---
title: "Troubleshooting & Host Diagnostics"
description: "Comprehensive diagnostics reference for fjord on FreeBSD: readiness audits, Libpod socket failures, PF firewall redirection, ocijail runtime bugs, and storage lock remediation."
---

# Troubleshooting &amp; Host Diagnostics

This reference provides root-cause diagnosis and remediation procedures for host readiness audits, engine communication failures, and runtime jail misconfigurations.

---

## 1. Host Readiness Diagnostics

The **System** dashboard runs automated audits against your FreeBSD host environment. The table below details the technical significance of each audit, typical failure symptoms, and remediation commands.

### Libpod API Socket (`podman.sock`)

- **Technical Role**: fjord communicates with Podman over a local Unix domain socket (`/var/run/podman/podman.sock`) to query container status, stream stdout/stderr logs, and spawn interactive exec sessions.
- **Failure Symptom**: fjord reports the Podman engine is unavailable; stack status indicators show disconnected sockets.
- **Remediation**:
  Ensure the `podman_service` rc daemon is enabled and running:
  ```sh
  sysrc podman_service_enable=YES
  service podman_service restart
  ```
  !!! note "Restarting `podman_service` stops your containers"
      On FreeBSD, containers launched via the Libpod API socket die with the service. Restart your stacks from fjord after cycling it.

---

### Container Init &amp; Monitor (`catatonit` &amp; `conmon`)

- **Technical Role**: `catatonit` serves as PID 1 inside container pods to reap zombie processes and route signals; `conmon` monitors container lifecycle, preserving exit codes and I/O streams while the engine daemon is idle.
- **Failure Symptom**: Compose stacks fail immediately upon execution with an unhelpful `no such file or directory` error from the OCI runtime.
- **Remediation**:
  Install both packages via FreeBSD `pkg`:
  ```sh
  pkg install -y catatonit conmon
  ```

---

### OCI Jail Runtime (`ocijail`)

- **Technical Role**: `ocijail` is the low-level OCI runtime that translates container manifests into FreeBSD `jail(8)` instances.
- **Failure Symptom**: Containers fail to drop privileges or report permission errors when accessing application configuration files. Older versions (< 0.6.0) leak host `umask` settings into container root filesystems, resulting in world-inaccessible image assets.
- **Remediation**:
  Verify and upgrade `ocijail` to 0.6.0 or newer:
  ```sh
  pkg install -y ocijail
  pkg upgrade -y ocijail
  ```

---

### Packet Filter (PF) Anchors for Podman

- **Technical Role**: Podman's bridge networking (`cni-rdr`) requires PF redirection and NAT anchors to publish container ports to external network interfaces.
- **Failure Symptom**: Containers start successfully and bind internal ports, but inbound traffic to host ports hangs or drops with no connection established.
- **Remediation**:
  Add the following anchor declarations to `/etc/pf.conf` above any blocking filter rules, replacing `$ext_if` with your physical network interface:
  ```pf
  rdr-anchor "cni-rdr/*"
  nat-anchor "cni-rdr/*"
  table <cni-nat>
  nat on $ext_if inet from <cni-nat> to any -> ($ext_if)
  ```
  Reload the Packet Filter configuration:
  ```sh
  pfctl -f /etc/pf.conf
  ```

---

### AppJail Engine &amp; Director

- **Technical Role**: Enables native FreeBSD jail management via `appjail` and `appjail-director`.
- **Failure Symptom**: The AppJail backend is grayed out, or deployment fails with `"the appjail engine is not available on this host"`.
- **Remediation**:
  Install `appjail` (5.5.0+) and the director package:
  ```sh
  pkg install -y appjail sysutils/py-director
  service fjordd restart
  ```

---

### Packet Filter Anchors for AppJail

- **Technical Role**: AppJail assigns virtual network addresses to jails and routes external traffic via NAT anchors.
- **Failure Symptom**: Virtual network jails fail to launch; stack output reports `The nat command requires appjail-nat/jail/*` and `appjail-director up` exits with code 78.
- **Remediation**:
  Add AppJail anchors to `/etc/pf.conf` and reload:
  ```pf
  nat-anchor "appjail-nat/jail/*"
  nat-anchor "appjail-nat/network/*"
  rdr-anchor "appjail-rdr/*"
  ```
  ```sh
  pfctl -f /etc/pf.conf
  ```

---

## 2. Common Runtime Issues

### Port Conflict: `pre-flight failed: port X/tcp is already in use`
- **Cause**: fjord's pre-flight detected that a host port the stack needs is already held — by a local daemon (BIND, Unbound, Nginx), by another container (named in the message), or by another stack's host-network sidecar (two stacks each shipping a postgres on 5432 or a redis on 6379 collide this way).
- **Remediation**: Inspect the holding process using `sockstat`:
  ```sh
  sockstat -4 -l -p <port>
  ```
  Either stop the conflicting service or open the stack in fjord, select a different host port under **Resources**, and launch the stack.

---

### Director Failure: `ProjectLocked`
- **Cause**: Two `appjail-director` invocations collided on the same stack workspace (for instance, clicking **Apply** while a background container restart was still active).
- **Remediation**: Allow running operations to complete, or inspect active processes:
  ```sh
  ps aux | grep director
  ```
  Once the active process completes, retry the operation from fjord.

---

### Storage Corruption: Incomplete Layer Locks
- **Symptom**: every `podman`/`buildah` command warns `Found incomplete layer "<id>", deleting it` and then fails with `cannot unmount ... pool or dataset is busy`; image pulls, updates and AppJail rebuilds all fail after that.
- **Cause**: a container-storage layer record is flagged incomplete while a jail still has that layer mounted as its root (AppJail jails are built from buildah containers, so this is usually one of them). Every storage operation first tries to delete the layer and can't.
- **Remediation**:
  1. Find who holds it: `mount | grep <layer id>` shows the jail root the layer is nullfs-mounted into.
  2. Stop that stack from fjord (**Stop** runs `down`, which removes the jail and lets buildah release the layer).
  3. Start it again, then retry the operation that failed.

---

### Network Error on Host-Network Jail: `errno 43 (Protocol not supported)`
- **Cause**: The jail was initialized with IPv4 disabled (`ip4=disable`) instead of inheriting host networking.
- **Remediation**: When deploying host-network stacks on AppJail, ensure the jail template explicitly includes `ip4: inherit`. Triggering **Update** or **Apply** from the stack view recreates the jail with proper inheritance annotations.

---

### Remote SMB Volume Mount Refusal
- **Cause**: FreeBSD's kernel SMB client (`mount_smbfs`) supports only SMB1 dialect. Modern NAS devices and file servers reject SMB1 negotiations by default for security.
- **Remediation**: For FreeBSD hosts, connect persistent network storage using NFS (`nfs://server/export`).
