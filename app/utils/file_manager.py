"""File system utilities for audit workspaces."""
from __future__ import annotations

import secrets
import shutil
from pathlib import Path
from typing import BinaryIO


class FileValidationError(ValueError):
    """Raised when an uploaded file fails validation."""


def _generate_workspace_name() -> str:
    return secrets.token_urlsafe(12)


def create_workspace(root: str) -> Path:
    workspace_dir = Path(root) / _generate_workspace_name()
    workspace_dir.mkdir(parents=True, exist_ok=False)
    return workspace_dir


def validate_contract_filename(filename: str) -> None:
    if not filename or not filename.lower().endswith(".sol"):
        raise FileValidationError("Only Solidity (.sol) files are supported.")


def persist_contract(uploaded_file: BinaryIO, destination: Path) -> Path:
    destination_path = destination / "contract.sol"
    with open(destination_path, "wb") as target:
        shutil.copyfileobj(uploaded_file, target)
    return destination_path


def secure_delete(path: Path) -> None:
    if path.is_file():
        path.write_bytes(b"")
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


__all__ = [
    "create_workspace",
    "validate_contract_filename",
    "persist_contract",
    "secure_delete",
    "FileValidationError",
]
