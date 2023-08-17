from typing import Optional

from pydantic import BaseModel

class Database(BaseModel):
    name: str = None
    COUCHDB_USER: Optional[str] = None
    COUCHDB_PASSWORD: Optional[str] = None
    port: int = 0