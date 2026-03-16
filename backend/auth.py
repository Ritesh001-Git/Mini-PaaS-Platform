import os
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from database import get_db
import models
from auth import create_token

oauth = OAuth()

# -----------------------------
# Register GitHub OAuth
# -----------------------------
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

# -----------------------------
# Register Google OAuth
# -----------------------------
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# -----------------------------
# GitHub Login
# -----------------------------
async def github_login(request: Request):
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


# -----------------------------
# GitHub Callback
# -----------------------------
async def github_callback(request: Request, db: Session):

    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)

    github_user = resp.json()

    email = github_user.get("email")

    # Some GitHub accounts hide email
    if not email:
        email = github_user["login"] + "@github"

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(email=email, password="oauth")
        db.add(user)
        db.commit()

    jwt_token = create_token(user.email)

    return RedirectResponse(f"/?token={jwt_token}")


# -----------------------------
# Google Login
# -----------------------------
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


# -----------------------------
# Google Callback
# -----------------------------
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