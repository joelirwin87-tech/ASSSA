"""Utility to invoke Mythril symbolic execution."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


class MythrilNotInstalledError(RuntimeError):
    """Raised when Mythril is not available in the runtime environment."""


def run_mythril(contract_path: Path) -> dict:
    try:
        result = subprocess.run(
            [
                "myth", "analyze", str(contract_path), "--execution-timeout", "90", "--json"
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:  # pragma: no cover
        raise MythrilNotInstalledError("Mythril is not installed in the container.") from exc

    if result.returncode not in {0, 1}:  # Mythril returns 1 when vulnerabilities found
        raise RuntimeError(
            f"Mythril scan failed (code {result.returncode}): {result.stderr.strip()}"
        )

    output = result.stdout.strip() or "{}"
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Failed to parse Mythril output as JSON.") from exc


__all__ = ["run_mythril", "MythrilNotInstalledError"]
