"""Send audit reports to clients via SMTP."""
from __future__ import annotations

import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.config import EmailConfig


def send_report(
    config: EmailConfig,
    recipient_email: str,
    summary_text: str,
    pdf_path: Path,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Your Affordable Smart Contract Audit Report"
    msg["From"] = f"{config.sender_name} <{config.sender_email}>"
    msg["To"] = recipient_email
    msg.set_content(
        """Hello,\n\nThank you for using Affordable Smart Contract Audits. Your report is attached.\n\nSummary:\n{summary}\n\nRegards,\nAffordable Smart Contract Audits""".format(
            summary=summary_text
        )
    )

    mime_type, _ = mimetypes.guess_type(pdf_path.name)
    maintype, subtype = (mime_type or "application/pdf").split("/")
    msg.add_attachment(
        pdf_path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=pdf_path.name,
    )

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
        if config.use_tls:
            smtp.starttls()
        if config.username and config.password:
            smtp.login(config.username, config.password)
        smtp.send_message(msg)


__all__ = ["send_report"]
