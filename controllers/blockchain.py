import os
import shutil
import time
from pathlib import Path

import ruamel.yaml
from rich.console import Console

from models.domain import Domain

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=1)
yaml.boolean_representation = [f"false", f"true"]
console = Console()


class Blockchain:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        console.print("[bold white]# Creating genesis block[/]")
        console.print("")
        self.genesisBlock()
        console.print("")
        console.print("[bold white]# Creating channel[/]")
        console.print("")
        self.createChannel()
        console.print("")
        console.print("[bold white]# Joinning channel[/]")
        console.print("")
        self.joinChannel()
        console.print("")
        console.print("[bold white]# Setting anchor peers[/]")
        console.print("")
        self.setAnchorPeer()
        console.print("")

    def genesisBlock(self):
        # Preparing configtx
        config = str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"
        pathconfig = Path(config)
        pathconfig.mkdir(parents=True, exist_ok=True)

        origconfig = str(Path().absolute()) + "/config/configtx.yaml"

        shutil.copy(
            origconfig,
            config + "/configtx.yaml",
        )

        with open(config + "/configtx.yaml") as cftx:
            datacfg = yaml.load(cftx)

        datacfg["Organizations"][0]["MSPDir"] = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + "msp"
        )
        datacfg["Organizations"][0]["OrdererEndpoints"] = [
            self.domain.orderer.name
            + "."
            + self.domain.name
            + ":"
            + str(self.domain.orderer.generallistenport)
        ]
        datacfg["Orderer"]["OrdererType"] = "etcdraft"
        datacfg["Orderer"]["Addresses"] = [
            self.domain.orderer.name
            + "."
            + self.domain.name
            + ":"
            + str(self.domain.orderer.generallistenport)
        ]
        datacfg["Orderer"]["EtcdRaft"]["Consenters"] = [
            {
                "Host": (self.domain.orderer.name + "." + self.domain.name),
                "Port": self.domain.orderer.generallistenport,
                "ClientTLSCert": (
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/ordererOrganizations/"
                    + self.domain.orderer.name
                    + "/tls/server.crt"
                ),
                "ServerTLSCert": (
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/ordererOrganizations/"
                    + self.domain.orderer.name
                    + "/tls/server.crt"
                ),
            },
        ]

        with open(config + "/configtx.yaml", "w") as cftx:
            yaml.dump(datacfg, cftx)

        # Creating gblock
        pathchannel = Path("domains/" + self.domain.name + "/channel-artifacts")
        pathchannel.mkdir(parents=True, exist_ok=True)

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
            + " -profile SampleAppChannelEtcdRaft -outputBlock "
            + block
            + " -channelID "
            + self.domain.networkname
        )

    def createChannel(self):
        config = str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"
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

        console.print("## Waiting Orderer...")
        time.sleep(5)

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
        pathchannel = Path("domains/" + self.domain.name + "/channel-artifacts")
        block = (
            str(Path().absolute())
            + "/"
            + str(pathchannel)
            + "/"
            + self.domain.networkname
            + ".block"
        )

        os.environ["BLOCKFILE"] = block

        for org in self.domain.organizations:
            for peer in org.peers:
                config = (
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/"
                    + peer.name
                    + "/peercfg"
                )

                PEER_CA = (
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/tlsca"
                    + "/tlsca."
                    + org.name
                    + "-cert.pem"
                )

                PEER_MSP = (
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/users"
                    + "/Admin@"
                    + org.name
                    + "."
                    + self.domain.name
                    + "/msp"
                )

                os.environ["FABRIC_CFG_PATH"] = config
                os.environ["CORE_PEER_TLS_ENABLED"] = "true"
                os.environ["CORE_PEER_LOCALMSPID"] = org.name + "MSP"
                os.environ["CORE_PEER_TLS_ROOTCERT_FILE"] = PEER_CA
                os.environ["CORE_PEER_MSPCONFIGPATH"] = PEER_MSP
                os.environ["CORE_PEER_ADDRESS"] = "localhost:" + str(
                    peer.peerlistenport
                )

                console.print(
                    "## Peer "
                    + peer.name
                    + " Address: "
                    + os.environ["CORE_PEER_ADDRESS"]
                )

                console.print("## Waiting Peer...")
                time.sleep(5)

                os.system(str(Path().absolute()) + "/bin/peer channel join -b " + block)

    def setAnchorPeer(self):
        pass
