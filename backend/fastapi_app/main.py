from fastapi import FastAPI, Request, HTTPException
import httpx

from .models import LeadIn
from .config import N8N_WEBHOOK_URL

app = FastAPI(title="FlowDesk API")


@app.post("/lead")
async def create_lead(lead: LeadIn, request: Request):
    """Принимает лида от фронта/бота и пересылает в n8n."""

    client_host = request.client.host

    payload = {
        "name": lead.name,
        "email": lead.email,
        "source": lead.source or "web",
        "client_ip": client_host,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=payload)
    except httpx.RequestError as e:
        # n8n недоступен
        raise HTTPException(
            status_code=502, detail=f"Error sending data to automation service: {e}"
        )

    if resp.status_code >= 400:
        # n8n ответил ошибкой
        raise HTTPException(
            status_code=502,
            detail=f"Automation service returned {resp.status_code}: {resp.text}",
        )

    return {"status": "ok", "forwarded_to_n8n": True}
