import os
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

import models
from auth import create_token

oauth = OAuth()

oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def github_login(request: Request):
    redirect_uri = str(request.base_url) + "auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


async def github_callback(request: Request, db: Session):

    token = await oauth.github.authorize_access_token(request)
    user_data = await oauth.github.get("user", token=token)

    github_user = user_data.json()

    email = github_user.get("email")

    if not email:
        email = f"{github_user['login']}@github"

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(email=email, password="None")
        db.add(user)
        db.commit()

    jwt_token = create_token(user.email)

    return RedirectResponse(f"/?token={jwt_token}")


async def google_login(request: Request):
    redirect_uri = str(request.base_url) + "auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

async def google_callback(request: Request, db: Session):

    token = await oauth.google.authorize_access_token(request)

    user_info = token["userinfo"]
    email = user_info["email"]

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(email=email, password="oauth")
        db.add(user)
        db.commit()

    jwt_token = create_token(user.email)

    return RedirectResponse(f"/?token={jwt_token}")