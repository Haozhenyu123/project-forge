"""Loop storage layer: file I/O for inbox, processed, runs, and state.json."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import LoopEpisode, LoopIteration, LoopSignal, LoopStatus, LoopPolicy


def loop_dir(project_dir: Path) -> Path:
    return project_dir / ".project-forge" / "loop"


def ensure_dirs(project_dir: Path) -> Dict[str, Path]:
    """Ensure all loop storage directories exist and return their paths."""
    base = loop_dir(project_dir)
    dirs = {
        "base": base,
        "inbox": base / "inbox",
        "processed": base / "processed",
        "runs": base / "runs",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def atomic_write(path: Path, text: str) -> None:
    """Write to a temp file, then atomically replace the target."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def backup_file(path: Path) -> Optional[Path]:
    """Create a timestamped backup of a file before modification. Returns backup path."""
    if not path.is_file():
        return None
    backup = path.with_suffix(path.suffix + f".bak-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}")
    shutil.copy2(str(path), str(backup))
    return backup


def save_state(project_dir: Path, episode: LoopEpisode) -> None:
    """Atomically save the current loop state."""
    dirs = ensure_dirs(project_dir)
    state_path = dirs["base"] / "state.json"
    backup_file(state_path)
    episode.updated_at = datetime.utcnow().isoformat()
    atomic_write(state_path, json.dumps(episode.to_dict(), indent=2, sort_keys=True) + "\n")


def load_state(project_dir: Path) -> Optional[LoopEpisode]:
    """Load the current loop state, or None if absent."""
    state_path = loop_dir(project_dir) / "state.json"
    if not state_path.is_file():
        return None
    data = json.loads(state_path.read_text(encoding="utf-8"))
    return LoopEpisode.from_dict(data)


def ingest_signal_to_inbox(project_dir: Path, signal: LoopSignal) -> Path:
    """Write a signal to the inbox and return its path."""
    dirs = ensure_dirs(project_dir)
    path = dirs["inbox"] / f"{signal.fingerprint}.json"
    atomic_write(path, json.dumps(signal.to_dict(), indent=2, sort_keys=True) + "\n")
    return path


def move_to_processed(project_dir: Path, signal: LoopSignal) -> Path:
    """Move a signal from inbox to processed and return the new path."""
    dirs = ensure_dirs(project_dir)
    inbox_path = dirs["inbox"] / f"{signal.fingerprint}.json"
    processed_path = dirs["processed"] / f"{signal.fingerprint}.json"
    if inbox_path.is_file():
        shutil.move(str(inbox_path), str(processed_path))
    return processed_path


def list_inbox(project_dir: Path) -> List[LoopSignal]:
    """List all unprocessed signals in the inbox."""
    dirs = ensure_dirs(project_dir)
    signals = []
    for p in sorted(dirs["inbox"].glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            signals.append(LoopSignal.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            pass
    return signals


def save_iteration(
    project_dir: Path, episode_id: str, iteration: LoopIteration
) -> Path:
    """Save an iteration record to runs/<episode-id>/<iteration-id>.json."""
    dirs = ensure_dirs(project_dir)
    ep_dir = dirs["runs"] / episode_id
    ep_dir.mkdir(parents=True, exist_ok=True)
    path = ep_dir / f"{iteration.iteration_id}.json"
    atomic_write(
        path,
        json.dumps(iteration.to_dict(), indent=2, sort_keys=True) + "\n",
    )
    return path


def load_iterations(project_dir: Path, episode_id: str) -> List[LoopIteration]:
    """Load all iteration records for an episode."""
    dirs = ensure_dirs(project_dir)
    ep_dir = dirs["runs"] / episode_id
    if not ep_dir.is_dir():
        return []
    iterations = []
    for p in sorted(ep_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            iterations.append(LoopIteration.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            pass
    return iterations


def rollback_state(project_dir: Path, backup_path: Path) -> None:
    """Restore state from a backup file."""
    state_path = loop_dir(project_dir) / "state.json"
    if backup_path.is_file():
        shutil.copy2(str(backup_path), str(state_path))
