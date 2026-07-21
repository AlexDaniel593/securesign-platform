from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.crypto import router as crypto_router
from app.api.v1.certificates import router as certificates_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(crypto_router, prefix="/crypto", tags=["Cryptography"])
router.include_router(certificates_router, prefix="/certificates", tags=["Certificates"])
