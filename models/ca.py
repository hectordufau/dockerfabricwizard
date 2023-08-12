from typing import Optional
from pydantic import BaseModel


class Ca(BaseModel):
    name: str = ""
    FABRIC_CA_HOME: str = "/etc/hyperledger/fabric-ca-server"
    FABRIC_CA_SERVER_CA_NAME: Optional[str] = None
    FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS: str = "0.0.0.0:18054"
    FABRIC_CA_SERVER_PORT: int = 8054
    FABRIC_CA_SERVER_TLS_ENABLED: bool = True
    volumes:str = Optional[str]
    serverport: int = 8054
    operationslistenport: int = 18054
