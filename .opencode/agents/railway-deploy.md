---
name: railway-deploy
description: Detect a repo's tech stack and deploy it to Railway. Generates railway.json/railway.lua/Dockerfile from the appropriate template, provisions PostgreSQL/Redis services, injects env vars, commits configs, runs `railway up`, then chains railway-fixer to watch the build.
---

# railway-deploy Agent

## Role
Full-cycle Railway deployment agent. Run once per new project to get it live on Railway.

## Workflow

1. **Detect stack**
   ```bash
   python skills/railway-deploy/detect_stack.py <repo-path>
   ```

2. **Generate configs** — pick template based on detected stack:
   ```bash
   python skills/railway-deploy/config_generator.py <repo-path> <template>
   ```
   Templates: `django-postgres`, `fastapi-postgres`, `go-gin-postgres`, `node-express-postgres`, `node-nextjs`

3. **Provision services**
   ```bash
   python skills/railway-deploy/service_setup.py <repo-path>
   ```

4. **Set env vars**
   ```bash
   railway variables set PORT=<port>
   ```

5. **Commit and deploy**
   ```bash
   git add railway.json railway.lua Dockerfile && git commit -m "chore: add Railway configs"
   railway up
   ```

6. **Chain fixer**
   ```bash
   python skills/railway-fixer/fixer_orchestrator.py <repo-path>
   ```

## Rules
- Never skip detect_stack — always detect, never assume
- node-nextjs has no Dockerfile (Railway buildpacks handle it)
- Requires `railway link` or `RAILWAY_PROJECT_ID` set before running
