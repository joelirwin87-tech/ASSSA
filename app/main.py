from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st

from app.config import ConfigError, load_config
from app.services.audit_runner import execute_audit, prepare_pdf_path
from app.services.email_service import send_report
from app.services.payments import (
    PaymentError,
    create_checkout_session,
    init_stripe,
    verify_payment,
)
from app.utils.file_manager import (
    FileValidationError,
    create_workspace,
    persist_contract,
    secure_delete,
    validate_contract_filename,
)

PROMPT_TEMPLATE = Path(__file__).resolve().parent / "prompts" / "executive_summary_prompt.md"


@st.cache_resource(show_spinner=False)
def get_config():
    try:
        return load_config()
    except ConfigError as exc:
        st.error(f"Configuration error: {exc}")
        st.stop()


def _initialize_stripe():
    config = get_config()
    init_stripe(config.stripe)
    return config


def _render_sidebar(config_email: str | None) -> None:
    st.sidebar.header("Need help?")
    st.sidebar.write(
        "Reach out at **{email}** for enterprise support, rush audits, or integration help.".format(
            email=config_email or "support@example.com"
        )
    )
    st.sidebar.markdown("""
**Security Promise**
- Files are processed in isolated workspaces.
- Reports are emailed and all artifacts securely deleted after completion.
- We never store your contracts server-side after your audit finishes.
""")


def _display_checkout_button(email: str) -> None:
    st.success("Payment verified. You can now run the audit.")
    st.session_state["payment_verified"] = True
    st.session_state["customer_email"] = email


def _redirect_to_checkout(customer_email: str) -> None:
    config = get_config()
    try:
        checkout_url = create_checkout_session(
            config.stripe,
            customer_email=customer_email,
            success_params={"session_id": "{CHECKOUT_SESSION_ID}"},
        )
    except PaymentError as exc:
        st.error(str(exc))
        return
    st.session_state["checkout_url"] = checkout_url
    st.toast("Checkout session ready. Click the button below to pay.")



def _process_success_flow() -> Optional[str]:
    params = st.experimental_get_query_params()
    session_id = params.get("session_id", [None])[0]
    if not session_id:
        return None
    try:
        if verify_payment(session_id):
            st.experimental_set_query_params()  # clear params
            st.session_state["payment_verified"] = True
            return st.session_state.get("customer_email")
    except PaymentError as exc:
        st.warning(str(exc))
    return None


def _audit_form():
    config = _initialize_stripe()
    _render_sidebar(config.email.sender_email)

    st.title("Affordable Smart Contract Audits")
    st.caption("Automated first-line security analysis for Solidity projects.")

    email = st.text_input(
        "Business email",
        placeholder="you@company.com",
        value=st.session_state.get("customer_email", ""),
    )
    uploaded_contract = st.file_uploader(
        "Upload Solidity contract", type=["sol"], accept_multiple_files=False
    )

    verified_email = _process_success_flow()
    if verified_email:
        if not email:
            st.session_state["customer_email"] = verified_email
        _display_checkout_button(verified_email)

    if not st.session_state.get("payment_verified"):
        if st.button("Start Secure Checkout", type="primary", disabled=not (uploaded_contract and email)):
            if not email:
                st.error("Email is required for checkout.")
                return
            if not uploaded_contract:
                st.error("Please upload a Solidity contract before proceeding.")
                return
            st.session_state["customer_email"] = email
            _redirect_to_checkout(email)
        checkout_url = st.session_state.get("checkout_url")
        if checkout_url:
            st.link_button("Pay $99 to Run Audit", checkout_url, use_container_width=True)
        return

    if st.button("Run Audit", type="primary", use_container_width=True):
        if not uploaded_contract:
            st.error("Upload a Solidity contract to continue.")
            return
        try:
            validate_contract_filename(uploaded_contract.name)
        except FileValidationError as exc:
            st.error(str(exc))
            return

        workspace = create_workspace(config.storage_root)
        try:
            contract_path = persist_contract(uploaded_contract, workspace)
            pdf_path = prepare_pdf_path(workspace)
            with st.spinner("Running automated analysis. This can take a few minutes..."):
                slither_report, mythril_report, summary_text, generated_pdf = execute_audit(
                    config,
                    contract_path,
                    PROMPT_TEMPLATE,
                    pdf_path,
                )
            st.success("Audit complete! Sending email...")
            send_report(config.email, st.session_state["customer_email"], summary_text, generated_pdf)
            st.success("Report emailed successfully.")

            st.download_button(
                label="Download PDF Report",
                data=generated_pdf.read_bytes(),
                file_name=generated_pdf.name,
                mime="application/pdf",
            )

            with st.expander("Slither Raw Output"):
                st.json(slither_report)
            with st.expander("Mythril Raw Output"):
                st.json(mythril_report)

        except Exception as exc:  # pragma: no cover - visible to user
            st.error(f"Audit failed: {exc}")
        finally:
            secure_delete(workspace)
            st.session_state.pop("payment_verified", None)
            st.session_state.pop("checkout_url", None)
            st.session_state.pop("customer_email", None)


if __name__ == "__main__":
    _audit_form()
