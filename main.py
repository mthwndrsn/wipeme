from fastapi import FastAPI, Form
from pydantic import BaseModel
from typing import Optional
import requests
from datetime import datetime
import pdfkit

app = FastAPI()

# Dummy breach check using HaveIBeenPwned public API
def check_breaches(email: str):
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    headers = {
        "hibp-api-key": "your_api_key_here",  # Replace with your actual key
        "User-Agent": "IdentityCleanseMVP"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        return []
    else:
        return [{"error": "Unable to fetch breach data."}]

# Risk scoring model
def calculate_risk(breaches):
    if not breaches:
        return 10  # Low risk
    count = len(breaches)
    return min(100, 10 + count * 15)  # Basic score model

# Report generation (as HTML string for now)
def generate_report(email, breaches, score):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <html>
    <head><title>Identity Cleanse Report</title></head>
    <body>
        <h1>Identity Cleanse Report</h1>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Generated at:</strong> {now}</p>
        <p><strong>Risk Score:</strong> {score}/100</p>
        <h2>Breaches:</h2>
        <ul>
    """
    if breaches and isinstance(breaches, list):
        for breach in breaches:
            html += f"<li>{breach.get('Name', 'Unknown')} – {breach.get('BreachDate', '')}</li>"
    else:
        html += "<li>No breaches found or error in lookup.</li>"
    html += """
        </ul>
    </body>
    </html>
    """
    return html

@app.post("/generate-report")
async def generate_identity_report(email: str = Form(...)):
    breaches = check_breaches(email)
    risk_score = calculate_risk(breaches)
    report_html = generate_report(email, breaches, risk_score)

    # Convert to PDF (optionally save or serve directly)
    pdf_path = f"report_{email.replace('@', '_at_')}.pdf"
    pdfkit.from_string(report_html, pdf_path)

    return {"message": "Report generated successfully", "risk_score": risk_score, "pdf_file": pdf_path}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Identity Cleanse MVP. Use POST /generate-report to submit email."}
