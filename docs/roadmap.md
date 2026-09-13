---
title: "fjord Roadmap"
description: "What comes after fjord 0.2.0: stack dependencies and boot control, authentication, ZFS-backed app data with snapshots, and a fjord cluster that migrates stacks between hosts."
---

# Roadmap

What is planned after 0.2.0, in the order it is likely to land. Nothing here is a promise; issues and pull requests on [daemonless/fjord](https://github.com/daemonless/fjord) move things up.

---

## 0.3 — Dependencies and boot

### Stack dependencies
Within a stack, compose `depends_on` already orders services (and the AppJail director bundle does the same). Between stacks there is nothing yet. Planned: `x-fjord: depends_on: [postgres]`, settable from the Resources tab, honoured in three places:

- **Start** brings dependencies up first and says so in Output.
- **Stop / Delete** warn when another stack depends on this one.
- **Boot** orders stacks by the dependency graph.

Cycles are rejected at save.

### Start at boot
Today every stack that was running comes back on boot, in directory order. Planned: a per-stack **Boot** setting — *on*, *off*, or *manual* (never auto-start) — shown in the stack list and on the stack page; boot order from dependencies with an optional explicit priority; a stagger so ten stacks don't all pull at once.

## 1.0 gate — Authentication

There is none. A first-run administrator password, a session cookie, one middleware in front of the API and the terminal WebSocket. Nothing that faces the network is promoted out of "tech preview" before this.

## After that, roughly in order

- **Volumes per engine** — the Volumes page follows the default engine only; AppJail has no named volumes yet, so remote folders (NFS/SMB) need podman.
- **Update policy per stack** — *manual* (today), *notify*, or *auto* on a schedule, with the digest pin as the brake. Pairs with **notifications** (webhook, Discord, email) for "updates available" and "stack crashed".
- **Adopt existing containers and jails** — import a compose directory or a running container as a stack, for hosts built by hand.
- **Fix button** on readiness checks — run the safe, non-destructive fixes (`pkg install`, `service start`) from the UI with live output. Designed, not built.
- **Persistent shells** — a shell that survives navigating away.
- **Templates** — "New stack from…" a saved compose, for stacks no catalog has.
- **Extensions** — out-of-process extensions (checks, folder providers, catalog sources, UI pages, later engines) installed as packages. Designed; needs the internal engine refactor first.
- **Registry-verified architectures** — the store trusts each repo's declared build architectures.
- **Shared services** — one database stack used by several apps, built on dependencies.

## ZFS-backed app data

When the App data location is a ZFS dataset — which on a FreeBSD host it usually is — fjord should use ZFS rather than plain directories: a child dataset per app (`zroot/data/fjord/radarr`), so quotas, per-app usage and `zfs send` backups fall out; a **snapshot before every Update** with a **Rollback** button on the stack page; scheduled snapshots with retention. This is an operator-side policy of the App data location, never a per-manifest property: the same catalog has to work on UFS and Linux hosts, and pool tuning is not something an app author can know.

## Cluster and migration

The long-term shape: several fjord hosts that know each other, one UI over all of them, and a stack that can move between them.

- **Peers** — each fjord registers the others (address + token; needs authentication first). The stack list shows every host's stacks; install picks a host.
- **Migrate** — snapshot the app's dataset, `zfs send` it to the target while the stack keeps running, stop, send the final increment, recreate the stack on the target from its own files (compose, `.env`, bundle, icon), pre-flight there (engine, ports, folder sets — NFS resolves anywhere, local paths must exist), start, remove at the source. Dependencies move with the stack or are checked on the target.
- **Replicate** — scheduled sends of a stack's dataset to a peer as a warm standby, and *Restore* from it.

This is why authentication, dependencies and ZFS-backed data come first: each is a piece of this.

## Not planned

- TLS termination in `fjordd` — a reverse proxy does it better.
