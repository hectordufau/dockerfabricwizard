import os
from pathlib import Path

from rich.console import Console

from models.domain import Domain

console = Console()


class Blockchain:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        console.print("[bold white]# Creating genesis block[/]")
        self.genesisBlock()
        console.print("[bold white]# Creating channel[/]")
        self.createChannel()
        console.print("[bold white]# Joinning channel[/]")
        self.joinChannel()
        console.print("[bold white]# Setting anchor peers[/]")
        self.setAnchorPeer()

    def genesisBlock(self):
        pathchannel = Path("domains/" + self.domain.name + "/channel-artifacts")
        pathchannel.mkdir(parents=True, exist_ok=True)

        config = str(Path().absolute()) + "/config/"

        block = (
            str(Path().absolute())
            + "/"
            + str(pathchannel)
            + "/"
            + self.domain.networkname
            + ".block"
        )

        os.system(
            str(Path().absolute())
            + "/bin/configtxgen -configPath "
            + config
            + " -profile SampleAppChannelInsecureSolo -outputBlock "
            + block
            + " -channelID "
            + self.domain.networkname
        )

    def createChannel(self):
        pass

    def joinChannel(self):
        pass

    def setAnchorPeer(self):
        pass
