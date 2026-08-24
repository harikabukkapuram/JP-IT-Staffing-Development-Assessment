# JP IT STAFFING LLC — Development Internship Assessment

This project implements both demo flows shown in the assessment videos.

## Part 1 — EmailPro
- CSV upload and validation
- Duplicate removal
- Business / individual classification
- Campaign creation
- Campaign reporting
- Responsive dark UI

## Part 2 — Singing Bowl Export Desk
- Search API integration (Serper when `SERPER_API_KEY` is configured)
- Demo fallback data so the project runs without an API key
- PDF upload and text extraction
- PDF lead-report export
- SMTP email integration with demo mode fallback

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Optional real API/email setup

Copy `.env.example` to `.env` or configure environment variables.

For real search:
`SERPER_API_KEY=...`

For real Gmail SMTP:
`SMTP_HOST=smtp.gmail.com`
`SMTP_USER=your Gmail address`
`SMTP_PASSWORD=your Gmail App Password`

Do not commit API keys, passwords or `.env` files.

## Demo CSV

Create a file named `contacts.csv`:

```csv
name,email
Acme,info@acme.com
John,john@gmail.com
Sales,sales@company.com
Priya,priya@gmail.com
```

Upload it in EmailPro, run classification, then create a campaign.

## Submission note

The app intentionally has safe demo fallbacks. This means a reviewer can run and evaluate the UI/API workflow without needing your private credentials.
