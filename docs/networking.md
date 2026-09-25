---
title: "Networking"
description: "How fjord connects containers: published ports on the bridge, the host's own stack, an address of their own on your LAN by DHCP or from a pool, private networks between a stack's services, and addresses that stay put across updates and reboots."
---

# Networking

Every service in a stack is somewhere on a network. fjord offers four places,
and the **Services** tab of each stack shows and changes where each service is.

---

## 1. Where a service can live

| Network | Reached at | Good for |
| :--- | :--- | :--- |
| **bridge** (default) | this host's address, on the ports the service publishes (`http://host:8181`) | most apps; nothing to set up |
| **host** | this host's address, on the ports the app binds itself | apps that need the host's network directly (DHCP servers, discovery) |
| **LAN** | an address of its own on your network (`http://192.168.5.25`) | apps you want reachable like another machine: own DNS name, own DHCP reservation, no port clashes |
| **private** | only by the other services of the same stack | a database or cache that nothing outside the app should reach |

A service can be on more than one: a typical multi-service app puts its web
front end on the LAN and its database on the stack's private network, so the
database is reachable by the app and by nothing else.

!!! note "Bridge needs pf"
    Ports published on the bridge network go through pf's rdr anchors. The
    **System** page checks for them; see
    [Troubleshooting](troubleshooting.md#packet-filter-pf-anchors-for-podman).

---

## 2. LAN networks

A LAN network gives a container its own address on one of the host's
bridges, as if it were another machine plugged into the same switch.

**What it needs on the host**

- The [cni-epair](https://github.com/daemonless/cni-epair) plugin. fjord
  offers to install it: an **Install** button in the setup wizard and on the
  **System** page (see [Installation](install.md#1-host-prerequisites)).
- A bridge with the host's network card (or a VLAN on it) as a member. If the
  host has none, **Networks → New network** shows the exact commands to create
  one, both for now and in `rc.conf` for every boot.

**Creating one:** **Networks → New network**, pick the bridge, give it a name,
and choose where its addresses come from (next section). Stacks can then be
put on it from the install wizard or the **Services** tab.

### Where addresses come from

- **DHCP** (the default where the plugin supports it): your router hands out
  the address, the same way it does for any other device. fjord records the
  service's MAC address, so the router keeps giving it the same lease; add a
  reservation for that MAC on the router to make it permanent.
- **Pool**: fjord hands out addresses from a range you choose. Pick a range
  your router's DHCP server does not use, and keep your fixed addresses
  outside it (for example, fixed addresses in `.10–.99`, the pool
  `.100–.199`).
- **Static**: nothing is handed out; every service on the network needs an
  address you type in.

---

## 3. Addresses that stay put

A service keeps its address through updates, restarts and reboots:

- The first time a service starts on a LAN network, fjord writes its address
  (on a pool network) or its MAC (on a DHCP network) into the stack's
  `compose.yaml`. From then on it gets the same one every time.
- An address or MAC you set yourself in the **Services** tab is never changed.
- An address another stack already has is refused: **Save** and **Start** say
  which stack holds it (`192.168.5.19 on vlan5 is smokeping's address — give
  seerr another address in the Services tab`).
- Reservations left behind by containers that no longer exist are released
  the next time a stack starts on that network.

---

## 4. Finding each other by name

Services of the same stack reach each other by service name
(`postgres://database:5432`) on any network they share. On the podman engine
that takes the **cni-dnsname** plugin (`pkg install cni-dnsname`); without it
a multi-service app starts, fails to find its database, and restarts over and
over. The **System** page checks for it.

---

## 5. IPv6

A pool or static network can carry an IPv6 segment next to its IPv4 one;
services on it then get an address of each. DHCP networks are IPv4 only.

---

## 6. AppJail

AppJail stacks use AppJail's own virtual networks: each jail gets an address
behind NAT, and ports are published with `expose`. The **Networks** page lists
which networks each engine can use.
