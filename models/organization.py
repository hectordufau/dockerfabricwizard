from typing import List, Optional

from pydantic import BaseModel

from models.ca import Ca
from models.peer import Peer


class Organization(BaseModel):
    name: str = None
    ca: Ca = None
    peers: List[Peer] = []
    qtypeers: int = 0
    keystore: Optional[str] = None
