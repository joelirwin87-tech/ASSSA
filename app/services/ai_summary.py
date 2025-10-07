"""Generate AI summaries of audit findings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import openai

from app.config import OpenAIConfig


def format_findings(slither_report: Dict[str, Any], mythril_report: Dict[str, Any]) -> str:
    return json.dumps(
        {
            "slither": slither_report,
            "mythril": mythril_report,
        },
        indent=2,
    )


def generate_summary(
    config: OpenAIConfig,
    prompt_template_path: Path,
    slither_report: Dict[str, Any],
    mythril_report: Dict[str, Any],
) -> str:
    prompt_template = prompt_template_path.read_text(encoding="utf-8")
    findings_json = format_findings(slither_report, mythril_report)

    client = openai.OpenAI(api_key=config.api_key)
    response = client.responses.create(
        model=config.model,
        input=[
            {
                "role": "system",
                "content": prompt_template,
            },
            {
                "role": "user",
                "content": findings_json,
            },
        ],
        max_output_tokens=800,
    )

    try:
        return response.output[0].content[0].text.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Unexpected response structure from OpenAI API.") from exc


__all__ = ["generate_summary", "format_findings"]
