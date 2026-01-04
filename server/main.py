# server/main.py

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.api.search import router as search_router
from server.api.video import router as video_router
from server.middleware.schema_validation import UISchemaValidationMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

# ------------------------------------------------------------------
# App initialization (SERVER OWNER)
# ------------------------------------------------------------------
app = FastAPI(title="GreenStream Backend")
app.add_middleware(UISchemaValidationMiddleware)
app.include_router(search_router)
app.include_router(video_router)

print("✅ SERVER LOADED")

# ------------------------------------------------------------------
# Static Web UI (HTML / JS / CSS)
# ------------------------------------------------------------------
UI_WEB_PATH = PROJECT_ROOT / "frontend" / "ui_web"
print("✅ UI_WEB_PATH =", UI_WEB_PATH)

app.mount(
    "/ui",
    StaticFiles(directory=UI_WEB_PATH, html=True),
    name="ui",
)

app.mount(
    "/assets",
    StaticFiles(directory=UI_WEB_PATH / "assets"),
    name="assets",
)



# ------------------------------------------------------------------
# API Routers
# ------------------------------------------------------------------
from server.api.ui import router as ui_router  # noqa: E402

app.include_router(ui_router)

# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


