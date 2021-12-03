from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from dspback.config import oauth, repository_config
from dspback.database.models import UserTable
from dspback.database.procedures import delete_repository_access_token
from dspback.dependencies import create_or_update_repository_token, get_current_user, get_db, url_for
from dspback.schemas import RepositoryToken, RepositoryType

router = APIRouter()


@router.get('/authorize/{repository}')
async def authorize_repository(repository: str, request: Request, user: UserTable = Depends(get_current_user)):
    redirect_uri = url_for(request, 'auth_repository', repository=repository)
    return await getattr(oauth, repository).authorize_redirect(request, redirect_uri)


@router.get("/auth/{repository}")
async def auth_repository(
    request: Request,
    repository: RepositoryType,
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        repo = getattr(oauth, repository)
        token = await repo.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')

    create_or_update_repository_token(db, user, repository, token)
    return RedirectResponse("/")


@router.get("/access_token/{repository}", response_model=RepositoryToken)
async def get_access_token(
    repository: RepositoryType, user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)
) -> RepositoryToken:
    repository_token: RepositoryToken = user.repository_token(db, repository)
    if not repository_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return repository_token


@router.delete("/access_token/{repository}", response_model=RepositoryToken)
async def delete_access_token(
    repository: RepositoryType, user: UserTable = Depends(get_current_user), db: Session = Depends(get_db)
) -> RepositoryToken:
    delete_repository_access_token(db, repository, user)


@router.get("/urls/{repository}")
async def get_urls(repository: RepositoryType, user: UserTable = Depends(get_current_user)):
    # TODO, build schema for repository config and validate
    if repository not in repository_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(repository_config[repository])
