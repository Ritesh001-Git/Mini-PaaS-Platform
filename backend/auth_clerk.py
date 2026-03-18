from fastapi import Request, HTTPException
from clerk_backend_api import Clerk
import os

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))


def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        token = auth_header.split(" ")[1]
    except:
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    try:
        session = clerk.sessions.verify_session(token)
        return session
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")