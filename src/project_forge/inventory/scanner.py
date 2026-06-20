"""Static, side-effect-free architecture scanner."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from .models import ArchitectureInventory, Relationship, Service, Workspace


IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".project-forge",
    "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "coverage", ".next",
}
NON_ARCHITECTURE_DIRS = {"docs", "examples", "fixtures", "templates", "test", "tests"}
SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".java"}
FRAMEWORK_DEPS = {
    "next": "Next.js", "react": "React", "vue": "Vue", "@angular/core": "Angular",
    "express": "Express", "@nestjs/core": "NestJS", "electron": "Electron",
    "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
}
DATABASE_DEPS = {
    "pg": "PostgreSQL", "psycopg": "PostgreSQL", "psycopg2": "PostgreSQL",
    "mysql": "MySQL", "mysql2": "MySQL", "pymysql": "MySQL", "sqlite3": "SQLite",
    "better-sqlite3": "SQLite", "pymongo": "MongoDB", "mongodb": "MongoDB",
    "@prisma/client": "Prisma", "prisma": "Prisma", "sqlalchemy": "SQLAlchemy",
    "redis": "Redis", "ioredis": "Redis", "supabase": "Supabase",
}
QUEUE_DEPS = {
    "celery": "Celery", "bull": "Bull", "bullmq": "BullMQ", "amqplib": "RabbitMQ",
    "pika": "RabbitMQ", "kafkajs": "Kafka", "confluent-kafka": "Kafka",
}
INTEGRATION_DEPS = {
    "openai": "OpenAI", "anthropic": "Anthropic", "stripe": "Stripe",
    "@stripe/stripe-js": "Stripe", "@sentry/node": "Sentry", "sentry-sdk": "Sentry",
    "firebase": "Firebase", "firebase-admin": "Firebase", "@supabase/supabase-js": "Supabase",
    "boto3": "AWS", "@aws-sdk/client-s3": "AWS", "twilio": "Twilio",
    "@sendgrid/mail": "SendGrid", "auth0": "Auth0", "@clerk/nextjs": "Clerk",
    "algoliasearch": "Algolia", "github": "GitHub",
}
ENV_INTEGRATIONS = {
    "OPENAI_": "OpenAI", "ANTHROPIC_": "Anthropic", "STRIPE_": "Stripe",
    "SENTRY_": "Sentry", "FIREBASE_": "Firebase", "SUPABASE_": "Supabase",
    "AWS_": "AWS", "TWILIO_": "Twilio", "SENDGRID_": "SendGrid",
    "AUTH0_": "Auth0", "CLERK_": "Clerk", "ALGOLIA_": "Algolia", "GITHUB_": "GitHub",
}
ENTRYPOINT_CANDIDATES = (
    "src/index.ts", "src/index.js", "src/main.ts", "src/main.js", "index.js",
    "main.py", "app/main.py", "manage.py", "cmd/main.go", "src/main.rs",
    "app/page.tsx", "pages/index.tsx", "manifest.json",
)
ENV_PATTERNS = (
    re.compile(r"(?:process\.env|import\.meta\.env)\.([A-Z][A-Z0-9_]*)"),
    re.compile(r"(?:getenv|os\.getenv|env)\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"os\.environ\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]\s*\]"),
    re.compile(r"\$\{([A-Z][A-Z0-9_]*)"),
    re.compile(r"(?:secrets|vars)\.([A-Z][A-Z0-9_]*)"),
)
PORT_PATTERNS = (
    re.compile(r"\.listen\(\s*(\d{2,5})\b"),
    re.compile(r"\bport\s*[=:]\s*(\d{2,5})\b", re.IGNORECASE),
    re.compile(r"--port(?:=|\s+)(\d{2,5})\b"),
)


def _rel(path: Path, root: Path) -> str:
    value = path.resolve().relative_to(root.resolve()).as_posix()
    return value or "."


def _identifier(path: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_") or "root"
    return "service_" + cleaned


def _read_text(path: Path) -> str:
    """Read bounded non-secret text; real .env files are intentionally opaque."""

    name = path.name.lower()
    if name == ".env" or (name.startswith(".env.") and not name.endswith((".example", ".sample", ".template"))):
        return ""
    try:
        if path.stat().st_size > 1_000_000:
            return ""
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _read_json(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(_read_text(path))
    except (TypeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _walk_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(
            item for item in directories if item not in IGNORED_DIRS | NON_ARCHITECTURE_DIRS
        )
        for name in sorted(names):
            files.append(Path(current) / name)
    return files


def _expand_workspace(root: Path, pattern: str) -> Iterable[Path]:
    clean = pattern.strip().rstrip("/")
    if not clean or clean.startswith("!") or Path(clean).is_absolute() or ".." in Path(clean).parts:
        return []
    return [path for path in root.glob(clean) if path.is_dir()]


def _workspace_paths(root: Path) -> List[Workspace]:
    found: Dict[str, Workspace] = {}
    package = _read_json(root / "package.json")
    raw = package.get("workspaces", [])
    patterns = raw.get("packages", []) if isinstance(raw, dict) else raw
    if isinstance(patterns, list):
        for pattern in patterns:
            if isinstance(pattern, str):
                for path in _expand_workspace(root, pattern):
                    rel = _rel(path, root)
                    found[rel] = Workspace(rel, "package.json")
    for filename in ("pnpm-workspace.yaml", "pnpm-workspace.yml"):
        config = root / filename
        if config.is_file():
            for pattern in re.findall(r"^\s*-\s*['\"]?([^'\"#]+)", _read_text(config), re.MULTILINE):
                for path in _expand_workspace(root, pattern.strip()):
                    rel = _rel(path, root)
                    found[rel] = Workspace(rel, filename)
    lerna = _read_json(root / "lerna.json")
    if isinstance(lerna.get("packages"), list):
        for pattern in lerna["packages"]:
            if isinstance(pattern, str):
                for path in _expand_workspace(root, pattern):
                    rel = _rel(path, root)
                    found[rel] = Workspace(rel, "lerna.json")
    return [found[key] for key in sorted(found)]


def _dependencies(service_root: Path) -> Set[str]:
    names: Set[str] = set()
    package = _read_json(service_root / "package.json")
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(section, {})
        if isinstance(values, dict):
            names.update(str(item).lower() for item in values)
    for filename in ("requirements.txt", "pyproject.toml"):
        text = _read_text(service_root / filename).lower()
        for known in set(FRAMEWORK_DEPS) | set(DATABASE_DEPS) | set(QUEUE_DEPS) | set(INTEGRATION_DEPS):
            if re.search(r"(?<![a-z0-9_.-])" + re.escape(known) + r"(?![a-z0-9_.-])", text):
                names.add(known)
    return names


def _service_files(service_root: Path, all_files: Sequence[Path]) -> List[Path]:
    result = []
    for path in all_files:
        try:
            relative = path.relative_to(service_root)
        except ValueError:
            continue
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if (
            path.suffix.lower() in SOURCE_SUFFIXES
            or path.name.lower().startswith(("dockerfile", "compose"))
            or path.name.lower().endswith((".example", ".sample", ".template"))
        ):
            result.append(path)
    return result[:1000]


def _static_signals(files: Sequence[Path]) -> Tuple[Set[str], Set[int]]:
    environment: Set[str] = set()
    ports: Set[int] = set()
    for path in files:
        text = _read_text(path)
        if path.name.lower().endswith((".example", ".sample", ".template")):
            environment.update(re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=", text, re.MULTILINE))
        for pattern in ENV_PATTERNS:
            environment.update(pattern.findall(text))
        for pattern in PORT_PATTERNS:
            ports.update(int(value) for value in pattern.findall(text) if 0 < int(value) <= 65535)
    return environment, ports


def _entrypoints(service_root: Path, project_root: Path) -> List[str]:
    found: Set[str] = set()
    package = _read_json(service_root / "package.json")
    for key in ("main", "module"):
        value = package.get(key)
        if isinstance(value, str) and (service_root / value).is_file():
            found.add(_rel(service_root / value, project_root))
    binary = package.get("bin")
    values = [binary] if isinstance(binary, str) else list(binary.values()) if isinstance(binary, dict) else []
    for value in values:
        if isinstance(value, str) and (service_root / value).is_file():
            found.add(_rel(service_root / value, project_root))
    for candidate in ENTRYPOINT_CANDIDATES:
        if (service_root / candidate).is_file():
            found.add(_rel(service_root / candidate, project_root))
    return sorted(found)


def _resource_names(dependencies: Set[str], mapping: Mapping[str, str]) -> List[str]:
    return sorted({label for name, label in mapping.items() if name in dependencies})


def _service(root: Path, service_root: Path, all_files: Sequence[Path]) -> Service:
    dependencies = _dependencies(service_root)
    relevant_files = _service_files(service_root, all_files)
    environment, ports = _static_signals(relevant_files)
    package = _read_json(service_root / "package.json")
    frameworks = _resource_names(dependencies, FRAMEWORK_DEPS)
    languages = []
    if (service_root / "package.json").is_file():
        languages.append("TypeScript" if any(path.suffix in {".ts", ".tsx"} for path in relevant_files) else "JavaScript")
    if (service_root / "pyproject.toml").is_file() or (service_root / "requirements.txt").is_file():
        languages.append("Python")
    path = _rel(service_root, root)
    name = package.get("name") if isinstance(package.get("name"), str) else service_root.name
    kind = "web" if set(frameworks) & {"Next.js", "React", "Vue", "Angular"} else "api" if set(frameworks) & {"FastAPI", "Django", "Flask", "Express", "NestJS"} else "application"
    integrations = set(_resource_names(dependencies, INTEGRATION_DEPS))
    for variable in environment:
        integrations.update(label for prefix, label in ENV_INTEGRATIONS.items() if variable.startswith(prefix))
    return Service(
        id=_identifier(path), name=str(name), path=path, kind=kind,
        languages=sorted(languages), frameworks=frameworks,
        entrypoints=_entrypoints(service_root, root), ports=sorted(ports),
        environment_variables=sorted(environment),
        databases=_resource_names(dependencies, DATABASE_DEPS),
        queues=_resource_names(dependencies, QUEUE_DEPS), integrations=sorted(integrations),
    )


def _compose_resources(paths: Sequence[Path]) -> Tuple[Set[str], Set[str], Set[int]]:
    databases: Set[str] = set()
    queues: Set[str] = set()
    ports: Set[int] = set()
    image_signals = {
        "postgres": (databases, "PostgreSQL"), "mysql": (databases, "MySQL"),
        "mongo": (databases, "MongoDB"), "redis": (databases, "Redis"),
        "rabbitmq": (queues, "RabbitMQ"), "kafka": (queues, "Kafka"),
    }
    for path in paths:
        text = _read_text(path)
        lowered = text.lower()
        for token, (target, label) in image_signals.items():
            if re.search(r"\bimage\s*:\s*[^\n#]*" + token, lowered):
                target.add(label)
        for host_port in re.findall(r"['\"]?(\d{2,5}):\d{2,5}(?:/tcp)?['\"]?", text):
            value = int(host_port)
            if 0 < value <= 65535:
                ports.add(value)
    return databases, queues, ports


class InventoryScanner:
    """Discover architecture facts without executing or importing target code."""

    def scan(self, project: Path) -> ArchitectureInventory:
        root = project.resolve()
        if not root.is_dir():
            raise ValueError(f"Project directory does not exist: {project}")
        files = _walk_files(root)
        workspaces = _workspace_paths(root)
        roots = {root / item.path for item in workspaces}
        for path in files:
            if path.name in {"package.json", "pyproject.toml", "requirements.txt"}:
                if workspaces and path.parent == root:
                    continue
                roots.add(path.parent)
        if not roots:
            roots.add(root)
        services = [_service(root, path, files) for path in sorted(roots, key=lambda item: _rel(item, root))]
        docker = sorted(_rel(path, root) for path in files if path.name.lower().startswith("dockerfile"))
        compose = sorted(_rel(path, root) for path in files if re.match(r"(?:docker-)?compose.*\.ya?ml$", path.name, re.I))
        ci = sorted(_rel(path, root) for path in files if ".github/workflows" in path.as_posix() or path.name in {".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml"})
        deploy_names = {"vercel.json", "netlify.toml", "fly.toml", "render.yaml", "render.yml", "railway.json", "Procfile", "app.yaml"}
        deploy = sorted(_rel(path, root) for path in files if path.name in deploy_names or "k8s" in path.parts or "kubernetes" in path.parts)
        compose_paths = [root / path for path in compose]
        compose_databases, compose_queues, compose_ports = _compose_resources(compose_paths)
        if len(services) == 1:
            services[0].ports = sorted(set(services[0].ports) | compose_ports)
        databases = sorted({item for service in services for item in service.databases} | compose_databases)
        queues = sorted({item for service in services for item in service.queues} | compose_queues)
        integrations = sorted({item for service in services for item in service.integrations})
        config_files = [path for path in files if path in compose_paths or ".github/workflows" in path.as_posix()]
        config_environment, _ = _static_signals(config_files)
        environment = sorted({item for service in services for item in service.environment_variables} | config_environment)
        relationships = []
        for service in services:
            relationships.extend(Relationship(service.id, "db_" + item, "uses") for item in service.databases)
            relationships.extend(Relationship(service.id, "queue_" + item, "publishes/consumes") for item in service.queues)
            relationships.extend(Relationship(service.id, "integration_" + item, "integrates") for item in service.integrations)
        warnings = []
        if not any(service.entrypoints for service in services):
            warnings.append("No application entrypoint was detected statically.")
        return ArchitectureInventory(
            project_name=root.name, workspaces=workspaces, monorepo=bool(workspaces),
            services=services, databases=databases, queues=queues, integrations=integrations,
            environment_variables=environment, docker_files=docker, compose_files=compose,
            ci_files=ci, deploy_files=deploy, relationships=relationships, warnings=warnings,
        )


def scan_project(project: Path) -> ArchitectureInventory:
    """Convenience API for a default static scan."""

    return InventoryScanner().scan(project)
