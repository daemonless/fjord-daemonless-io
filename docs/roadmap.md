---
title: "fjord Roadmap"
description: "What comes after fjord 0.4.3: a ZFS dataset per app, then a fjord that is safe to leave alone and keeps itself up to date (jobs, history, notifications, auto-update with snapshots), then scheduled snapshots, compose history and 1.0."
---

# Roadmap

What is planned, in the order it is likely to land. Nothing here is a promise. Issues and pull requests on [daemonless/fjord](https://github.com/daemonless/fjord) move things up. What already shipped is in the [changelog](https://github.com/daemonless/fjord/blob/main/CHANGELOG.md).

---

## 0.4.3: in release candidates now

Update all with a diff of what changes, a `fjord` command for the shell, typed settings in the install wizard, a stack's parts in the App Store, health checks with a recovery policy per stack, a banner for host and engine problems, and a round of hardening. Try it from the [v0.4.3 pre-releases](https://github.com/daemonless/fjord/releases).

## 0.4.4: a dataset per app

When the App data location is on ZFS, a new install gets a dataset of its own (`zroot/containers/radarr`), not a plain folder inside a shared one. It comes before auto-update because auto-update's snapshots need it: a snapshot then covers one app, and restoring is a rollback rather than a copy. On a host or location that is not ZFS (Linux, UFS), app data stays in plain folders. Stacks you already have are left as they are until 0.5.0 can move them.

## 0.5.0: safe to leave alone, keeps itself up to date

### Jobs, Cancel and History
- **Every action is a job** that fjord runs itself: install, update, start, stop, delete, prune. An Activity tray lists what is running, queued and recently done. A second action on a busy stack waits its turn instead of being refused.
- **Cancel** stops a running pull or health watch. A cancel in the middle of a recreate leaves the old container running, never none.
- **History per stack**: every start, update, rollback and automatic run, with what triggered it and how it ended, plus what happened while you were away (stops, crashes and why, health changes). Roll back or restore data from any entry.

### Notifications and the catalog
- **Notifications** to ntfy, Gotify, Discord, email or a webhook, per event, and an optional heartbeat URL for an outside monitor.
- **New in the catalog**: a badge and a row for apps added recently, and a catalog's news as one line on the App Store.
- **App notices**: an app can say "this update needs you to do something", and Update waits until you confirm.
- **App changes, reviewed**: when an app's compose changes in the catalog, an installed stack lists the changes in words and applies them on top of your own edits.

### Auto-update and data safety
- **Move an existing stack onto its own dataset**, as a job with progress: stop, copy, check, switch, start. The old folder is removed only once the app runs.
- **A snapshot before every update**, the last three kept, and **Restore data** in one click: stop, roll the dataset back, roll the image back, start.
- **Keep up to date** per stack, from *Notify* through *Rebuilds*, *Patch* and *Minor* to *All*, in a maintenance window, one stack at a time, with a health watch and automatic rollback. A **Schedules** page says what runs when, and offers Run now.
- **Dependencies between stacks**: `x-fjord: depends_on`, started first, warned about on stop and delete, and used for boot order.

### The host
- **Clean up leftovers**: jails, network interfaces and address reservations that nothing uses any more. One click removes what fjord can prove it made.
- **Networks come back after a reboot** before the stacks that need them.
- **Private means private**: stacks on different private networks cannot reach each other.
- **Better IPv6**: pinned addresses, Open links and published ports over v6, SLAAC on LAN networks.
- **Ctrl+K**: jump to any stack, app or page.

## 0.6.0: snapshots and compose history

- **Scheduled snapshots** with retention, and what changed between two snapshots.
- **Per-app usage, quota and `zfs send`** on the datasets from 0.4.4.
- **Compose history**: every successful deploy keeps its compose, `.env` and image digests; compare two, redeploy one.

## 1.0

- **Compose checks with fixes**: on Save and before a start, mistakes fjord knows about (an address in use on the LAN, a .NET app without `allow.mlock`, `:latest` with auto-update) are said, with a one-click fix where the fix is certain.
- **Release notes in Version…**, from the image's source repository.
- **Logs** from every service of a stack in time order.
- **Docs** for people setting fjord up for the first time: install, networks, updates, AppJail.
- The UI tests run on every pull request.

## After 1.0

- **Cluster and migration**: several fjord hosts in one UI; a stack moves between them with its data (snapshot, `zfs send`, final increment, recreate on the target), or keeps a warm standby on a peer.
- Shared services, templates ("New stack from…"), extensions, persistent shells, signature checks on images.

## Ideas, not scheduled

- **Jails you build yourself**: a recipe (`Containerfile` or `Makejail`) that fjord builds, updates and rolls back like any other stack.
- **VPN networks**: a WireGuard network a stack can join, with no way out if the tunnel drops.
- **Kubernetes** as a third engine next to podman and AppJail: a single FreeBSD node where a stack is a pod. It waits on the node pieces being FreeBSD packages.

## Not planned

- TLS in `fjordd`. A reverse proxy in front of it does that better.
