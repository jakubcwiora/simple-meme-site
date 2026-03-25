# Simple Meme Site

A Flask web application that scrapes and displays memes from [demotywatory.pl](https://demotywatory.pl). Users can add new random memes to their personal gallery or remove existing ones. The main focus of this project is the **CI/CD pipeline** built with GitHub Actions.

---

## Table of Contents

- [Application Overview](#application-overview)
- [Tech Stack](#tech-stack)
- [How Docker Compose Works (No Static File)](#how-docker-compose-works-no-static-file)
- [CI/CD Pipeline](#cicd-pipeline)
  - [Trigger Conditions](#trigger-conditions)
  - [CI: Test Job](#ci-test-job)
  - [CD: Build & Deploy Jobs](#cd-build--deploy-jobs)
  - [Required Secrets](#required-secrets)
- [Running Locally](#running-locally)

---

## Application Overview

| Feature | Description |
|---|---|
| **Meme Gallery** | Displays all stored memes in a responsive card grid |
| **Add Meme** | Scrapes a random meme from `demotywatory.pl/losuj` and saves it to the database |
| **Delete Meme** | Removes a meme from the gallery and the database |
| **Meme Popup** | Click any meme to view it enlarged in an overlay |

---

## Tech Stack

- **Backend**: Python / Flask
- **Database**: MySQL 8.0
- **Scraping**: BeautifulSoup4 + Requests
- **Containerization**: Docker (image hosted on [GitHub Container Registry](https://ghcr.io))
- **CI/CD**: GitHub Actions
- **Networking**: Tailscale VPN (used for secure SSH deployment)

---

## How Docker Compose Works (No Static File)

Previous versions of this project kept a single committed `docker-compose.yml` that developers edited by hand. That file has been **intentionally removed**. Instead, a `docker-compose.yml` is **generated dynamically** in each of the three contexts where it is needed, so credentials never live in version control and each context gets exactly the configuration it requires:

### 1 — CI testing (inside GitHub Actions)

`main.yml` writes a temporary `docker-compose.test.yml` inline using a shell heredoc every time the test job runs:

```
┌──────────────────────────────────────────┐
│  GitHub Actions runner                   │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  docker-compose.test.yml (generated│  │
│  │  at runtime, deleted afterwards)   │  │
│  │                                    │  │
│  │  services:                         │  │
│  │    mysql:           ◄──────────────┼──┼── only MySQL; no app container
│  │      image: mysql:8.0              │  │   (app runs directly on runner)
│  │      ports: 3306:3306              │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Flask app (pytest) ──► localhost:3306   │
└──────────────────────────────────────────┘
```

- Credentials are generated with `openssl rand` at the start of each run and exported to `$GITHUB_ENV`; they are never reused.
- Only a MySQL container is started — the Flask app itself runs directly on the runner, connecting to `localhost:3306`.
- After tests finish the container and generated file are removed by `docker compose -f docker-compose.test.yml down` (runs even on failure via `if: always()`).

### 2 — CD deployment (inside GitHub Actions → production server)

`deploy.yml` generates a `docker-compose.yml` **and** a `.env` file at deploy time, then transfers them to the production server over SSH:

```
GitHub Actions runner
  │
  ├─ builds Docker image  (tagged with $GITHUB_SHA)
  │
  ├─ generates docker-compose.yml  ← app + mysql services, credentials from GitHub Secrets
  ├─ generates .env                ← DB_NAME / DB_USER / DB_PASSWORD / MYSQL_ROOT_PASSWORD
  │
  └─ SCP files + gzipped image ──► production server (via Tailscale VPN + SSH)
                                        │
                                        └─ docker-compose up -d
```

- All sensitive values come from **GitHub Secrets** and are never stored in the repository.
- The image tag includes the commit SHA so every deploy is traceable and rollback-friendly.
- `schema.sql` is mounted into the MySQL container via `docker-entrypoint-initdb.d` so the schema is applied automatically on first start.

### 3 — Local developer setup (`start.sh`)

Running `./start.sh` starts an interactive session that:

1. Checks whether any MySQL container is already running and offers to reuse it.
2. Prompts for DB credentials (with safe defaults).
3. Writes a `docker-compose.yml` to the current directory (never committed).
4. Pulls the pre-built image from GitHub Container Registry (`ghcr.io/jakubcwiora/simple-meme-site:containerized`) and starts the stack.

---

## CI/CD Pipeline

There are two separate workflow files:

| File | Purpose |
|---|---|
| [`.github/workflows/main.yml`](.github/workflows/main.yml) | **CI** — runs tests on every push / PR |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | **CD** — builds the Docker image and deploys to the production server |

### Trigger Conditions

| Workflow | Trigger |
|---|---|
| `main.yml` | Push or pull request to `feature/containerized-mysql` |
| `deploy.yml` | Push to `feature/containerized-mysql` |

### CI: Test Job

```
push / pull_request
        │
        ▼
  ┌───────────┐
  │   test    │
  └───────────┘
```

Steps:

1. **Check out** the repository (`actions/checkout@v3`)
2. **Generate random DB credentials** using `openssl rand` and export them to `$GITHUB_ENV`
3. **Set up Python 3.11** and install dependencies from `requirements.txt`
4. **Set up Docker Buildx** (`docker/setup-buildx-action@v2`)
5. **Spin up a temporary MySQL 8.0 container** via a dynamically generated `docker-compose.test.yml`, with a healthcheck
6. **Wait for MySQL** to become ready (polls `mysqladmin ping` with a 120-second timeout)
7. **Initialise the schema** by piping `schema.sql` into the running container with `docker compose exec`
8. **Re-export credentials** as the `DB_*` variables the app reads at runtime
9. **Run the test suite** with `pytest tests/`
10. **Tear down** Docker resources (runs even on failure via `if: always()`)

### CD: Build & Deploy Jobs

```
push to feature/containerized-mysql
        │
        ▼
  ┌───────────┐
  │   build   │  ← builds Docker image, uploads as Actions artifact
  └─────┬─────┘
        │
        ▼
  ┌───────────┐
  │  deploy   │  ← downloads artifact, connects via Tailscale+SSH, deploys
  └───────────┘
```

**Build job** steps:

1. **Check out** the repository
2. **Build the Docker image** tagged with `${{ github.sha }}`
3. **Save the image** to `myapp.tar` and upload it as a workflow artifact

**Deploy job** steps:

1. **Download** the Docker image artifact
2. **Load** the image into the local Docker daemon
3. **Connect to the VPN** via Tailscale (`tailscale/github-action@v3`) using OAuth credentials
4. **Set up SSH** using the `SSH_PRIVATE_KEY` secret and scan the server's host key
5. **Generate `docker-compose.yml` and `.env`** with production credentials from GitHub Secrets
6. **Transfer** `docker-compose.yml`, `.env`, `schema.sql`, and the gzipped image to the server via `scp`
7. **SSH to the server** and run `docker-compose up -d`

### Required Secrets

Configure the following secrets in **Settings → Secrets and variables → Actions**:

| Secret | Used by | Description |
|---|---|---|
| `DB_USER` | `main.yml`, `deploy.yml` | MySQL application user |
| `DB_PASSWORD` | `main.yml`, `deploy.yml` | MySQL application user password |
| `DB_NAME` | `main.yml`, `deploy.yml` | MySQL database name |
| `MYSQL_ROOT_PASSWORD` | `deploy.yml` | MySQL root password |
| `TS_OAUTH_CLIENT_ID` | `deploy.yml` | Tailscale OAuth client ID |
| `TS_OAUTH_SECRET` | `deploy.yml` | Tailscale OAuth secret |
| `SSH_PRIVATE_KEY` | `deploy.yml` | Private SSH key for the production server |
| `SERVER_HOST` | `deploy.yml` | Hostname or Tailscale IP of the production server |
| `SERVER_USERNAME` | `deploy.yml` | SSH username on the production server |

---

## Running Locally

**Prerequisites**: Docker installed and a GitHub account with access to the package registry.

1. Clone the repository:

   ```bash
   git clone https://github.com/jakubcwiora/simple-meme-site.git
   cd simple-meme-site
   ```

2. Run the interactive start script:

   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   The script will:
   - Authenticate with GitHub Container Registry (prompts for a GitHub PAT, or reads the `GITHUB_PAT` env var automatically)
   - Ask for your MySQL credentials (press Enter to accept the safe defaults)
   - Generate a `docker-compose.yml` locally (this file is **not** committed)
   - Pull the pre-built image from GHCR and start the stack

3. Open [http://localhost:5000](http://localhost:5000) in your browser.

> **Tip:** You can skip the interactive prompts by setting `GITHUB_PAT` in your environment before running `start.sh`.
