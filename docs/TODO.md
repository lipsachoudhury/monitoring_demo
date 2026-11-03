# TODO — Local monitoring demo

Run this only on the Linux machine where Cursor is open. Bind to `127.0.0.1`. One shared `admin` account. Read-only CPU, memory, network, and listening ports. No SSH, no host control, no public deploy.

Out of scope: alerts, history, Windows/macOS, roles, SSO, and any action that changes the host.

## 1. Project initialization and basic UI

- [x] Create a Python 3.11+ venv and pin `flask` and `python-dotenv` in `app/requirements.txt`
- [x] Add an app factory, config from the environment, and `run.py` on `127.0.0.1:5000`
- [x] Add Blueprint stubs and three placeholder pages: Sign in, Servers, Live view
- [x] Add a shared layout and minimal CSS so each page is readable
- [x] Add `.env.example` and ignore `.env`, `.venv`, and `__pycache__`
- [x] **Security:** no secrets in code or git; do not bind `0.0.0.0`
- [x] **Docs:** local setup in `README.md` (venv, install, copy `.env.example`)

## 2. Sign-in and unit tests

- [ ] Sign-in form posts username and password
- [ ] Accept only `admin` and `ADMIN_PASSWORD_HASH` from `.env` via `check_password_hash`
- [ ] Start a session on success; keep a failed attempt on the page with one generic message
- [ ] Sign out clears the session; other pages redirect to sign-in when unsigned
- [ ] pytest: valid login, wrong password, wrong username, logout, unsigned redirect
- [ ] **Security:** never log or store the plain password; cookie `HttpOnly` and `SameSite=Lax`; `SECRET_KEY` from the environment only
- [ ] **Docs:** how to generate `SECRET_KEY` and `ADMIN_PASSWORD_HASH`; what the tests cover

## 3. Server list

- [ ] Seed `localhost` on first run so the demo works before anyone adds a host
- [ ] Add form: display name, host (`localhost` or `127.0.0.1` only), OS fixed to Linux
- [ ] Save the list in one local file; remove deletes that entry only
- [ ] pytest: seed, add, reject a non-local host, remove
- [ ] **Security:** fixed file path; no shell; reject any host other than the local machine
- [ ] **Docs:** where the list file lives, and that remove does not change the Linux host

## 4. Live read-only metrics

- [ ] Show CPU used percent
- [ ] Show memory used, total, and percent
- [ ] Show bytes sent and received, plus the rate since the last refresh
- [ ] Show listening TCP ports: port, bind address, and process name when the OS provides it
- [ ] If one figure fails, that card shows an error and the rest of the page still loads
- [ ] Leave restart, stop, kill, and edit controls off the page
- [ ] pytest with a stubbed reader: full success and one failed metric
- [ ] **Security:** read local counters only; no SSH, no shell, no control actions
- [ ] **Docs:** the four figures and that nothing is stored after the page closes

## 5. Refresh every 5 seconds

- [ ] JSON metrics endpoint that requires a session
- [ ] Live view polls about every 5 seconds and updates the cards
- [ ] pytest: unsigned call is rejected; signed call returns all four sections
- [ ] **Security:** session required; response is read-only JSON
- [ ] **Docs:** refresh interval

## 6. GitHub Actions CI

- [ ] Workflow on push and pull request: Python 3.11, install deps, run pytest
- [ ] Pass a dummy `SECRET_KEY` and password hash as workflow env; do not use real secrets
- [ ] **Security:** do not print secrets; do not upload `.env`
- [ ] **Docs:** one line in `README.md` that CI runs the unit tests

## 7. Local check

- [ ] `python run.py`, then open `http://127.0.0.1:5000`
- [ ] Unsigned users cannot open the server list or the live view
- [ ] `admin` and the hashed password sign in; a wrong password does not
- [ ] CPU, memory, network, and ports show and refresh on their own
- [ ] Add and remove a list entry; the live view still cannot control the host
- [ ] **Security:** process listens on `127.0.0.1` only
- [ ] **Docs:** mark the checks above in `README.md` when they pass
