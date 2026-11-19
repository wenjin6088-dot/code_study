import os
import uuid
from pathlib import Path


def _upload_root() -> Path:
    return Path(os.environ.get("UPLOAD_DIR", "storage/uploads"))


def _safe_basename(relative_name: str) -> str:
    """Strip any directory components, keeping only the file's own name."""
    return Path(relative_name.replace("\\", "/")).name


def save_file(
    user_id: uuid.UUID | str,
    task_id: uuid.UUID | str,
    relative_name: str,
    content: bytes,
) -> str:
    """Persist ``content`` under ``{UPLOAD_DIR}/{user_id}/{task_id}/`` and
    return the storage path it was written to.

    The stored filename is prefixed with a random UUID so that two files
    sharing the same basename (e.g. two ``main.py`` from different folders)
    never collide.
    """
    basename = _safe_basename(relative_name)
    directory = _upload_root() / str(user_id) / str(task_id)
    directory.mkdir(parents=True, exist_ok=True)

    storage_path = directory / f"{uuid.uuid4()}_{basename}"
    storage_path.write_bytes(content)
    return str(storage_path)


def read_file(storage_path: str) -> bytes:
    """Read back the raw bytes previously written by :func:`save_file`."""
    return Path(storage_path).read_bytes()
