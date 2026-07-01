import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional


TEMPLATES_DIR = Path(__file__).parent / "templates"

TEMPLATE_MAP = {
    ("node", "express"): "node-express-postgres",
    ("node", "nestjs"): "node-express-postgres",
    ("node", "fastify"): "node-express-postgres",
    ("node", "nextjs"): "node-nextjs",
    ("python", "fastapi"): "fastapi-postgres",
    ("python", "django"): "django-postgres",
    ("python", "flask"): "fastapi-postgres",
    ("go", "gin"): "go-gin-postgres",
    ("go", "echo"): "go-gin-postgres",
    ("go", "fiber"): "go-gin-postgres",
}

ALWAYS_COPY = ["railway.json", "railway.lua"]


def generate_configs(repo_root: str, stack: dict, force: bool = False) -> dict:
    repo_path = Path(repo_root)
    template_name = _select_template(stack)
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    generated = []
    env_template = _generate_env_example(repo_path, stack)

    for item in template_path.iterdir():
        dest = repo_path / item.name
        if dest.exists() and not force:
            continue

        if item.is_file():
            content = _render_template(item.read_text(), stack)
            dest.write_text(content)
            generated.append(str(dest.relative_to(repo_path)))

    if env_template:
        env_dest = repo_path / ".env.example"
        if not env_dest.exists() or force:
            env_dest.write_text(env_template)
            generated.append(".env.example")

    return {
        "template": template_name,
        "files": generated,
    }


def _select_template(stack: dict) -> str:
    key = (stack["runtime"], stack["framework"])

    for (r, f), tmpl in TEMPLATE_MAP.items():
        if r == stack["runtime"] and (f == stack["framework"] or f is None):
            return tmpl

    generic_map = {
        "node": "node-express-postgres",
        "python": "fastapi-postgres",
        "go": "go-gin-postgres",
    }
    return generic_map.get(stack["runtime"], "node-express-postgres")


def _render_template(content: str, stack: dict) -> str:
    replacements = {
        "{{PORT}}": str(stack.get("port", 3000)),
        "{{START_COMMAND}}": stack.get("start_command", "npm start"),
        "{{BUILD_COMMAND}}": stack.get("build_command", ""),
        "{{FRAMEWORK}}": stack.get("framework", ""),
        "{{RUNTIME}}": stack.get("runtime", ""),
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def _generate_env_example(repo_path: Path, stack: dict) -> Optional[str]:
    lines = ["# Railway Deployment Environment Variables", ""]

    if "postgresql" in stack.get("database", []):
        lines.append("DATABASE_URL=${{postgres.DATABASE_URL}}")

    if "redis" in stack.get("cache", []):
        lines.append("REDIS_URL=${{redis.REDIS_URL}}")

    if stack["runtime"] == "node":
        lines.append("NODE_ENV=production")
        lines.append("PORT={{PORT}}")
    elif stack["runtime"] == "python":
        lines.append("PYTHONUNBUFFERED=1")
        lines.append("PORT={{PORT}}")
    elif stack["runtime"] == "go":
        lines.append("PORT={{PORT}}")

    lines.append("")
    lines.append("# Add your secrets below:")
    lines.append("# API_KEY=your-key-here")

    return "\n".join(lines)


if __name__ == "__main__":
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    import subprocess
    result = subprocess.run(
        ["python", str(Path(__file__).parent / "detect_stack.py"), repo_root],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    stack = json.loads(result.stdout)
    generated = generate_configs(repo_root, stack)
    print(json.dumps(generated, indent=2))
