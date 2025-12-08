from fastapi import FastAPI, Request, HTTPException
import httpx

from .models import LeadIn
from .config import N8N_WEBHOOK_URL

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

templates = Jinja2Templates(directory="backend/fastapi_app/templates")

app = FastAPI(title="FlowDesk API")


@app.post("/lead")
async def create_lead(lead: LeadIn, request: Request):
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
        print("Error when calling n8n:", repr(e))
        raise HTTPException(
            status_code=503, detail=f"Error sending data to automation service: {e}"
        )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=503,
            detail=f"Automation service returned {resp.status_code}: {resp.text[:200]}",
        )

    return {"status": "ok", "forwarded_to_n8n": True}


@app.get("/lead-form", response_class=HTMLResponse)
async def lead_form(request: Request):
    return templates.TemplateResponse("lead_form.html", {"request": request})


@app.post("/lead-form")
async def lead_form_submit(request: Request):
    form = await request.form()
    name = form.get("name")
    email = form.get("email")

    payload = {
        "name": name,
        "email": email,
        "source": "web-form",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(N8N_WEBHOOK_URL, json=payload)
        resp.raise_for_status()

    return templates.TemplateResponse("lead_success.html", {"request": request})


# python -m uvicorn backend.fastapi_app.main:app --reload
