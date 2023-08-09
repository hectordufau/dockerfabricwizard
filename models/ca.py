from pydantic import BaseModel


class Ca(BaseModel):
    name: str = None
    FABRIC_CA_HOME: str = "/etc/hyperledger/fabric-ca-server"
    FABRIC_CA_SERVER_CA_NAME: str = None
    FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS: str = "0.0.0.0:18054"
    FABRIC_CA_SERVER_PORT: int = 0
    FABRIC_CA_SERVER_TLS_ENABLED: bool = True
    serverport: int = 0
    operationslistenport: int = 0
