from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app import crud, schemas
from app.core import security
from app.core.config import settings
from app.deps import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# ---------------------------
# Register endpoint
# ---------------------------
@router.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED
)
async def register_new_user(
    user_in: schemas.UserCreate,
    session: Session = Depends(get_db),
) -> schemas.UserOut:
    """
    Create a new user in the system.

    Raises:
        HTTPException: If a user with the same email already exists.
    """
    existing_user = crud.get_user_by_email(session=session, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists."
        )

    new_user = crud.register_new_user(session=session, user_data=user_in)
    return new_user


# ---------------------------
# Login endpoint
# ---------------------------
@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_db),
) -> schemas.Token:
    """
    Authenticate user and return an access token.

    Raises:
        HTTPException: If the credentials are incorrect.
    """
    user = crud.get_user_by_email(session=session, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}
