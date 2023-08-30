import json
import os
import tarfile
import time
from pathlib import Path

from rich.console import Console

from controllers.build import Build
from models.chaincode import Chaincode
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

console = Console()
from python_on_whales import DockerClient

docker = DockerClient()


class ChaincodeDeploy:
    def __init__(self, domain: Domain, pathccsrc: str) -> None:
        self.domain: Domain = domain
        self.pathccsrc = pathccsrc
        self.chaincodename = pathccsrc.split("/")[-1]
        self.packageid = None

    def buildAll(self):
        console.print("[bold orange1]CHAINCODE DEPLOY[/]")
        console.print("")
        if self.buildDockerImage():
            console.print("")
            self.packageChaincode()
            console.print("")
            self.installChaincode()

    def buildDockerImage(self) -> bool:
        console.print("[bold white]# Building Docker Image[/]")
        console.print("")

        success = False

        dockerfile = self.pathccsrc + "/Dockerfile"
        tag = self.chaincodename + "_ccaas_image:latest"

        if not os.path.isfile(dockerfile):
            console.print("## Dockerfile not found!")
            while True:
                console.input("Press ENTER to exit.")
                break
        else:
            docker.buildx.build(
                context_path=self.pathccsrc,
                file=dockerfile,
                tags=[tag],
                build_args={"CC_SERVER_PORT": 9999},
            )
            success = True

        return success

    def packageChaincode(self):
        console.print("[bold white]# Packaging chaincode[/]")
        build = str(Path().absolute()) + "/chaincodes/build/"

        pathsrc = Path(build + "src/")
        pathsrc.mkdir(parents=True, exist_ok=True)

        pathpkg = Path(build + "pkg/")
        pathpkg.mkdir(parents=True, exist_ok=True)

        connectionfile = str(pathsrc) + "/connection.json"
        metadatafile = str(pathpkg) + "/metadata.json"
        ccversion = 1
        ccindex = None

        for i, cc in enumerate(self.domain.chaincodes):
            if cc.name == self.chaincodename:
                ccindex = i
                ccversion = cc.version + 1

        peername = "{{{{{peername}}}}}".format(peername=".peername")
        connectiondata = {
            "address": peername + "_" + self.chaincodename + "_ccaas:9999",
            "dial_timeout": "10s",
            "tls_required": "false",
        }

        metadata = {"type": "ccaas", "label": self.chaincodename + "_" + str(ccversion)}

        tarcode = str(pathpkg) + "/code.tar.gz"
        tarchaincode = build + self.chaincodename + ".tar.gz"

        with open(connectionfile, "w", encoding="UTF-8") as connfile:
            json.dump(connectiondata, connfile, indent=2)

        with open(metadatafile, "w", encoding="UTF-8") as metafile:
            json.dump(metadata, metafile, indent=2)

        with tarfile.open(tarcode, "w:gz") as tar:
            tar.add(str(pathsrc), arcname="connection.json")

        with tarfile.open(tarchaincode, "w:gz") as tar:
            tar.add(tarcode, arcname="code.tar.gz")
            tar.add(metadatafile, arcname="metadata.json")

        org = self.domain.organizations[0]
        peer = org.peers[0]

        self.peerEnvVariables(org, peer)

        os.system(
            str(Path().absolute())
            + "/bin/peer lifecycle chaincode calculatepackageid "
            + tarchaincode
            + " > "
            + build
            + "PACKAGEID.txt"
        )

        console.print("## Waiting Peer...")
        time.sleep(5)

        with open(build + "PACKAGEID.txt", encoding="utf-8") as f:
            packageid = f.read().strip()

        newcc = Chaincode()
        newcc.name = self.chaincodename
        newcc.version = ccversion
        newcc.packageid = packageid
        self.packageid = packageid

        if ccindex is None:
            self.domain.chaincodes.append(newcc)
        else:
            self.domain.chaincodes[ccindex] = newcc

        build = Build(self.domain)
        build.buildConfig()

    def installChaincode(self):
        console.print("[bold white]# Installing chaincode[/]")
        chaincodepkg = (
            str(Path().absolute())
            + "/chaincodes/build/"
            + self.chaincodename
            + ".tar.gz"
        )
        for org in self.domain.organizations:
            peer = org.peers[0]
            console.print("[bold]# Installing chaincode on " + peer.name + "[/]")
            self.peerEnvVariables(org, peer)

            command = (
                str(Path().absolute())
                + "/bin/peer lifecycle chaincode queryinstalled --output json "
                + "| jq -r 'try (.installed_chaincodes[].package_id)' "
                + "| grep ^$"
                + self.packageid
                + "$"
            )
            os.system(command)

            console.print("# Waiting Peer...")
            time.sleep(2)

            command = (
                str(Path().absolute())
                + "/bin/peer lifecycle chaincode install "
                + chaincodepkg
            )

            os.system(command)

            console.print("# Waiting Peer...")
            time.sleep(2)

            console.print(
                "[bold]# Result chaincode installation on " + peer.name + "[/]"
            )

            command = (
                str(Path().absolute())
                + "/bin/peer lifecycle chaincode queryinstalled --output json "
                + "| jq -r 'try (.installed_chaincodes[].package_id)'"
                + "| grep ^$"
                + self.packageid
                + "$"
            )

            os.system(command)

            console.print("# Waiting Peer...")
            time.sleep(2)

    def peerEnvVariables(self, org: Organization, peer: Peer):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name

        config = (
            domainpath + "/peerOrganizations/" + org.name + "/" + peer.name + "/peercfg"
        )

        PEER_CA = (
            domainpath
            + "/peerOrganizations/"
            + org.name
            + "/tlsca"
            + "/tlsca."
            + org.name
            + "-cert.pem"
        )

        PEER_MSP = (
            domainpath
            + "/peerOrganizations/"
            + org.name
            + "/users"
            + "/Admin@"
            + org.name
            + "."
            + self.domain.name
            + "/msp"
        )

        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/tlsca/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        ORDERER_ADMIN_TLS_SIGN_CERT = (
            domainpath + "/ordererOrganizations/orderer/tls/server.crt"
        )
        ORDERER_ADMIN_TLS_PRIVATE_KEY = (
            domainpath + "/ordererOrganizations/orderer/tls/server.key"
        )

        os.environ["FABRIC_CFG_PATH"] = config
        os.environ["CORE_PEER_TLS_ENABLED"] = "true"
        os.environ["CORE_PEER_LOCALMSPID"] = org.name + "MSP"
        os.environ["CORE_PEER_TLS_ROOTCERT_FILE"] = PEER_CA
        os.environ["CORE_PEER_MSPCONFIGPATH"] = PEER_MSP
        os.environ["CORE_PEER_ADDRESS"] = "localhost:" + str(peer.peerlistenport)
        os.environ["ORDERER_CA"] = ORDERER_CA
        os.environ["ORDERER_ADMIN_TLS_SIGN_CERT"] = ORDERER_ADMIN_TLS_SIGN_CERT
        os.environ["ORDERER_ADMIN_TLS_PRIVATE_KEY"] = ORDERER_ADMIN_TLS_PRIVATE_KEY
