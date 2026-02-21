import asyncio
import logging
import os
from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse, Response

from .auth import verify_api_key
from .generator import generate_image
from .models import ImageRequest

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Title Image Service",
    description="Erzeugt 16:9-Titelbilder aus JSON-Parametern.",
    version="0.1.0",
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(
    request: ImageRequest,
    _: str = Depends(verify_api_key),
):
    data = request.model_dump()
    filename = data.pop("dateiname", "").strip()
    if not filename:
        filename = datetime.now().strftime("linkedin_title_%Y-%m-%d-%H-%M.png")

    try:
        png_bytes: bytes = await asyncio.to_thread(generate_image, data, None)
    except Exception as e:
        logger.exception("Fehler bei der Bildgenerierung: %s", e)
        # Pillow wirft ValueError bei ungültigen Farben
        if isinstance(e, (ValueError, OSError)):
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=str(e))
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Interner Serverfehler")

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def run():
    import uvicorn
    uvicorn.run(
        "title_image_service.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
