from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from data import CASES, CASES_BY_ID

app = FastAPI(title="Legal Case Management - Asana App Component Middleware")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
#  Asana App Component: Entry Point (Widget)
# ──────────────────────────────────────────────
@app.get("/widget")
async def widget():
    """Asana widget entry-point – sidebar'da gösterilen özet kart."""
    return {
        "template": "summary_with_details_v0",
        "metadata": {
            "title": "Hukuk Dosya Yönetimi",
            "subtitle": f"{len(CASES)} aktif dosya",
            "subicon": {"type": "completed"},
            "fields": [
                {
                    "name": "Toplam Dosya",
                    "type": "text_with_icon",
                    "text": str(len(CASES)),
                    "icon": "briefcase",
                },
                {
                    "name": "Bekleyen Ek",
                    "type": "text_with_icon",
                    "text": str(
                        sum(len(c["attachments"]) for c in CASES)
                    ),
                    "icon": "paperclip",
                },
            ],
            "num_comments": 0,
        },
    }


# ──────────────────────────────────────────────
#  Asana App Component: Modal Form (GET)
#  İlk açılışta case dropdown'ı döner.
# ──────────────────────────────────────────────
@app.get("/form")
async def form_metadata():
    """Modal ilk açıldığında case seçimi sunar."""
    case_options = [
        {
            "id": case["id"],
            "label": case["name"],
            "icon_url": None,
        }
        for case in CASES
    ]

    return {
        "template": "form_metadata_v0",
        "metadata": {
            "title": "Dosya & Ek Seçimi",
            "subtitle": "Bir hukuk dosyası seçin, ardından ek belgelerden birini seçin.",
            "on_change_callback": "/form/on_change",
            "submit_button_text": "Ekle",
            "fields": [
                {
                    "id": "case_id",
                    "name": "Hukuk Dosyası",
                    "type": "dropdown",
                    "is_required": True,
                    "options": case_options,
                    "width": "full",
                },
                {
                    "id": "attachment_id",
                    "name": "Ek Belge",
                    "type": "dropdown",
                    "is_required": True,
                    "options": [],
                    "width": "full",
                },
            ],
        },
    }


# ──────────────────────────────────────────────
#  Asana App Component: on_change callback
#  Case seçilince attachment dropdown'ı günceller.
# ──────────────────────────────────────────────
@app.post("/form/on_change")
async def form_on_change(request: Request):
    """Case seçimi değiştiğinde attachment listesini döner."""
    body = await request.json()
    changed_field = body.get("changed_field", "")
    values = body.get("values", {})

    case_options = [
        {"id": c["id"], "label": c["name"], "icon_url": None}
        for c in CASES
    ]

    attachment_options = []
    selected_case_id = values.get("case_id")

    if changed_field == "case_id" and selected_case_id:
        case = CASES_BY_ID.get(selected_case_id)
        if case:
            attachment_options = [
                {
                    "id": att["id"],
                    "label": att["name"],
                    "icon_url": None,
                }
                for att in case["attachments"]
            ]

    return {
        "template": "form_metadata_v0",
        "metadata": {
            "title": "Dosya & Ek Seçimi",
            "subtitle": "Bir hukuk dosyası seçin, ardından ek belgelerden birini seçin.",
            "on_change_callback": "/form/on_change",
            "submit_button_text": "Ekle",
            "fields": [
                {
                    "id": "case_id",
                    "name": "Hukuk Dosyası",
                    "type": "dropdown",
                    "is_required": True,
                    "options": case_options,
                    "width": "full",
                },
                {
                    "id": "attachment_id",
                    "name": "Ek Belge",
                    "type": "dropdown",
                    "is_required": True,
                    "options": attachment_options,
                    "width": "full",
                },
            ],
        },
    }


# ──────────────────────────────────────────────
#  Asana App Component: Form Submit
# ──────────────────────────────────────────────
@app.post("/form/submit")
async def form_submit(request: Request):
    """Seçilen case + attachment bilgisini onaylar."""
    body = await request.json()
    values = body.get("values", {})

    case_id = values.get("case_id")
    attachment_id = values.get("attachment_id")

    case = CASES_BY_ID.get(case_id)
    if not case:
        return JSONResponse(
            status_code=400,
            content={"error": "Geçersiz dosya seçimi."},
        )

    attachment = next(
        (a for a in case["attachments"] if a["id"] == attachment_id),
        None,
    )
    if not attachment:
        return JSONResponse(
            status_code=400,
            content={"error": "Geçersiz ek belge seçimi."},
        )

    return {
        "resource_name": attachment["name"],
        "resource_url": f"https://legalcrm.example.com/cases/{case_id}/attachments/{attachment_id}",
    }


# ──────────────────────────────────────────────
#  Yardımcı REST Endpoint'ler (test / debug)
# ──────────────────────────────────────────────
@app.get("/cases")
async def list_cases():
    """Tüm case'leri listeler."""
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "client": c["client"],
            "case_type": c["case_type"],
            "status": c["status"],
            "attachment_count": len(c["attachments"]),
        }
        for c in CASES
    ]


@app.get("/cases/{case_id}/attachments")
async def list_attachments(case_id: str):
    """Belirli bir case'in attachment'larını döner."""
    case = CASES_BY_ID.get(case_id)
    if not case:
        return JSONResponse(
            status_code=404,
            content={"error": f"'{case_id}' bulunamadı."},
        )
    return case["attachments"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
