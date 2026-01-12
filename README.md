# MCP Server for Copilot — Python

This repository contains a small MCP (Model Context Protocol) server and client examples focused on BMI calculation and SQL Server connectivity. The project is configured to avoid committing secrets: runtime secrets must be provided via environment variables or a secrets manager (Azure Key Vault, CI secrets, etc.).

Quick start
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set your secrets locally (or set env vars directly):

```bash
cp .env.example .env
# edit .env to add your real values (do NOT commit .env)
```

3. Run local Docker SQL server (optional) for tests:

```bash
export SA_PASSWORD="your_local_sa_password_here"
docker-compose up -d
python test_docker_sql.py
```

Environment variables used
- `OPENAI_API_KEY` — OpenAI API key used by LLM clients
- `SA_PASSWORD` — SQL Server `sa` password for local Docker testing
- `SQL_PASSWORD` — SQL user password for `SqlPassword` configs
- `SQL_AUTH_TYPE` — Authentication type used (e.g. `ActiveDirectoryMsi`, `SqlPassword`)

Security
- Do NOT commit secrets to source control. Use `.env` locally and add it to `.gitignore`.
- In production (Azure), use Azure Key Vault or Function App settings rather than storing secrets in code.

Where to look next
- `bmi_server.py` — Main MCP server with BMI and SQL tools
- `shared_code/mcp_server.py` — Shared server utilities and connection helpers
- `sql_config.py` — Example SQL configurations (now reads `SQL_PASSWORD` from env)
- `docker-compose.yml` — Local Docker SQL Server setup (uses `${SA_PASSWORD}`)

If you'd like, I can also add an automated test that validates required env vars are set before runtime.

Developer Onboarding
---------------------

Quick setup commands to get started as a developer. A `Makefile` is provided to simplify common tasks.

Install local git hooks (recommended):

```bash
# Install the local pre-commit hook that scans staged files for secrets
make install-hooks
```

Create local environment file and install dependencies:

```bash
make env-setup
make deps
```

Start local Docker SQL server and run tests:

```bash
make start-docker
make test-docker
```

Notes:
- The `install-hooks` command runs `./scripts/install-hooks.sh` which writes a pre-commit hook to `.git/hooks/pre-commit`.
- Hooks in `.git/hooks` are local; running `make install-hooks` on each developer machine is recommended.
- For CI and shared enforcement, consider adding `pre-commit` framework config or a server-side secret scanning policy.
