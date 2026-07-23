from datetime import datetime, timedelta, timezone
import logging
from typing import TYPE_CHECKING, Annotated

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from pwdlib import PasswordHash
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel, select

from .dependencies import SessionDep
from .links import SiteAccessRelationship

if TYPE_CHECKING:
    from .sites import Site

logger = logging.getLogger(f"uvicorn.{__name__}")

ACCESS_TOKEN_EXPIRE_MINUTES = 30

with open("private.pem", "rb") as f:
    private_key = f.read()

with open("public.pem", "rb") as f:
    public_key = f.read()


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

FAKE_HASH = password_hash.hash("password")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(SQLModel, table=False):
    username: str = Field(primary_key=True)
    email: str
    full_name: str
    disabled: bool
    permissions: str


class UserInDb(User, table=True):
    hashed_password: str

    sites: list["Site"] = Relationship(link_model=SiteAccessRelationship)


users = APIRouter(prefix="/users")


def authenticate_user(username, password, session: SessionDep) -> User:
    user = session.get(UserInDb, username)
    if not user:
        logger.info(f"failed login with nonexistent user {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="username or password is incorrect",
        )
    valid, new_hash = password_hash.verify_and_update(
        password=password, hash=user.hashed_password
    )
    if not valid:
        logger.info(f"failed login for user {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="username or password is incorrect",
        )
    if new_hash:
        user.hashed_password = new_hash
        session.commit()

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm="EdDSA")
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, public_key, algorithms=["EdDSA"])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = session.get(UserInDb, username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@users.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session=session)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


class PermissionChecker:
    def __init__(
        self, action: str, resource_type: str, path_param_name: str | None = None
    ):
        self.action = action
        self.resource_type = resource_type
        self.path_param_name = path_param_name

    def __call__(
        self, request: Request, user: Annotated[User, Depends(get_current_active_user)]
    ):
        user_perms = user.permissions.split(" ")

        # --- SCENARIO A: Collection Endpoint (No specific path param) ---
        if not self.path_param_name:
            # Must possess a wildcard to access the full collection
            wildcard_match = f"{self.action}:{self.resource_type}:*"
            global_wildcard = f"*:{self.resource_type}:*"

            if wildcard_match in user_perms or global_wildcard in user_perms:
                return True

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: You do not have global '{self.action}' access to all '{self.resource_type}' resources.",
            )

        # --- SCENARIO B: Instance Endpoint (Has path param) ---
        resource_id = request.path_params.get(self.path_param_name)
        if resource_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Configuration error: '{self.path_param_name}' missing from route path.",
            )

        res_id_str = str(resource_id)

        exact_match = f"{self.action}:{self.resource_type}:{res_id_str}"
        action_wildcard = f"*:{self.resource_type}:{res_id_str}"
        id_wildcard = f"{self.action}:{self.resource_type}:*"
        full_wildcard = f"*:{self.resource_type}:*"

        has_permission = any(
            perm in user_perms
            for perm in (exact_match, action_wildcard, id_wildcard, full_wildcard)
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Missing '{self.action}' on '{self.resource_type}:{res_id_str}'",
            )

        return True


@users.get("/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@users.get("/")
async def get_all_users(
    session: SessionDep,
    _: bool = Depends(PermissionChecker(action="read", resource_type="user")),
) -> list[User]:
    return [user for user in session.exec(select(UserInDb))]
