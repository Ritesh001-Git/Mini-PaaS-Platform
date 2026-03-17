import os
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

import models
from auth import create_token

# -----------------------------
# Environment Config
# -----------------------------
BASE_URL = os.getenv("BASE_URL")

if not BASE_URL:
    raise Exception("BASE_URL environment variable is not set")

BASE_URL = BASE_URL.rstrip("/")  # avoid double slashes

# -----------------------------
# OAuth Setup
# -----------------------------
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

# -----------------------------
# GitHub OAuth
# -----------------------------
async def github_login(request: Request):
    redirect_uri = f"{BASE_URL}/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


async def github_callback(request: Request, db: Session):
    try:
        token = await oauth.github.authorize_access_token(request)
        user_data = await oauth.github.get("user", token=token)
        github_user = user_data.json()
    except Exception:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed")

    email = github_user.get("email")

    # GitHub sometimes doesn't return email
    if not email:
        email = f"{github_user['login']}@github"

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(email=email, password="oauth")
        db.add(user)
        db.commit()

    jwt_token = create_token(user.email)

    return RedirectResponse(f"{BASE_URL}/?token={jwt_token}")


# -----------------------------
# Google OAuth
# -----------------------------
async def google_login(request: Request):
    redirect_uri = f"{BASE_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def google_callback(request: Request, db: Session):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
    except Exception:
        raise HTTPException(status_code=400, detail="Google OAuth failed")

    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    email = user_info["email"]

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(email=email, password="oauth")
        db.add(user)
        db.commit()

    jwt_token = create_token(user.email)

    return RedirectResponse(f"{BASE_URL}/?token={jwt_token}")