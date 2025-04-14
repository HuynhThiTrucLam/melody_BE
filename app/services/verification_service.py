from random import randint
from services.email_service import send_email
from db.mongo import verification_codes_collection
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from core import security
from core.config import logger


async def send_verification_code(email: str, purpose: str = "signup"):
    try:
        logger.info(f"send_verification_code:: Sending verification code to {email}")
        existing = verification_codes_collection.find_one(
            {"email": email, "purpose": purpose}
        )

        if existing and datetime.utcnow() < existing["expires_at"] - timedelta(
            minutes=9
        ):
            logger.info(f"send_verification_code:: EMAIL - Too many requests")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another code.",
            )

        logger.info(f"send_verification_code:: Generating code")
        code = str(randint(1000, 9999))
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        hashed_code = security.get_hash_code(code)

        verification_codes_collection.insert_one(
            {
                "email": email,
                "purpose": purpose,
                "code": hashed_code,
                "expires_at": expires_at,
            }
        )
        logger.info(
            f"send_verification_code:: EMAIL - Sending verification code to {email}"
        )
        await send_email(email, code)
        return {"message": "Verification code sent."}
    except Exception as e:
        logger.error(f"send_verification_code:: ERROR - {e}")
        raise HTTPException(status_code=500, detail=str(e))


def verify_verification_code(email: str, code: str):
    try:
        entry = verification_codes_collection.find_one(
            {"email": email, "purpose": "signup"}
        )

        if not entry:
            raise HTTPException(status_code=400, detail="Verification code not found.")

        if entry["verified"]:
            raise HTTPException(status_code=400, detail="Code already verified.")

        if not security.verify_hashed_code(code, entry["code"]):
            raise HTTPException(status_code=400, detail="Invalid verification code.")

        if datetime.utcnow() > entry["expires_at"]:
            raise HTTPException(status_code=400, detail="Verification code expired.")

        verification_codes_collection.update_one(
            {"email": email, "purpose": "signup"}, {"$set": {"verified": True}}
        )

        return {"message": "Verification successful."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
