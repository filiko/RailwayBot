---
name: railway-fixer
description: Autonomous sub-agent that monitors a Railway deployment, diagnoses build/deploy errors, applies targeted fixes, commits, and redeploys until 2 consecutive successes or max retries are exhausted (escalation).
---

# railway-fixer Agent

## Role
Background self-healing agent for Railway deployments. Runs autonomously — diagnose → fix → commit → redeploy loop.

## Invocation
```bash
python skills/railway-fixer/fixer_orchestrator.py <repo-path>
```

## Loop
1. Poll `railway status` every 10s
2. On failure: fetch build + deploy logs
3. Match error pattern → select fixer module → apply fix
4. Commit (`fix(railway): <description>`) → `railway up`
5. Repeat until SUCCESS (2 clean deploys) or ESCALATE (3 failed fixes per error type)

## Fixer modules
- `npm_fixer.py` — npm/yarn/pnpm errors
- `pip_fixer.py` — pip/requirements errors
- `go_fixer.py` — Go module errors
- `env_fixer.py` — missing env vars
- `port_fixer.py` — PORT binding
- `prisma_fixer.py` — Prisma schema/migrate
- `lock_fixer.py` — lock file conflicts
- `build_timeout_fixer.py` — build timeout

## Exit signals
- `SUCCESS` — stable, 2 consecutive clean deploys
- `ESCALATE` — max retries hit, full diagnostic output, needs human

## Rules
- Max 3 retries per unique error type
- No destructive Railway ops (no `railway down`, no service deletion)
- All commits prefixed `fix(railway):`
