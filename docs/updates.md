---
title: "Updates"
description: "How fjord updates single stacks and all stacks at once: SBOM package diffs, Update all, major-version database safety, 30-second health watches, AppJail parity, and one-click rollback."
---

# Updates

`fjordd` checks container registries on its own background schedule for every installed stack, both Podman and AppJail, and shows exactly what will change before any container or jail is touched. Every update runs inside the daemon (closing your browser tab never interrupts an in-progress update) and verifies the new workload stays healthy.

---

## 1. What the Update Panel Shows

![The Update panel: a patch version, the packages that change, one service ticked](img/update-dark.png#only-dark){ .glightbox }
![The Update panel: a patch version, the packages that change, one service ticked](img/update-light.png#only-light){ .glightbox }

Clicking **Update** on a stack opens a diff per service powered by each image's published SBOM:

- **Rebuild of the same version**: The upstream app version is unchanged, while underlying FreeBSD or OS packages inside the image were updated (listed with old and new package versions).
- **Patch, minor, or major bump**: Names the running and new application versions, image digests, and changed internal packages.

Select individual services or the entire stack and click **Update** (or run `fjord update <stack>` from the [CLI](cli.md)).

### Update All
When one or more stacks have updates available, the **Stacks** page and sidebar offer **Update all** (and `fjord update --all` in the CLI):

1. A combined pre-flight diff shows every stack and service that will change, including version numbers, digests, and SBOM package diffs. Any stack can be unchecked before starting.
2. `fjordd` updates one stack at a time, preserving LAN addresses and recording the previous image digest for rollback on each stack.
3. Each sidebar and row badge clears as its stack passes its post-update health watch.

---

## 2. Picking Versions, Channels &amp; Safety Guardrails

**Change Version...** in a stack's menu (`⋮`) lists the image's release trains (`latest`, `pkg`, `pkg-latest`, or major-version trains, including architecture-prefixed tags like LinuxServer's) and runs the version switch as a tracked daemon job:

- **Safe upgrade offers only**: `fjord` never offers pre-releases, cross-flavor jumps, or multi-major skips automatically.
- **Stateful database protection**: Databases whose on-disk format is tied to a major release (`postgres`, `mongo`, `elasticsearch`, `opensearch`) are **never** offered a major version jump automatically; major upgrades stay explicit after a dump and restore.
- **Pin to exact digest**: Locks a service to its current SHA-256 manifest digest so republished rolling tags never move it until you unpin.
- **Architecture &amp; pull safety**: Tags lacking a build for your host (`amd64` vs. `arm64`) are disabled up front. If an image pull fails (network error, rate limit, missing tag), **`fjordd` aborts before touching the running container or jail**, leaving your existing workload up and recording the pull error in **Output**.

---

## 3. Post-Update Verification &amp; Rollback

After pulling the new image (including pulling Makejail base images before recreating AppJail services), `fjordd` recreates the target services and verifies two gates:

1. **Every target container or jail was actually replaced** (preventing stale containers held by open exec sessions from masquerading as updated).
2. **30-second stay-up watch**: `fjordd` watches the new containers or jails for 30 seconds. Any unexpected exit, crash loop, or empty jail marks the update **Update failed** in the UI and **Output** log.

**Roll back** (or `fjord rollback <stack> [svc...]`) restores the recorded previous image digest, runs the same health checks, and pins that digest so you stay on the known-good build until you unpin.

---

## 4. Apply After Editing

Editing `compose.yaml`, `appjail-director.yml`, or `.env` and clicking **Save** writes to disk without restarting anything. Clicking **Apply** recreates **only** the services whose configuration changed, resolves YAML anchors safely, and runs the same stay-up health check.

---

## 5. AppJail Parity

AppJail stacks have full update parity with Podman stacks:

- Per-service **Change Version...**, **Pin**, and **Unpin** (even while a post-update watch is active).
- Pre-recreate image pulls for `Makejail`-backed jails so failed pulls never stop a running jail.
- 30-second post-update stay-up watch and one-click **Roll back**.
