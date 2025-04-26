from fastapi import APIRouter
from db.mongo import db

router = APIRouter()


@router.get("/health")
async def health():
    try:
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
