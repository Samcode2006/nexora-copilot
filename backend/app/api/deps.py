from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.security import AuthUser, TokenVerifier, unauthenticated

_bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_token_verifier() -> TokenVerifier:
    return TokenVerifier(get_settings())


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> AuthUser:
    """The authenticated student comes ONLY from the validated token, never from the client."""
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise unauthenticated()
    return await verifier.verify(creds.credentials)


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
