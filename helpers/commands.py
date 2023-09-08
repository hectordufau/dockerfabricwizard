from models.domain import Domain


class Commands:
    
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain