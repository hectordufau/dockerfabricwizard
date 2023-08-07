from typing import List

from models.ca import Ca
from models.orderer import Orderer
from models.peer import Peer


class Organization:
    name: str
    orderer: Orderer
    ca: Ca
    peers: List[Peer]
    qtdepeers: int
