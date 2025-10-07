# Affordable Smart Contract Audits

A production-ready Streamlit MVP that sells automated smart contract audits for a flat $99 per contract. Clients upload a Solidity file, pay via Stripe Checkout, and receive an AI-curated PDF report via email.

## Directory Structure

```
.
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── prompts
│   │   └── executive_summary_prompt.md
│   ├── services
│   │   ├── __init__.py
│   │   ├── ai_summary.py
│   │   ├── audit_runner.py
│   │   ├── email_service.py
│   │   ├── mythril_scan.py
│   │   ├── payments.py
│   │   ├── pdf_report.py
│   │   └── slither_scan.py
│   └── utils
│       ├── __init__.py
│       └── file_manager.py
├── .env.example
├── .streamlit
│   └── config.toml
├── Dockerfile
├── README.md
└── requirements.txt
```

## Core Workflow

1. **Payment Gating:** Users must complete Stripe Checkout before running scans. Sessions are verified using the `session_id` returned by Stripe.
2. **Secure Processing:** Uploaded contracts are stored inside a unique workspace under `AUDIT_STORAGE_ROOT`. After the audit finishes (success or failure) all artifacts are securely deleted.
3. **Automated Scans:** Slither and Mythril run via their CLI interfaces. JSON outputs feed the AI summarizer.
4. **AI Executive Summary:** An OpenAI model produces client-friendly Markdown based on the raw scan data.
5. **Branded PDF Report:** Markdown is rendered into a PDF with metadata and raw JSON appendices.
6. **Email Delivery:** The finished PDF and summary are emailed to the client via SMTP.

## Environment Configuration

Copy `.env.example` to `.env` (or configure equivalent environment variables in your deployment platform). Required values:

- Stripe: `STRIPE_SECRET_KEY`, optional `STRIPE_PRICE_ID`, and success/cancel URLs. Configure your success URL as `https://your-domain.com?session_id={CHECKOUT_SESSION_ID}` so Stripe injects the paid session.
- Email: SMTP host, port, credentials, and sender metadata.
- OpenAI: API key and preferred model ID (default `gpt-4o-mini`).
- Storage: Optional `AUDIT_STORAGE_ROOT` override.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export $(cat .env | xargs)  # or use python-dotenv
streamlit run app/main.py
```

Ensure `slither` and `myth` executables are available (installed by `pip install -r requirements.txt`). Both tools depend on `solc`; install via `sudo apt-get install solc` on Linux or follow the official docs for macOS/Windows.

## Docker Build & Run

```bash
docker build -t affordable-audits .
docker run --env-file .env -p 8501:8501 affordable-audits
```

## DigitalOcean Deployment

1. **Create Droplet:** Provision a Docker-enabled droplet (e.g., Ubuntu 22.04, 2 vCPU/4GB RAM).
2. **Copy Files:** `scp -r . root@your-droplet-ip:/opt/affordable-audits`
3. **SSH In:** `ssh root@your-droplet-ip`
4. **Environment:** `cd /opt/affordable-audits && cp .env.example .env` then edit values, especially Stripe URLs pointing to your droplet domain.
5. **Docker Build:** `docker build -t affordable-audits .`
6. **Run Container:**
   ```bash
   docker run -d \
     --name affordable-audits \
     --restart unless-stopped \
     --env-file /opt/affordable-audits/.env \
     -p 80:8501 \
     affordable-audits
   ```
7. **Firewall:** Open HTTP (80) and HTTPS (443). Configure an Nginx reverse proxy or DigitalOcean Load Balancer + SSL for production.

## Stripe Configuration

- Create a product named **Smart Contract Audit** priced at $99.
- Generate a Checkout success URL `https://your-domain.com?session_id={CHECKOUT_SESSION_ID}` and cancel URL `https://your-domain.com/cancel`.
- Set `STRIPE_PRICE_ID` to the price ID or leave unset to use the fallback price defined in code.

## Email Provider Setup

Use a transactional provider (e.g., SendGrid, Postmark, SES). Update SMTP credentials in `.env`. The app uses TLS by default.

## Example Audit Run

### Example Input Contract (`ExampleToken.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ExampleToken {
    mapping(address => uint256) public balanceOf;
    address public owner;

    constructor() {
        owner = msg.sender;
        balanceOf[msg.sender] = 1_000_000 ether;
    }

    function transfer(address to, uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "insufficient");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
    }

    function withdrawAll() external {
        (bool ok, ) = owner.call{value: address(this).balance}("");
        require(ok, "withdraw failed");
    }
}
```

### Sample Output (Excerpt)

- **Executive Summary:**
  - Critical: External call to `owner.call` allows reentrancy. Mitigation: use `pull` pattern or reentrancy guard.
  - Medium: Missing access control on `withdrawAll`; anyone can drain funds. Restrict to owner.
  - Informational: Token logic lacks events.
- **Attachments:** PDF report with branded cover page, AI summary, full JSON payload from Slither/Mythril.
- **Delivery:** Email sent to client with PDF attached and summary in body.

## Maintenance Tips

- Monitor API usage from OpenAI and Stripe dashboards.
- Rotate SMTP and API keys regularly.
- Keep dependencies updated (`pip install --upgrade -r requirements.txt`).
- Periodically run integration tests with representative contracts.

---

Built for rapid validation while preserving professional UX, compliance-ready billing, and secure handling of client IP.
