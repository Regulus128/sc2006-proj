from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
OUT_PATH = BASE_DIR / "content" / "out" / "hawker_opportunities_ver2.geojson"

@router.get("/opportunity.geojson")
def opportunity_geojson():
    if not OUT_PATH.exists():
        raise HTTPException(status_code=404, detail="GeoJSON not found in content/out/")
    return FileResponse(str(OUT_PATH), media_type="application/geo+json")


