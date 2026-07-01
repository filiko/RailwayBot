# RailwayBot Skills

Three composable skills covering the full Railway deployment lifecycle.

---

## railway-deploy

**Invocation:** `/railway-deploy` | `"deploy my repo to Railway"`

Automates first-time Railway deployment end-to-end.

### What it does
1. Runs `detect_stack.py` to identify runtime, framework, database, cache, port
2. Picks the matching config template (Dockerfile + railway.json + railway.lua)
3. Provisions PostgreSQL/Redis via Railway API
4. Injects required environment variables
5. Commits generated configs and runs `railway up`
6. Spawns `railway-fixer` to monitor the build

### Files
```
railway-deploy/
├── skill.yaml
├── detect_stack.py       # returns JSON: {runtime, framework, database, cache, port, ...}
├── config_generator.py   # copies + customizes template files into repo
├── service_setup.py      # calls railway CLI to add DB/cache services
├── workflow.md
└── templates/
    ├── django-postgres/      Dockerfile  railway.json  railway.lua
    ├── fastapi-postgres/     Dockerfile  railway.json  railway.lua
    ├── go-gin-postgres/      Dockerfile  railway.json  railway.lua
    ├── node-express-postgres/Dockerfile  railway.json  railway.lua
    └── node-nextjs/          railway.json  railway.lua
```

### Quick start
```bash
python skills/railway-deploy/detect_stack.py /path/to/repo
python skills/railway-deploy/config_generator.py /path/to/repo fastapi-postgres
python skills/railway-deploy/service_setup.py /path/to/repo
cd /path/to/repo && railway up
```

---

## railway-fixer

**Invocation:** `/railway-fixer` | `"fix my railway deploy"` | `"railway is failing"`

Autonomous self-healing agent for failing Railway deployments.

### What it does
Runs a continuous loop:
1. Polls `railway status` every 10 seconds
2. On failure: fetches build + deploy logs
3. Matches error patterns → dispatches to specialized fixer module
4. Applies fix, commits (`fix(railway): <description>`), redeploys
5. Exits with `SUCCESS` after 2 consecutive clean builds, or `ESCALATE` after 3 failed attempts per error type

### Fixer modules
| Module | Handles |
|---|---|
| `npm_fixer.py` | npm/yarn/pnpm install failures, missing packages |
| `pip_fixer.py` | pip install, requirements.txt issues |
| `go_fixer.py` | Go module download/build errors |
| `env_fixer.py` | Missing required environment variables |
| `port_fixer.py` | PORT binding, must listen on `0.0.0.0` |
| `prisma_fixer.py` | Prisma schema validation, migrate deploy errors |
| `lock_fixer.py` | Stale/conflicting lock files |
| `build_timeout_fixer.py` | Railway build timeout exceeded |

### Quick start
```bash
python skills/railway-fixer/fixer_orchestrator.py /path/to/repo
# Watch for SUCCESS or ESCALATE
```

---

## railway-manage

**Invocation:** `/railway-manage` | `"railway logs"` | `"rollback railway"` | `"railway scale"`

Day-2 operations for a live Railway project.

### What it does
Wraps common Railway CLI operations with guided steps:
- **Logs** — `railway logs [--build] [--service <name>]`
- **Env vars** — `railway variables set/list/delete`
- **Rollback** — `railway rollback --deployment-id <id>`
- **Scale** — `railway scale --replicas <n>`
- **Migrations** — `railway run <migrate-command>`

### Quick start
```bash
# Tail live logs
railway logs

# Update a secret
railway variables set STRIPE_KEY=sk_live_...

# Rollback
railway status
railway rollback --deployment-id <id>

# Run migrations
railway run npx prisma migrate deploy
```

---

## Skill chain

```
/railway-deploy
    └──[auto-chains]──▶ /railway-fixer
                              └──[on escalation]──▶ human review
                                                         └──[after fix]──▶ /railway-manage
```

---

## Prerequisites

| Requirement | Check |
|---|---|
| Railway CLI | `railway --version` |
| Railway auth | `railway whoami` |
| Project linked | `railway link` in repo dir OR set `RAILWAY_PROJECT_ID` |
| Python 3.8+ | `python --version` |
