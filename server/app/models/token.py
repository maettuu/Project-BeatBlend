from typing import Optional
from .camel_model import CamelModel


class Token(CamelModel):
    access_token: str
    token_type: str


class SpotifyToken(Token):
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
