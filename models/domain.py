from typing import List, Optional

from pydantic import BaseModel

from models.ca import Ca
from models.chaincode import Chaincode
from models.orderer import Orderer
from models.organization import Organization


class Domain(BaseModel):
    name: str = None
    ca: Ca = None
    caorderer: Ca = None
    orderer: Orderer = None
    qtyorgs: int = 0
    organizations: List[Organization] = []
    networkname: Optional[str] = None
    chaincodes: List[Chaincode] = []
