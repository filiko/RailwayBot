# Railway Manage Skill Workflow

## Purpose
Post-deployment management operations for Railway projects.

## Commands

### 1. logs

Tail build and deployment logs:

```bash
railway logs
railway logs --build
railway logs --deploy
railway logs --service <service-name>
```

Options:
- `--tail N`: Show last N lines (default: 100)
- `--follow`: Stream logs in real-time
- `--since 1h`: Show logs from the last hour

### 2. env

Manage environment variables:

```bash
# List all environment variables
railway variables

# Set a variable
railway variables set DATABASE_URL=$DATABASE_URL

# Delete a variable
railway variables unset API_KEY

# Get a specific variable
railway variables get DATABASE_URL
```

### 3. rollback

Rollback to a previous deployment:

```bash
# List recent deployments
railway deployments list

# Rollback to specific deployment
railway rollback <deployment-id>

# Rollback to previous deployment
railway rollback
```

### 4. scale

Scale service replicas:

```bash
railway scale up
railway scale down
railway scale --replicas 3
```

### 5. migrate

Run database migrations:

```bash
# Detect and run migrations based on project type
# Python (Django)
python manage.py migrate

# Python (FastAPI/Alembic)
alembic upgrade head

# Node (Prisma)
npx prisma migrate deploy

# Node (Drizzle)
npx drizzle-kit migrate
```

### 6. redeploy

Trigger a manual redeploy:

```bash
railway up
```

## Usage Examples

### Watch logs while debugging
```
railway logs --follow
```

### Add a secret after deployment
```
railway variables set STRIPE_SECRET_KEY=sk_live_...
```

### Rollback a broken deploy
```
railway rollback
```

### Run migrations safely
```
railway run python manage.py migrate
```
