import json
import os
import shutil
import tarfile
import time
from pathlib import Path

import docker
from rich.console import Console

from controllers.build import Build
from models.chaincode import Chaincode
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

console = Console()
from python_on_whales import DockerClient

whales = DockerClient()
client = docker.DockerClient()


class ChaincodeDeploy:
    def __init__(self, domain: Domain, pathccsrc: str) -> None:
        self.domain: Domain = domain
        self.pathccsrc = pathccsrc
        self.chaincodename = pathccsrc.split("/")[-1]
        self.chaincodeversion = 0
        self.packageid = None

    def buildAll(self):
        console.print("[bold orange1]CHAINCODE DEPLOY[/]")
        console.print("")
        if self.buildDockerImage():
            console.print("")
            self.packageChaincode()
            console.print("")
            self.installChaincode()
            console.print("")
            self.approveOrg()
            console.print("")
            self.commitChaincodeDefinition()
            console.print("")
            self.startDockerContainer()
            console.print("")
            self.chaincodeInvokeInit()
            console.print("")

    def buildFirefly(self):
        if self.buildDockerImage():
            console.print("")
            self.packageChaincode()
            console.print("")
            self.installChaincode()
            console.print("")
            self.approveOrg()
            console.print("")
            self.commitChaincodeDefinition()
            console.print("")
            self.startDockerContainer()
            console.print("")

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
            whales.buildx.build(
                context_path=self.pathccsrc,
                file=dockerfile,
                tags=[tag],
                build_args={"CC_SERVER_PORT": 9999},
            )
            success = True

        return success

    def packageChaincode(self):
        console.print("[bold white]# Packaging chaincode[/]")
        build = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/chaincodes/build/"
        )

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
            "tls_required": False,
        }

        metadata = {"type": "ccaas", "label": self.chaincodename + "_" + str(ccversion)}

        tarcode = str(pathpkg) + "/code.tar.gz"
        tarchaincode = build + self.chaincodename + ".tar.gz"

        with open(connectionfile, "w", encoding="UTF-8") as connfile:
            json.dump(connectiondata, connfile, indent=2)

        with open(metadatafile, "w", encoding="UTF-8") as metafile:
            json.dump(metadata, metafile, indent=2)

        old_dir = os.getcwd()
        os.chdir(str(pathsrc))
        filessrc = sorted(os.listdir())
        with tarfile.open(tarcode, "w:gz") as tar:
            for filename in filessrc:
                tar.add(filename)

        os.chdir(str(pathpkg))
        filespkg = sorted(os.listdir())
        with tarfile.open(tarchaincode, "w:gz") as tar:
            for filename in filespkg:
                tar.add(filename)

        os.chdir(old_dir)

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
        self.chaincodeversion = ccversion

        if ccindex is None:
            self.domain.chaincodes.append(newcc)
        else:
            self.domain.chaincodes[ccindex] = newcc

        build = Build(self.domain)
        build.buildConfig()

    def installChaincode(self):
        console.print("[bold white]# Installing chaincode[/]")
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        buildpath = domainpath + "/chaincodes/build/"
        chaincodepkg = buildpath + self.chaincodename + ".tar.gz"
        for org in self.domain.organizations:
            for peer in org.peers:
                console.print("[bold]# Installing chaincode on " + peer.name + "[/]")
                self.peerEnvVariables(org, peer)

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
                    + "| grep ^"
                    + self.packageid
                )

                os.system(command)

                console.print("# Waiting Peer...")
                time.sleep(2)

        shutil.rmtree(buildpath)

    def approveOrg(self):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        for org in self.domain.organizations:
            for peer in org.peers:
                if peer.name.split(".")[0] == "peer1":
                    console.print(
                        "[bold]# Approving chaincode definition for " + org.name + "[/]"
                    )
                    self.peerEnvVariables(org, peer)

                    command = (
                        str(Path().absolute())
                        + "/bin/peer lifecycle chaincode approveformyorg -o localhost:"
                        + str(self.domain.orderer.generallistenport)
                        + " --ordererTLSHostnameOverride "
                        + self.domain.orderer.name
                        + "."
                        + self.domain.name
                        + " --tls --cafile "
                        + ORDERER_CA
                        + " --channelID "
                        + self.domain.networkname
                        + " --name "
                        + self.chaincodename
                        + " --version "
                        + str(self.chaincodeversion)
                        + " --package-id "
                        + self.packageid
                        + " --sequence "
                        + str(self.chaincodeversion)
                        + " --init-required"
                    )

                    if self.chaincodename == "firefly":
                        command = (
                            str(Path().absolute())
                            + "/bin/peer lifecycle chaincode approveformyorg -o localhost:"
                            + str(self.domain.orderer.generallistenport)
                            + " --ordererTLSHostnameOverride "
                            + self.domain.orderer.name
                            + "."
                            + self.domain.name
                            + " --tls --cafile "
                            + ORDERER_CA
                            + " --channelID "
                            + self.domain.networkname
                            + " --name "
                            + self.chaincodename
                            + " --version "
                            + str(self.chaincodeversion)
                            + " --package-id "
                            + self.packageid
                            + " --sequence "
                            + str(self.chaincodeversion)
                        )

                    os.system(command)
                    console.print("# Waiting Peer...")
                    time.sleep(2)
                    self.checkCommit(org, peer)

    def checkCommit(self, org: Organization, peer: Peer):
        console.print("[bold]# Checking commit[/]")
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/tlsca/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        self.peerEnvVariables(org, peer)

        command = (
            str(Path().absolute())
            + "/bin/peer lifecycle chaincode checkcommitreadiness -o localhost:"
            + str(self.domain.orderer.generallistenport)
            + " --tls --cafile "
            + ORDERER_CA
            + " --channelID "
            + self.domain.networkname
            + " --name "
            + self.chaincodename
            + " --version "
            + str(self.chaincodeversion)
            + " --sequence "
            + str(self.chaincodeversion)
            + " --init-required --output json"
        )

        os.system(command)
        time.sleep(2)

    def commitChaincodeDefinition(self):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        for org in self.domain.organizations:
            for peer in org.peers:
                if peer.name.split(".")[0] == "peer1":
                    console.print(
                        "[bold]# Commiting chaincode definition for "
                        + self.domain.networkname
                        + " by "
                        + peer.name
                        + "[/]"
                    )
                    self.peerEnvVariables(org, peer)

                    CORE_PEER_TLS_ROOTCERT_FILE = (
                        domainpath
                        + "/peerOrganizations/"
                        + org.name
                        + "/"
                        + peer.name
                        + "/tls/ca.crt"
                    )

                    command = (
                        str(Path().absolute())
                        + "/bin/peer lifecycle chaincode commit -o localhost:"
                        + str(self.domain.orderer.generallistenport)
                        + " --ordererTLSHostnameOverride "
                        + self.domain.orderer.name
                        + "."
                        + self.domain.name
                        + " --tls --cafile "
                        + ORDERER_CA
                        + " --channelID "
                        + self.domain.networkname
                        + " --name "
                        + self.chaincodename
                        + " --peerAddresses localhost:"
                        + str(peer.peerlistenport)
                        + " --tlsRootCertFiles "
                        + CORE_PEER_TLS_ROOTCERT_FILE
                        + " --version "
                        + str(self.chaincodeversion)
                        + " --sequence "
                        + str(self.chaincodeversion)
                        + " --init-required"
                    )

                    if self.chaincodename == "firefly":
                        command = (
                            str(Path().absolute())
                            + "/bin/peer lifecycle chaincode commit -o localhost:"
                            + str(self.domain.orderer.generallistenport)
                            + " --ordererTLSHostnameOverride "
                            + self.domain.orderer.name
                            + "."
                            + self.domain.name
                            + " --tls --cafile "
                            + ORDERER_CA
                            + " --channelID "
                            + self.domain.networkname
                            + " --name "
                            + self.chaincodename
                            + " --peerAddresses localhost:"
                            + str(peer.peerlistenport)
                            + " --tlsRootCertFiles "
                            + CORE_PEER_TLS_ROOTCERT_FILE
                            + " --version "
                            + str(self.chaincodeversion)
                            + " --sequence "
                            + str(self.chaincodeversion)
                        )

                    os.system(command)
                    console.print("# Waiting Peer...")
                    time.sleep(2)

    def startDockerContainer(self):
        for org in self.domain.organizations:
            for peer in org.peers:
                console.print(
                    "[bold]# Starting the CCAAS container for " + org.name + "[/]"
                )

                container = whales.run(
                    image=self.chaincodename + "_ccaas_image:latest",
                    name=peer.name.replace(".", "")
                    + "_"
                    + self.chaincodename
                    + "_ccaas",
                    hostname=peer.name.replace(".", "")
                    + "_"
                    + self.chaincodename
                    + "_ccaas",
                    networks=[self.domain.networkname],
                    envs={
                        "CHAINCODE_SERVER_ADDRESS": "0.0.0.0:9999",
                        "CHAINCODE_ID": self.packageid,
                        "CORE_CHAINCODE_ID_NAME": self.packageid,
                        "CC_SERVER_PORT":9999,
                        "CHAINCODE_TLS_DISABLED":False
                    },
                    expose=[9999],
                    publish=[(9999,9999)],
                    remove=True,
                    detach=True,
                    init=True,
                    tty=True,
                )

                console.print("# Waiting Container...")
                time.sleep(7)

    def chaincodeInvokeInit(self):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        if self.chaincodename != "firefly":
            for org in self.domain.organizations:
                for peer in org.peers:
                    if peer.name.split(".")[0] == "peer1":
                        console.print(
                            "[bold]# Commiting chaincode definition for "
                            + self.domain.networkname
                            + " by "
                            + peer.name
                            + "[/]"
                        )
                        self.peerEnvVariables(org, peer)

                        CORE_PEER_TLS_ROOTCERT_FILE = (
                            domainpath
                            + "/peerOrganizations/"
                            + org.name
                            + "/tlsca/tlsca."
                            + org.name
                            + "-cert.pem"
                        )

                        fcncall = '{"function":"InitLedger","Args":[]}'

                        command = (
                            str(Path().absolute())
                            + "/bin/peer chaincode invoke -o localhost:"
                            + str(self.domain.orderer.generallistenport)
                            + " --ordererTLSHostnameOverride "
                            + self.domain.orderer.name
                            + "."
                            + self.domain.name
                            + " --tls --cafile "
                            + ORDERER_CA
                            + " --channelID "
                            + self.domain.networkname
                            + " --name "
                            + self.chaincodename
                            + " --peerAddresses localhost:"
                            + str(peer.peerlistenport)
                            + " --tlsRootCertFiles "
                            + CORE_PEER_TLS_ROOTCERT_FILE
                            + " --isInit -c "
                            + "'"
                            + fcncall
                            + "'"
                        )

                        os.system(command)

                        console.print("# Waiting Peer...")
                        time.sleep(2)

    def peerEnvVariables(self, org: Organization, peer: Peer, ord: bool = None):
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

        ORDERER_GENERAL_LOCALMSPDIR = (
            domainpath
            + "/ordererOrganizations/users/Admin@"
            + self.domain.name
            + "/msp"
        )

        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        ORDERER_ADMIN_TLS_SIGN_CERT = (
            domainpath + "/ordererOrganizations/orderer/tls/server.crt"
        )
        ORDERER_ADMIN_TLS_PRIVATE_KEY = (
            domainpath + "/ordererOrganizations/orderer/tls/server.key"
        )

        PORT = str(peer.peerlistenport)

        os.environ["FABRIC_CFG_PATH"] = config
        os.environ["CORE_PEER_TLS_ENABLED"] = "true"
        os.environ["CORE_PEER_LOCALMSPID"] = "OrdererMSP" if ord else org.name + "MSP"
        os.environ["CORE_PEER_TLS_ROOTCERT_FILE"] = PEER_CA
        os.environ["CORE_PEER_MSPCONFIGPATH"] = (
            ORDERER_GENERAL_LOCALMSPDIR if ord else PEER_MSP
        )
        os.environ["CORE_PEER_ADDRESS"] = "localhost:" + PORT
        os.environ["ORDERER_CA"] = ORDERER_CA
        os.environ["ORDERER_ADMIN_TLS_SIGN_CERT"] = ORDERER_ADMIN_TLS_SIGN_CERT
        os.environ["ORDERER_ADMIN_TLS_PRIVATE_KEY"] = ORDERER_ADMIN_TLS_PRIVATE_KEY
