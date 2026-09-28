"""Sidecar kernel — stripe-payment-integration. Does not replace src/."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
SYSTEM_ID = os.getenv("GARCAR_SYSTEM_ID", "stripe-payment-integration")
CHECKOUT = "https://buy.stripe.com/dRm8wPbb72pY2Mz8BR43S1D"
app = FastAPI(title=f"Garcar · {SYSTEM_ID}")
@app.get("/health")
def health():
    return {"ok": True, "system": SYSTEM_ID, "tier": "CASH", "mode": "sidecar", "ts": datetime.now(timezone.utc).isoformat()}
@app.get("/offer")
def offer():
    return RedirectResponse(CHECKOUT, status_code=302)
