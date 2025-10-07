"""High-level orchestration for automated smart contract audits."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from app.config import AppConfig
from app.services.ai_summary import generate_summary
from app.services.mythril_scan import run_mythril
from app.services.pdf_report import build_pdf
from app.services.slither_scan import run_slither


def execute_audit(
    config: AppConfig,
    contract_path: Path,
    prompt_template: Path,
    output_pdf_path: Path,
) -> Tuple[Dict[str, Any], Dict[str, Any], str, Path]:
    slither_report = run_slither(contract_path)
    mythril_report = run_mythril(contract_path)

    summary_markdown = generate_summary(
        config.openai,
        prompt_template,
        slither_report,
        mythril_report,
    )

    raw_findings = [
        ("Slither JSON", json.dumps(slither_report, indent=2)),
        ("Mythril JSON", json.dumps(mythril_report, indent=2)),
    ]

    pdf_path = build_pdf(
        output_pdf_path,
        brand_name=config.brand_name,
        brand_color=config.brand_color,
        summary_markdown=summary_markdown,
        raw_findings=raw_findings,
        footer_text=config.report_footer,
    )

    summary_text = summary_markdown.replace("\n", " ")
    return slither_report, mythril_report, summary_text, pdf_path


def prepare_pdf_path(workspace: Path) -> Path:
    pdf_path = workspace / "audit-report.pdf"
    if pdf_path.exists():
        pdf_path.unlink()
    return pdf_path


__all__ = ["execute_audit", "prepare_pdf_path"]
