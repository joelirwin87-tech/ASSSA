"""Utility to invoke Slither static analysis."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


class SlitherNotInstalledError(RuntimeError):
    """Raised when Slither is not available in the runtime environment."""


def run_slither(contract_path: Path) -> dict:
    """Run Slither and return the parsed JSON report.

    Parameters
    ----------
    contract_path: Path
        Absolute path to the Solidity contract.
    """
    try:
        result = subprocess.run(
            [
                "slither",
                str(contract_path),
                "--json",
                "-",
                "--detect",
                "arbitrary-send,tx-origin,controlled-delegatecall,unchecked-transfer",
            ],
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - depends on environment
        raise SlitherNotInstalledError("Slither is not installed in the container.") from exc

    if result.returncode not in {0, 255}:  # 255 indicates informational/warnings in Slither
        raise RuntimeError(
            f"Slither scan failed (code {result.returncode}): {result.stderr.strip()}"
        )

    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Failed to parse Slither output as JSON.") from exc


__all__ = ["run_slither", "SlitherNotInstalledError"]
