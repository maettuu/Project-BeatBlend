from typing import Optional
from .camel_model import CamelModel

class User(CamelModel):
    id: Optional[str] = None
    username: str


class SpotifyUser(User):
    username: Optional[str] = None
    auth_code: str
