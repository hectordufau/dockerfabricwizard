from pydantic import BaseModel


class Peer(BaseModel):
    name: str = None
    CORE_PEER_LISTENADDRESS:str = "0.0.0.0:7051"
