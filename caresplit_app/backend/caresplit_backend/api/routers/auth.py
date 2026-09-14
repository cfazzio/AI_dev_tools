from fastapi import APIRouter, Depends, HTTPException, status

from caresplit_backend.api.auth import TokenStore, get_token_store, verify_password
from caresplit_backend.api.models import LoginRequest, TokenResponse
from caresplit_backend.api.store import Store, get_store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def login(
    body: LoginRequest,
    store: Store = Depends(get_store),
    token_store: TokenStore = Depends(get_token_store),
) -> TokenResponse:
    user = store.users.get(body.username)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    token, expires_at = token_store.issue(user.username)
    return TokenResponse(access_token=token, expires_at=expires_at)
