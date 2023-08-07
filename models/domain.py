from typing import List

from models.organization import Organization


class Domain:
    name: str
    organizations: List[Organization]
    qtdeorgs: int
