from fastapi import APIRouter

API_VERSION = "1.0"

router = APIRouter()


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "roku-lan-media", "api_version": API_VERSION}
