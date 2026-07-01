# Railway Deploy Skill Workflow

## Purpose
Deploy any web application repository to Railway with appropriate service configuration (PostgreSQL, Redis, backend, frontend).

## Prerequisites
- Railway CLI installed (`npm i -g @railway/cli`)
- Git repository with code to deploy
- Railway account authenticated (`railway login`)

## Phase 1: Detect Stack

Run `detect_stack.py` in the repository root to determine:
- **Runtime**: node, python, go
- **Web framework**: express, fastify, nextjs, fastapi, django, flask, gin
- **Database**: postgresql, mysql, mongodb (based on ORM/ driver deps)
- **Cache**: redis, memcached
- **Workers**: background-jobs, cron

### Detection Files
| File | Detects |
|---|---|
| `package.json` | Node.js runtime, npm deps |
| `requirements.txt` | Python runtime, pip deps |
| `go.mod` | Go runtime, go deps |
| `Dockerfile` | Custom container builds |
| `next.config.js` | Next.js frontend |
| `prisma/schema.prisma` | Prisma ORM (PostgreSQL) |
| `drizzle.config.ts` | Drizzle ORM (PostgreSQL) |
| `manage.py` | Django |
| `alembic.ini` | Python migrations (PostgreSQL) |
| `redis`, `ioredis` in deps | Redis cache |
| `bull`, `bullmq`, `rq` in deps | Background workers |

### Output Schema
```json
{
  "runtime": "node|python|go",
  "framework": "express|fastapi|nextjs|gin|django|flask",
  "database": ["postgresql"],
  "cache": ["redis"],
  "workers": ["bullmq"],
  "port": 3000,
  "start_command": "npm start",
  "build_command": "npm run build"
}
```

## Phase 2: Select Template

Based on detected stack, select the appropriate template from `templates/`:

| Detected | Template |
|---|---|
| node + express + postgres | `node-express-postgres/` |
| node + nextjs | `node-nextjs/` |
| python + fastapi + postgres | `fastapi-postgres/` |
| python + django + postgres | `django-postgres/` |
| go + gin + postgres | `go-gin-postgres/` |

If no exact match, use the closest parent template (e.g., `node-express-postgres` for `node + express + postgres + redis`).

## Phase 3: Generate Configs

Copy template files to repository, modifying:

1. **`railway.json`** — Railway project configuration
   - Set `service.name` to detected app name
   - Configure healthcheck endpoint
   - Set build command
   - Set start command

2. **`railway.lua`** — Advanced Railway configuration
   - Nixpak build settings
   - Environment variables
   - Service dependencies (postgres → app)
   - Port mapping

3. **`Dockerfile`** (if template has one) — Custom container
   - Set correct base image
   - Expose correct port
   - Set correct start command

4. **`.env.example`** — Template for required env vars
   - List all required secrets (masked)
   - Document optional vars with defaults

## Phase 4: Create Railway Services

Run Railway CLI commands to provision services:

```bash
# Create PostgreSQL database
railway add --database postgresql

# Create Redis cache (if detected)
railway add --cache redis

# Link to Railway project (if not linked)
railway link
```

## Phase 5: Inject Environment Variables

Automatically set known environment variables:

| Variable | Source |
|---|---|
| `DATABASE_URL` | From Railway PostgreSQL addon |
| `REDIS_URL` | From Railway Redis addon |
| `PORT` | Detected from framework |
| `NODE_ENV` | `production` |
| `PYTHONUNBUFFERED` | `1` |
| `WEB_PORT` | Port the app listens on |

For unknown required env vars (API keys, tokens), prompt the user.

## Phase 6: Commit and Deploy

```bash
git add railway.json railway.lua Dockerfile .env.example
git commit -m "chore: add railway deployment configs"
railway up
```

## Phase 7: Chain to railway-fixer

After `railway up` succeeds, spawn the `railway-fixer` sub-agent to monitor the deployment:

```
Spawn: railway-fixer --watch --deployment-id=<current-deployment-id>
```

The fixer runs independently and will:
1. Poll deployment status
2. Auto-fix build errors
3. Commit fixes and trigger redeploy
4. Notify on success or escalate on failure

## Error Handling

| Situation | Action |
|---|---|
| Railway CLI not found | Install it: `npm i -g @railway/cli` |
| Not a git repo | Initialize: `git init` first |
| Not linked to Railway | Prompt user to run `railway link` |
| Detected stack unsupported | Ask user to specify manually |
| User missing required secrets | Prompt for each secret |

## Exit Conditions

- **SUCCESS**: Fixer reports 2 consecutive successful deploys
- **FAILURE**: Fixer reports 3 failed fix attempts → escalate to user
- **USER_ABORT**: User interrupts the process
