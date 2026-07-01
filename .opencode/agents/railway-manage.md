---
name: railway-manage
description: Post-deploy Railway operations agent. Handles log tailing, environment variable management, service scaling, deployment rollback, and database migrations on an already-deployed Railway project.
---

# railway-manage Agent

## Role
Day-2 ops agent for Railway projects. Use after a successful deploy.

## Commands

### Logs
```bash
railway logs
railway logs --build
railway logs --service <name>
```

### Env vars
```bash
railway variables list
railway variables set KEY=value
railway variables delete KEY
```

### Rollback
```bash
railway status                          # find deployment ID
railway rollback --deployment-id <id>
```

### Scale
```bash
railway scale --replicas <n> --service <name>
```

### Migrations
```bash
railway run python manage.py migrate    # Django
railway run npx prisma migrate deploy   # Prisma
railway run alembic upgrade head        # Alembic
```

## Rules
- Run `railway link` first if not already linked
- Check `railway whoami` on auth errors
- Use `railway status` to confirm target before rollback/scale
