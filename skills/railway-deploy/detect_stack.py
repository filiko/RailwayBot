import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


def detect_stack(repo_root: str) -> dict:
    repo_path = Path(repo_root)
    stack = {
        "runtime": None,
        "framework": None,
        "database": [],
        "cache": [],
        "workers": [],
        "port": None,
        "start_command": None,
        "build_command": None,
    }

    if (repo_path / "package.json").exists():
        stack["runtime"] = "node"
        _detect_node_stack(repo_path, stack)
    elif (repo_path / "requirements.txt").exists():
        stack["runtime"] = "python"
        _detect_python_stack(repo_path, stack)
    elif (repo_path / "go.mod").exists():
        stack["runtime"] = "go"
        _detect_go_stack(repo_path, stack)

    if stack["runtime"] is None:
        raise ValueError("Could not detect tech stack. No package.json, requirements.txt, or go.mod found.")

    _infer_defaults(stack)

    return stack


def _detect_node_stack(repo_path: Path, stack: dict) -> None:
    pkg = json.loads((repo_path / "package.json").read_text())
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

    if "next" in deps:
        stack["framework"] = "nextjs"
        stack["build_command"] = "npm run build"
        stack["start_command"] = "npm start"
        stack["port"] = 3000
    elif "@nestjs/core" in deps:
        stack["framework"] = "nestjs"
        stack["build_command"] = "npm run build"
        stack["start_command"] = "node dist/main.js"
        stack["port"] = 3000
    elif "express" in deps:
        stack["framework"] = "express"
        stack["build_command"] = None
        stack["start_command"] = "npm start"
        stack["port"] = int(os.getenv("PORT", "3000"))
    elif "fastify" in deps:
        stack["framework"] = "fastify"
        stack["build_command"] = None
        stack["start_command"] = "npm start"
        stack["port"] = int(os.getenv("PORT", "3000"))

    _detect_node_services(deps, stack)

    if (repo_path / "prisma" / "schema.prisma").exists():
        stack["database"].append("postgresql")
    elif (repo_path / "drizzle.config.ts").exists() or (repo_path / "drizzle.config.js").exists():
        stack["database"].append("postgresql")


def _detect_node_services(deps: dict, stack: dict) -> None:
    redis_deps = {"redis", "ioredis", "redis-om"}
    worker_deps = {"bull", "bullmq", "rq", "agenda"}

    for dep in deps:
        if dep in redis_deps:
            stack["cache"].append("redis")
        if dep in worker_deps:
            if dep in ("bull", "bullmq"):
                stack["workers"].append("bullmq")
            elif dep == "rq":
                stack["workers"].append("rq")


def _detect_python_stack(repo_path: Path, stack: dict) -> None:
    req = (repo_path / "requirements.txt").read_text().lower()

    if "fastapi" in req:
        stack["framework"] = "fastapi"
        stack["start_command"] = "uvicorn main:app --host 0.0.0.0 --port $PORT"
        stack["port"] = 8000
    elif "django" in req:
        stack["framework"] = "django"
        stack["build_command"] = "python manage.py migrate && python manage.py collectstatic --noinput"
        stack["start_command"] = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
        stack["port"] = 8000
    elif "flask" in req:
        stack["framework"] = "flask"
        stack["start_command"] = "flask run --host 0.0.0.0 --port $PORT"
        stack["port"] = 5000
    else:
        stack["framework"] = "python"
        stack["start_command"] = "python main.py"
        stack["port"] = 8000

    _detect_python_services(req, stack)

    if (repo_path / "prisma" / "schema.prisma").exists():
        stack["database"].append("postgresql")

    if (repo_path / "alembic.ini").exists() or (repo_path / "alembic").is_dir():
        stack["database"].append("postgresql")


def _detect_python_services(req: str, stack: dict) -> None:
    if "psycopg2" in req or "asyncpg" in req or "sqlalchemy" in req:
        stack["database"].append("postgresql")
    if "redis" in req or "aioredis" in req:
        stack["cache"].append("redis")
    if "rq" in req or "celery" in req:
        stack["workers"].append("celery")
    if "huey" in req:
        stack["workers"].append("huey")


def _detect_go_stack(repo_path: Path, stack: dict) -> None:
    go_mod = (repo_path / "go.mod").read_text()

    if "gin-gonic" in go_mod or '"github.com/gin-gonic/gin"' in go_mod:
        stack["framework"] = "gin"
    elif "echo-framework" in go_mod or '"github.com/labstack/echo"' in go_mod:
        stack["framework"] = "echo"
    elif "fiber" in go_mod or '"github.com/gofiber/fiber"' in go_mod:
        stack["framework"] = "fiber"
    else:
        stack["framework"] = "go"

    stack["start_command"] = "go run ."
    stack["port"] = 8080

    if "postgres" in go_mod or "pq" in go_mod:
        stack["database"].append("postgresql")
    if "redis" in go_mod or "go-redis" in go_mod:
        stack["cache"].append("redis")


def _infer_defaults(stack: dict) -> None:
    if stack["port"] is None:
        stack["port"] = 3000
    if stack["start_command"] is None:
        if stack["runtime"] == "node":
            stack["start_command"] = "npm start"
        elif stack["runtime"] == "python":
            stack["start_command"] = "python main.py"
        elif stack["runtime"] == "go":
            stack["start_command"] = "go run ."


def format_stack_report(stack: dict) -> str:
    lines = [
        f"Runtime: {stack['runtime']}",
        f"Framework: {stack['framework']}",
        f"Database: {', '.join(stack['database']) or 'none'}",
        f"Cache: {', '.join(stack['cache']) or 'none'}",
        f"Workers: {', '.join(stack['workers']) or 'none'}",
        f"Port: {stack['port']}",
        f"Start: {stack['start_command']}",
    ]
    if stack["build_command"]:
        lines.append(f"Build: {stack['build_command']}")
    return "\n".join(lines)


if __name__ == "__main__":
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    try:
        stack = detect_stack(repo_root)
        print(json.dumps(stack, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
