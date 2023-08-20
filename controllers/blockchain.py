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
        # Preparing configtx

        # Creating gblock
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
            + " -profile TwoOrgsApplicationGenesis -outputBlock "
            + block
            + " -channelID "
            + self.domain.networkname
        )

    def createChannel(self):
        config = str(Path().absolute()) + "/config/"
        pathchannel = Path("domains/" + self.domain.name + "/channel-artifacts")
        block = (
            str(Path().absolute())
            + "/"
            + str(pathchannel)
            + "/"
            + self.domain.networkname
            + ".block"
        )
        os.environ["FABRIC_CFG_PATH"] = config
        os.environ["BLOCKFILE"] = block

        ORDERER_CA = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/tlsca/tlsca."
            + self.domain.name
            + "-cert.pem"
        )
        ORDERER_ADMIN_TLS_SIGN_CERT = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
            + "/tls/server.crt"
        )
        ORDERER_ADMIN_TLS_PRIVATE_KEY = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
            + "/tls/server.key"
        )

        os.system(
            str(Path().absolute())
            + "/bin/osnadmin channel join --channelID "
            + self.domain.networkname
            + " --config-block "
            + block
            + " -o localhost:"
            + str(self.domain.orderer.adminlistenport)
            + " --ca-file '"
            + ORDERER_CA
            + "' --client-cert '"
            + ORDERER_ADMIN_TLS_SIGN_CERT
            + "' --client-key '"
            + ORDERER_ADMIN_TLS_PRIVATE_KEY
            + "'"
        )

    def joinChannel(self):
        pass

    def setAnchorPeer(self):
        pass
