"""Safe local plugin lifecycle services for Codex and Claude Code."""

import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

from .models import Host, HostOperation, HostResult, PlannedChange


EXCLUDE_DIRS = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist"}
CACHEBUSTER_RE = re.compile(r"^[0-9A-Za-z.-]+$")


def package_entries(source):
    source = Path(source)
    package = json.loads((source / "package.json").read_text(encoding="utf-8"))
    entries = ["package.json", *package.get("files", [])]
    for required in ("src", "pyproject.toml"):
        if (source / required).exists() and required not in entries:
            entries.append(required)
    safe = []
    for entry in entries:
        relative = Path(entry)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("package entries must be project-relative: %s" % entry)
        if entry not in safe:
            safe.append(entry)
    return safe


def copy_payload(source, target, entries=None):
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for entry in entries or package_entries(source):
        src, dst = source / entry, target / entry
        if not src.exists():
            continue
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDE_DIRS))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def manifest_version(plugin_dir, manifest):
    data = json.loads((Path(plugin_dir) / manifest).read_text(encoding="utf-8"))
    return str(data["version"])


def update_json(path, updater):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    updater(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


class HostService:
    """Manage one host installation without changing the source checkout."""

    def __init__(self, host, source, plugin_dir, marketplace_file, manifest, clock=None):
        self.host = Host(host)
        self.source = Path(source).resolve()
        self.plugin_dir = Path(plugin_dir)
        self.marketplace_file = Path(marketplace_file)
        self.manifest = manifest
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @classmethod
    def codex(cls, source, codex_home, agents_home, clock=None):
        return cls(
            Host.CODEX,
            source,
            Path(codex_home) / "plugins" / "project-forge",
            Path(agents_home) / "plugins" / "marketplace.json",
            ".codex-plugin/plugin.json",
            clock,
        )

    @classmethod
    def claude(cls, source, marketplace_root, clock=None):
        root = Path(marketplace_root)
        return cls(
            Host.CLAUDE,
            source,
            root / "plugins" / "project-forge",
            root / "marketplace.json",
            ".claude-plugin/plugin.json",
            clock,
        )

    def install(self, cachebuster=None, dry_run=False):
        return self._deploy(HostOperation.INSTALL, cachebuster, dry_run, require_existing=False)

    def update(self, cachebuster=None, dry_run=False):
        return self._deploy(HostOperation.UPDATE, cachebuster, dry_run, require_existing=True)

    def verify(self):
        errors = []
        version = None
        manifest_path = self.plugin_dir / self.manifest
        if not manifest_path.is_file():
            errors.append("installed manifest is missing")
        else:
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                version = str(data["version"])
                if data.get("name") != "project-forge":
                    errors.append("installed manifest has the wrong plugin name")
            except (OSError, ValueError, KeyError) as exc:
                errors.append("installed manifest is invalid: %s" % exc)
        if not self._marketplace_contains(version):
            errors.append("marketplace entry is missing or stale")
        return self._result(
            HostOperation.VERIFY,
            "verified" if not errors else "invalid",
            version=version,
            errors=errors,
        )

    def uninstall(self, dry_run=False):
        if not self.plugin_dir.exists() and not self._marketplace_has_name():
            return self._result(HostOperation.UNINSTALL, "not_installed")
        changes = [PlannedChange("remove", str(self.plugin_dir), "installed plugin")]
        changes.append(PlannedChange("update", str(self.marketplace_file), "remove marketplace entry"))
        if dry_run:
            return self._result(HostOperation.UNINSTALL, "planned", dry_run=True, changes=changes)
        backup = self._backup(HostOperation.UNINSTALL)
        if self.plugin_dir.exists():
            shutil.rmtree(self.plugin_dir)
        self._write_marketplace(None)
        return self._result(HostOperation.UNINSTALL, "uninstalled", backup=backup, changes=changes)

    def restore(self, backup_dir, dry_run=False):
        backup = Path(backup_dir)
        metadata = backup / "metadata.json"
        if not metadata.is_file():
            return self._result(HostOperation.RESTORE, "failed", errors=["backup metadata is missing"])
        data = json.loads(metadata.read_text(encoding="utf-8"))
        if data.get("host") != self.host.value:
            return self._result(HostOperation.RESTORE, "failed", errors=["backup belongs to another host"])
        changes = [PlannedChange("restore", str(self.plugin_dir), str(backup))]
        if dry_run:
            return self._result(HostOperation.RESTORE, "planned", dry_run=True, changes=changes)
        plugin_backup = backup / "plugin"
        if self.plugin_dir.exists():
            shutil.rmtree(self.plugin_dir)
        if plugin_backup.exists():
            self.plugin_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(plugin_backup, self.plugin_dir)
        marketplace_backup = backup / "marketplace.json"
        if marketplace_backup.exists():
            self.marketplace_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(marketplace_backup, self.marketplace_file)
        elif self.marketplace_file.exists():
            self.marketplace_file.unlink()
        return self._result(HostOperation.RESTORE, "restored", backup=backup, changes=changes)

    def _deploy(self, operation, cachebuster, dry_run, require_existing):
        if require_existing and not self.plugin_dir.is_dir():
            return self._result(operation, "not_installed", errors=["plugin is not installed"])
        source_manifest = self.source / self.manifest
        if not source_manifest.is_file():
            return self._result(operation, "failed", errors=["source manifest is missing"])
        if cachebuster and not CACHEBUSTER_RE.fullmatch(cachebuster):
            return self._result(operation, "failed", errors=["cachebuster contains unsafe characters"])
        changes = [PlannedChange("replace", str(self.plugin_dir), "plugin payload")]
        changes.append(PlannedChange("update", str(self.marketplace_file), "marketplace entry"))
        if dry_run:
            return self._result(operation, "planned", dry_run=True, changes=changes)
        backup = self._backup(operation) if self.plugin_dir.exists() or self.marketplace_file.exists() else None
        self.plugin_dir.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".project-forge-stage-", dir=str(self.plugin_dir.parent)))
        try:
            copy_payload(self.source, staging)
            version = self._apply_cachebuster(staging, cachebuster)
            if self.plugin_dir.exists():
                shutil.rmtree(self.plugin_dir)
            staging.replace(self.plugin_dir)
            self._write_marketplace(version)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            if backup:
                self.restore(backup)
            raise
        status = "installed" if operation == HostOperation.INSTALL else "updated"
        return self._result(operation, status, version=version, backup=backup, changes=changes)

    def _apply_cachebuster(self, root, cachebuster):
        path = root / self.manifest
        data = json.loads(path.read_text(encoding="utf-8"))
        version = str(data["version"])
        if cachebuster:
            separator = "." if "+" in version else "+"
            version = "%s%s%s.%s" % (version, separator, self.host.value, cachebuster)
            data["version"] = version
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return version

    def _backup(self, operation):
        stamp = self.clock().strftime("%Y%m%dT%H%M%S.%fZ")
        backup = self.plugin_dir.parent / ".project-forge-backups" / (stamp + "-" + operation.value)
        backup.mkdir(parents=True, exist_ok=False)
        if self.plugin_dir.exists():
            shutil.copytree(self.plugin_dir, backup / "plugin")
        if self.marketplace_file.exists():
            shutil.copy2(self.marketplace_file, backup / "marketplace.json")
        metadata = {"host": self.host.value, "operation": operation.value, "plugin_dir": str(self.plugin_dir)}
        (backup / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return backup

    def _marketplace_data(self):
        if not self.marketplace_file.is_file():
            return {}
        try:
            return json.loads(self.marketplace_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _marketplace_has_name(self):
        return any(item.get("name") == "project-forge" for item in self._marketplace_data().get("plugins", []))

    def _marketplace_contains(self, version):
        for item in self._marketplace_data().get("plugins", []):
            if item.get("name") == "project-forge" and item.get("version") == version:
                return True
        return False

    def _write_marketplace(self, version):
        data = self._marketplace_data()
        if self.host == Host.CODEX:
            data.setdefault("name", "personal")
            data.setdefault("interface", {"displayName": "Personal Plugins"})
        else:
            data.setdefault("name", "project-forge-local")
        plugins = [item for item in data.get("plugins", []) if item.get("name") != "project-forge"]
        if version is not None:
            if self.host == Host.CODEX:
                plugins.append({"name": "project-forge", "path": str(self.plugin_dir), "version": version})
            else:
                plugins.append({"name": "project-forge", "source": "./plugins/project-forge", "version": version})
        data["plugins"] = plugins
        self.marketplace_file.parent.mkdir(parents=True, exist_ok=True)
        self.marketplace_file.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _result(self, operation, status, version=None, backup=None, dry_run=False, changes=None, errors=None):
        return HostResult(
            host=self.host,
            operation=operation,
            status=status,
            plugin_dir=self.plugin_dir,
            marketplace_file=self.marketplace_file,
            version=version,
            backup_dir=backup,
            dry_run=dry_run,
            changes=changes or [],
            errors=errors or [],
        )

