# Simple Meme Site

A Flask web application that scrapes and displays memes from [demotywatory.pl](https://demotywatory.pl). Users can add new random memes to their personal gallery or remove existing ones. The main focus of this project is the **CI/CD pipeline** built with GitHub Actions.

---

## Table of Contents

- [Application Overview](#application-overview)
- [Tech Stack](#tech-stack)
- [CI/CD Pipeline](#cicd-pipeline)
  - [Trigger Conditions](#trigger-conditions)
  - [Test Job](#test-job)
  - [Build & Push Job](#build--push-job)
  - [Required Secrets](#required-secrets)
- [Running Locally](#running-locally)

---

## Application Overview

| Feature | Description |
|---|---|
| **Meme Gallery** | Displays all stored memes in a responsive card grid |
| **Add Meme** | Scrapes a random meme from `demotywatory.pl/losuj` and saves it to the database |
| **Delete Meme** | Removes a meme from the gallery and the database |

---

## Tech Stack

- **Backend**: Python / Flask
- **Database**: MySQL 8.0
- **Scraping**: BeautifulSoup4 + Requests
- **Containerization**: Docker / Docker Compose
- **CI/CD**: GitHub Actions

---

## CI/CD Pipeline

The pipeline is defined in [`.github/workflows/main.yml`](.github/workflows/main.yml) and consists of two sequential jobs:

```
push / pull_request
        │
        ▼
  ┌───────────┐
  │   test    │  ← always runs
  └─────┬─────┘
        │ success + push to main/develop
        ▼
  ┌───────────┐
  │   build   │  ← builds & pushes Docker image
  └───────────┘
```

### Trigger Conditions

The pipeline runs on:

- **Push** to `main` or `develop` branches
- **Pull request** targeting `main` or `develop` branches

### Test Job

Runs on every push and pull request. Steps:

1. **Check out** the repository (`actions/checkout@v3`)
2. **Set up Python 3.11** (`actions/setup-python@v4`) and install dependencies from `requirements.txt`
3. **Set up Docker Buildx** (`docker/setup-buildx-action@v2`)
4. **Spin up a temporary MySQL 8.0 container** using an inline `docker-compose.test.yml` generated at runtime, with health-check polling
5. **Wait for the database** to become ready (up to 60 seconds, pinging with `mysqladmin`)
6. **Initialise the schema** by piping `schema.sql` into the running container
7. **Run the test suite** with `pytest tests/`
8. **Tear down** the Docker resources (runs even on failure via `if: always()`)

### Build & Push Job

Only runs when the `test` job passes **and** the event is a push to `main` or `develop`. Steps:

1. **Check out** the repository
2. **Set up Docker Buildx** (`docker/setup-buildx-action@v2`)
3. **Log in to DockerHub** (`docker/login-action@v2`) using repository secrets
4. **Build and push** the Docker image (`docker/build-push-action@v4`) to:

   ```
   jakubcwiora/simple-meme-site:latest
   ```

   Database connection parameters are passed as build arguments so the image is environment-aware.

### Required Secrets

Configure the following secrets in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `DB_USER` | MySQL application user |
| `DB_PASSWORD` | MySQL application user password |
| `DB_NAME` | MySQL database name |
| `MYSQL_ROOT_PASSWORD` | MySQL root password (used by the health-check in tests) |
| `DOCKER_USERNAME` | DockerHub username |
| `DOCKER_PASSWORD` | DockerHub access token or password |

---

## Running Locally

**Prerequisites**: Docker and Docker Compose installed.

1. Clone the repository and copy the example environment variables:

   ```bash
   git clone https://github.com/jakubcwiora/simple-meme-site.git
   cd simple-meme-site
   ```

2. Edit `docker-compose.yml` and set your preferred database credentials.

3. Start the stack:

   ```bash
   docker compose up --build
   ```

4. Open [http://localhost:5000](http://localhost:5000) in your browser.
