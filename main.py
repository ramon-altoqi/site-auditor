import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from auditor import audit_url, AuditError

load_dotenv()

app = FastAPI(
    title="Site Auditor",
    description="Auditoria técnica de SEO para URLs públicas",
    version="1.0.0",
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class AuditRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('O campo "url" não pode ser vazio')
        return v.strip()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["infra"])
def health():
    return {
        "status": "ok",
        "service": "site-auditor",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/audit", tags=["audit"])
def audit(body: AuditRequest):
    try:
        result = audit_url(body.url)
        return {"success": True, **result}
    except AuditError as e:
        return JSONResponse(
            status_code=e.http_status,
            content={"success": False, "error": {"type": e.error_type, "message": e.message}},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"type": "INTERNAL_ERROR", "message": str(e)}},
        )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
