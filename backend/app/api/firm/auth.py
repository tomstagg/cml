"""Firm auth: register, login, logout."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.firm_user import FirmUser, FirmUserRole
from app.models.organisation import Organisation
from app.schemas.firm import FirmLoginRequest, FirmLoginResponse, FirmRegisterRequest
from app.services.auth import create_access_token, hash_password, verify_password
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["firm-auth"])


@router.post("/register", response_model=FirmLoginResponse, status_code=status.HTTP_201_CREATED)
async def register(body: FirmRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new firm user via enrollment token."""
    if not body.accept_terms:
        raise HTTPException(status_code=400, detail="You must accept the terms and conditions")

    # Validate enrollment token
    org_result = await db.execute(
        select(Organisation).where(
            Organisation.enrollment_token == body.enrollment_token,
            Organisation.enrollment_token_used == False,
        )
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Invalid or already-used enrollment token")

    # Check email not already registered
    existing = await db.execute(select(FirmUser).where(FirmUser.email == str(body.email)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = FirmUser(
        org_id=org.id,
        email=str(body.email),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=FirmUserRole.admin,
    )
    db.add(user)

    org.enrolled = True
    org.enrollment_token_used = True
    db.add(org)

    await db.flush()

    token = create_access_token(str(user.id), str(org.id))
    return FirmLoginResponse(
        access_token=token,
        org_id=org.id,
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.post("/login", response_model=FirmLoginResponse)
async def login(body: FirmLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email + password."""
    result = await db.execute(select(FirmUser).where(FirmUser.email == str(body.email)))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.last_login = datetime.now(timezone.utc)
    db.add(user)

    token = create_access_token(str(user.id), str(user.org_id))
    return FirmLoginResponse(
        access_token=token,
        org_id=user.org_id,
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.get("/me")
async def get_me(current_user: FirmUser = Depends(get_current_user)):
    """Return current user info."""
    return {
        "user_id": current_user.id,
        "org_id": current_user.org_id,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
    }
