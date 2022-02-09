from typing import Optional, Any
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Depends
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.status import HTTP_403_FORBIDDEN

from dspback.database.models import RepositoryTokenTable, UserTable
from dspback.config import get_settings
from dspback.pydantic_schemas import ORCIDResponse, RepositoryToken, RepositoryType, TokenData


class OAuth2AuthorizationBearerToken(OAuth2):
    """
    Handles a bearer Authorization token in both a header or a cookie, making it compatible with both web and API
    requests.
    """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request, access_token: Optional[str] = None) -> Optional[str]:
        authorization = False
        scheme = "bearer"

        if access_token:
            authorization = True
            param = access_token

        else:
            header_authorization: str = request.headers.get("Authorization")
            cookie_authorization: str = request.cookies.get("Authorization")

            header_scheme, header_param = get_authorization_scheme_param(header_authorization)
            cookie_scheme, cookie_param = get_authorization_scheme_param(cookie_authorization)

            if header_scheme.lower() == scheme:
                authorization = True
                param = header_param

            elif cookie_scheme.lower() == scheme:
                authorization = True
                param = cookie_param

        if not authorization:
            if self.auto_error:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authenticated")
            else:
                return None
        return param


class Token(BaseModel):
    access_token: str
    token_type: str


oauth2_scheme = OAuth2AuthorizationBearerToken(tokenUrl="/token")


def url_for(request: Request, name: str, **path_params: Any) -> str:
    url_path = request.app.url_path_for(name, **path_params)
    # TODO - get the parent router path instead of hardcoding /api
    return "https://{}{}".format(get_settings().outside_host, url_path)


def create_access_token(data: dict, expiration_minutes: str, secret_key: str, algorithm: str) -> str:
    to_encode = data.copy()
    access_token_expires = timedelta(minutes=expiration_minutes)
    expire = datetime.utcnow() + access_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def create_or_update_user(db: Session, orcid_response: ORCIDResponse) -> UserTable:
    db_user: UserTable = get_user_table(db, orcid_response.orcid)
    if db_user:
        db_user = update_user_table(db, db_user, orcid_response)
    else:
        db_user = create_user_table(db, orcid_response)
    return db_user


def create_user_table(db: Session, orcid_response: ORCIDResponse) -> UserTable:
    db_user = UserTable(
        name=orcid_response.name,
        orcid=orcid_response.orcid,
        access_token=orcid_response.access_token,
        refresh_token=orcid_response.refresh_token,
        expires_in=orcid_response.expires_in,
        expires_at=orcid_response.expires_at,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_table(db: Session, db_user: UserTable, orcid_response: ORCIDResponse) -> UserTable:
    db_user.access_token = orcid_response.access_token
    db_user.refresh_token = orcid_response.refresh_token
    db_user.expires_in = orcid_response.expires_in
    db_user.expires_at = orcid_response.expires_at
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def create_or_update_repository_token(db, user: UserTable, repository, token) -> RepositoryToken:
    repository_token_table: RepositoryTokenTable = get_repository_table(db, user, repository)
    if repository_token_table:
        repository_token_table = update_repository_token(db, repository_token_table, token)
    else:
        repository_token_table = create_repository_token(repository, db, user, token)
    return RepositoryToken.from_orm(repository_token_table)


def create_repository_token(repository: str, db: Session, user: UserTable, repository_response) -> RepositoryTokenTable:
    # zenodo does not have a refresh_token apparently
    db_repository = RepositoryTokenTable(
        type=repository,
        access_token=repository_response['access_token'],
        user_id=user.id,
        # refresh_token=repository_response['access_token'],
        expires_in=repository_response.get('expires_in', None),
        expires_at=repository_response.get('expires_at', None)
    )
    db.add(db_repository)
    db.commit()
    db.refresh(db_repository)
    return db_repository


def update_repository_token(
    db: Session, db_repository: RepositoryTokenTable, repository_response
) -> RepositoryTokenTable:
    db_repository.access_token = repository_response['access_token']
    # db_repository.refresh_token = repository_response['refresh_token']
    db_repository.expires_in = repository_response.get('expires_in', None)
    db_repository.expires_at = repository_response.get('expires_at', None)
    # db_repository.refresh_token = repository_response['refresh_token']
    db.add(db_repository)
    db.commit()
    db.refresh(db_repository)
    return db_repository


def get_user_table(db: Session, orcid: str) -> UserTable:
    user_table = db.query(UserTable).filter(UserTable.orcid == orcid).first()
    return user_table


def get_repository_table(db: Session, user: UserTable, repository_type: RepositoryType) -> RepositoryTokenTable:
    repository_table = (
        db.query(RepositoryTokenTable)
        .filter(RepositoryTokenTable.user_id == user.id, RepositoryTokenTable.type == repository_type)
        .first()
    )
    return repository_table


def get_db(request: Request) -> Session:
    return request.state.db


async def get_current_user(request: Request, settings=Depends(get_settings), token: str = Depends(oauth2_scheme)) -> UserTable:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    db: Session = get_db(request)
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        token_data = TokenData(**payload)
        if token_data.orcid is None:
            raise credentials_exception
        if token_data.expiration < datetime.utcnow().timestamp():
            # TODO register token in db for requested expiration
            credentials_exception.detail = "Token is expired"
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user: UserTable = get_user_table(db, orcid=token_data.orcid)
    if user is None:
        raise credentials_exception
    return user
