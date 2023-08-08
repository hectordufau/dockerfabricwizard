from typing import List

from pydantic import BaseModel

from models.ca import Ca
from models.orderer import Orderer
from models.organization import Organization


class Domain(BaseModel):
    name: str = None
    orderer: Orderer = None
    ca: Ca = None
    qtyorgs: int = 0
    organizations: List[Organization] = []
    networkname: str = None
