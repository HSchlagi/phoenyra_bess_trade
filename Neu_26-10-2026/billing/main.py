from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import io

app = FastAPI(title="Phoenyra Billing API", version="0.1.0")

C_INVOICES = Counter("pho_bo_invoices_total", "Invoices generated")
INVOICES = {}

@app.post("/billing/generate")
def billing_generate(period: str = "2025-10"):
    inv_id = f"INV-{period}-0001"
    INVOICES[inv_id] = {"pdf": b"%PDF-FAKE%", "counterparty": "CP-A", "total_eur": 12345.67}
    C_INVOICES.inc()
    return {"period": period, "invoices":[{"invoice_id": inv_id, "counterparty":"CP-A", "total_eur":12345.67, "pdf_url": f"/billing/invoice/{inv_id}"}]}

@app.get("/billing/invoice/{id}")
def billing_invoice(id: str):
    doc = INVOICES.get(id)
    if not doc:
        raise HTTPException(404, "invoice not found")
    return Response(doc["pdf"], media_type="application/pdf")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
