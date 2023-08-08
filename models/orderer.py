from pydantic import BaseModel


class Orderer(BaseModel):
    name: str = None
