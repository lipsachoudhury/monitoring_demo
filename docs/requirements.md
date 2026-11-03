# Demo Monitoring Infrastructure — Requirements

Local, read-only view of a Linux server’s CPU, memory, network, and ports. Internal teams use a browser instead of signing in to the host.

This is a demo that runs on the Linux machine where it is installed. Setup stays on that one machine.

## Decisions for this demo

These choices keep the demo small. Change them if the product should do more.

- One shared sign-in for L1, L2, and L3. Username is `admin`. The password is stored only as a hash in `.env`.
- The UI can add and remove Linux servers in its list. It cannot change the host (no restart, stop, kill, or config edits).
- Live metrics are read on the machine running the app. The supported monitored host is that local Linux server (`localhost`).
- The screen shows current CPU, memory, network, and listening ports. It refreshes about every 5 seconds. It does not keep history.
- Windows, macOS, alerts, roles, and remote SSH collection are out of scope.

## Problem

L1, L2, and L3 currently sign in to Linux servers to see whether memory, CPU, network, and ports look healthy. That is slow for a status check and gives people shell access they do not need for a glance at usage.

## Users

All three groups use the same screens and the same account.

| Team | What they use it for |
| --- | --- |
| L1 | See if the server is busy or short on memory, and which ports are listening |
| L2 | Confirm CPU, memory, and network during an incident |
| L3 | Check the same figures while investigating, without a shell session |

## Goals

- Show live Linux resource and port data in the browser.
- Keep the demo usable by signing in once and opening the local server.
- Let a user add a Linux server to the list without editing code.

## Feature 1 — Read-only monitoring UI

A signed-in user can:

- See a short list of Linux servers.
- Open one server and read current usage.
- Watch the figures update on their own every 5 seconds.
- Sign out.

The monitoring view has no actions that affect the server. It does not offer restart, shutdown, process kill, package changes, or file edits.

**CPU.** Overall used percent.

**Memory.** Used and total (MiB or GiB) and used percent.

**Network.** Bytes sent and received since the counters started, plus a simple send/receive rate since the previous refresh.

**Ports.** Listening TCP ports: port number, bind address, and process name when the OS provides it.

If a figure cannot be read, that card shows an error and the rest of the page still loads.

## Feature 2 — Sign in

- The sign-in page asks for username and password.
- The demo username is `admin`.
- The password is checked against `ADMIN_PASSWORD_HASH` in `.env`. The app does not store or log the plain password.
- A match starts a session. Other pages redirect to sign-in when there is no session.
- A failed attempt stays on the sign-in page and shows a generic failure message.
- Signing out clears the session.

There is one account. The app does not have separate L1, L2, or L3 permissions.

## Feature 3 — Add a Linux server

A signed-in user can add a server with:

- Display name
- Host (`localhost` or `127.0.0.1` for this demo)
- Operating system fixed to Linux

The list is stored in a local file on the app host. The user can remove an entry from the list. Removing an entry does not change the Linux host.

The local server is the one that returns live CPU, memory, network, and port data. After a fresh start, that local server is already on the list so the demo works before anyone adds a host.

## Screens

1. **Sign in** — username, password, submit.
2. **Servers** — Linux servers, link to the live view, add form, remove.
3. **Live view** — read-only CPU, memory, network, and ports for the local server, updating every 5 seconds.

## Local setup

Run this on the demo machine. Use Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
cp .env.example .env
```

Set these in `.env`:

- `SECRET_KEY` — any long random string
- `ADMIN_USERNAME=admin`
- `ADMIN_PASSWORD_HASH` — hash of the demo password

Create the hash (replace the sample password):

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin'))"
```

Start the app and open `http://127.0.0.1:5000`:

```bash
python run.py
```

Sign in as `admin` with the password you hashed. Open the local server and confirm CPU, memory, network, and ports update without another login.

## Out of scope

- Alerts, thresholds, email, or chat notifications
- Charts kept after the page is closed, or any metrics database
- Windows or macOS agents
- SSH to other hosts, and storing SSH passwords
- More than one user, SSO, or team-specific permissions
- Any control action on the server
- Public deployment; the demo is bound to the local machine

## Acceptance

- Unsigned users cannot open the server list or the live view.
- `admin` and the hashed password sign in; a wrong password does not.
- The local Linux server shows CPU, memory, network, and listening ports.
- Those values refresh without a manual reload.
- A user can add and remove a Linux server entry.
- The live view has no control that restarts a service or kills a process.
