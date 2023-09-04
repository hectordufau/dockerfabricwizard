from typing import Optional

from pydantic import BaseModel


class Chaincode(BaseModel):
    name: str = None
    version: int = 0
    packageid: Optional[str] = None
    ccport: int = 0
    invoke: bool = False
    function: Optional[str] = None
