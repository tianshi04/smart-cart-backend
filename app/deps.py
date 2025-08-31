from typing import Generator
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import DecodeError, ExpiredSignatureError
from typing import Annotated
from sqlmodel import Session
from pydantic import BaseModel

from app.core.database import engine
from app.core import security
from app.core.config import settings
from app.models import User
        
def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]

class TokenPayload(BaseModel):
    sub: str

def get_current_user(token: TokenDep, session: SessionDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token đã hết hạn")
    except DecodeError:
        raise HTTPException(status_code=403, detail="Token không hợp lệ")

    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

# def get_current_active_superuser(current_user: CurrentUser) -> User:
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=403, detail="The user doesn't have enough privileges"
#         )
#     return current_user