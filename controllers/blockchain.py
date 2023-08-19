from models.domain import Domain


class Blockchain:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def genesisBlock(self):
        pass

    def createChannel(self):
        pass

    def joinChannel(self):
        pass

    def setAnchorPeer(self):
        pass
