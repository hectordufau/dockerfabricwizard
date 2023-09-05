from typing import Optional

from pydantic import BaseModel


class Chaincode(BaseModel):
    name: str = None
    servicename: Optional[str] = None
    version: int = 0
    packageid: Optional[str] = None
    ccport: int = 0
    invoke: bool = False
    function: Optional[str] = None
    usetls: bool = False
    client_key: Optional[str] = None
    client_cert: Optional[str] = None
    root_cert: Optional[str] = None
