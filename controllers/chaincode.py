import json
import os
import shutil
import tarfile
import time
from pathlib import Path

import docker
from rich.console import Console

from controllers.build import Build
from controllers.header import Header
from models.chaincode import Chaincode
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

console = Console()
from python_on_whales import DockerClient
from python_on_whales.components.network.cli_wrapper import Network

whales = DockerClient()
client = docker.DockerClient()

header = Header()


class ChaincodeDeploy:
    def __init__(self, domain: Domain, chaincode: Chaincode) -> None:
        self.domain: Domain = domain
        self.chaincode = chaincode
        self.pathccsrc = "".join(
            [str(Path().absolute()), "/chaincodes/", chaincode.name]
        )
        self.chaincodename = chaincode.name
        self.chaincodeversion = 0
        self.packageid = None

    def buildAll(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]CHAINCODE DEPLOY[/]")
        console.print("")

        if self.buildDockerImage():
            for org in self.domain.organizations:
                for peer in org.peers:
                    self.chaincodeCrypto(org, peer, self.chaincode)
                    console.print("")
                    self.packageChaincode(org, peer)
                    console.print("")
                    self.installChaincode(org, peer)
                    console.print("")
                    self.approveOrg(org, peer)
                    console.print("")
                    self.commitChaincodeDefinition(org, peer)
                    console.print("")
                    self.startDockerContainer(org, peer)
                    console.print("")
                    self.chaincodeInvokeInit(org, peer)
                    console.print("")
            self.removeccbuild()

    def buildFirefly(self):
        if self.buildDockerImage():
            for org in self.domain.organizations:
                for peer in org.peers:
                    self.chaincodeCrypto(org, peer, self.chaincode)
                    console.print("")
                    self.packageChaincode(org, peer)
                    console.print("")
                    self.installChaincode(org, peer)
                    console.print("")
                    self.approveOrg(org, peer)
                    console.print("")
                    self.startDockerContainer(org, peer)
                    console.print("")
                    self.commitChaincodeDefinition(org, peer)
                    console.print("")
            self.removeccbuild()

    def buildDockerImage(self) -> bool:
        console.print("[bold white]# Building Docker Image[/]")
        console.print("")

        builded = False
        for cc in self.domain.chaincodes:
            if cc.name == self.chaincodename:
                builded = True

        if builded:
            for org in self.domain.organizations:
                for peer in org.peers:
                    container = whales.container.exists(
                        peer.name.replace(".", "")
                        + "."
                        + self.chaincodename
                        + ".ccaas."
                        + self.domain.name
                    )
                    if container:
                        whales.container.stop(
                            whales.container.inspect(
                                peer.name.replace(".", "")
                                + "."
                                + self.chaincodename
                                + ".ccaas."
                                + self.domain.name
                            )
                        )

            image = whales.image.exists(self.chaincodename + "_ccaas_image:latest")
            if image:
                whales.image.remove(
                    whales.image.inspect(self.chaincodename + "_ccaas_image:latest"),
                    True,
                )

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
                build_args={"CC_SERVER_PORT": self.chaincode.ccport},
            )
            success = True

        return success

    def packageChaincode(self, org: Organization, peer: Peer):
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

        cccryptopath = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
        )

        with open(cccryptopath + "/tls/server.crt") as cert:
            certdata = cert.read()

        with open(cccryptopath + "/tls/server.key") as key:
            keydata = key.read()

        with open(cccryptopath + "/" + self.chaincodename + "/tls/ca.crt") as cacert:
            carootdata = cacert.read()

        peername = "{{{{{peername}}}}}".format(peername=".peername")

        connectiondata = {
            "address": peername
            + "."
            + self.chaincodename
            + ".ccaas."
            + self.domain.name
            + ":"
            + str(self.chaincode.ccport),
            "dial_timeout": "30s",
            "tls_required": self.chaincode.usetls,
            "client_auth_required": False,
            "client_key": keydata,
            "client_cert": certdata,
            "root_cert": carootdata,
        }

        metadata = {
            "path": "",
            "type": "ccaas",
            "label": self.chaincodename + "_" + str(ccversion),
        }

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

        self.chaincode.version = ccversion
        self.chaincode.servicename = self.chaincodename + "_ccaas"
        self.chaincode.packageid = packageid
        self.chaincode.client_key = keydata
        self.chaincode.client_cert = certdata
        self.chaincode.root_cert = carootdata
        self.packageid = packageid
        self.chaincodeversion = ccversion

        if ccindex is None:
            self.domain.chaincodes.append(self.chaincode)
        else:
            self.domain.chaincodes[ccindex] = self.chaincode

        build = Build(self.domain)
        build.buildConfig()

    def installChaincode(self, org: Organization, peer: Peer):
        console.print("[bold white]# Installing chaincode[/]")
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        buildpath = domainpath + "/chaincodes/build/"
        chaincodepkg = buildpath + self.chaincodename + ".tar.gz"

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

        console.print("[bold]# Result chaincode installation on " + peer.name + "[/]")

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

        # shutil.rmtree(buildpath)

    def approveOrg(self, org: Organization, peer: Peer):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        initrequired = ""
        if self.chaincode.invoke:
            initrequired = " --init-required"

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
                + initrequired
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

        initrequired = ""
        if self.chaincode.invoke:
            initrequired = " --init-required"

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
            + " --output json"
            + initrequired
        )

        os.system(command)
        time.sleep(2)

    def commitChaincodeDefinition(self, org: Organization, peer: Peer):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        initrequired = ""
        if self.chaincode.invoke:
            initrequired = " --init-required"

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
                + initrequired
            )

            os.system(command)
            console.print("# Waiting Peer...")
            time.sleep(2)

    def startDockerContainer(self, org: Organization, peer: Peer):
        console.print("[bold]# Starting the CCAAS container[/]")

        pathcc = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/"
            + self.chaincode.name
        )

        volumes = [
            (pathcc, "/etc/hyperledger/chaincode/"),
        ]

        envs = {
            "CC_SERVER_PORT": self.chaincode.ccport,
            "CORE_PEER_ADDRESS": peer.name
            + "."
            + self.domain.name
            + ":"
            + str(peer.peerlistenport),
            "CHAINCODE_SERVER_ADDRESS": "0.0.0.0:" + str(self.chaincode.ccport),
            "CORE_CHAINCODE_ID_NAME": self.packageid,
            # "CORE_PEER_TLS_ENABLED": self.chaincode.usetls,
            "CORE_PEER_TLS_ENABLED": True,
            "CORE_PEER_CHAINCODEADDRESS": peer.name
            + "."
            + self.domain.name
            + ":"
            + str(peer.chaincodelistenport),
            "CORE_PEER_TLS_ROOTCERT_FILE": "/etc/hyperledger/chaincode/tls/ca.crt",
            "CORE_TLS_CLIENT_CERT_PATH": "/etc/hyperledger/chaincode/tls/server.crt",
            "CORE_TLS_CLIENT_KEY_PATH": "/etc/hyperledger/chaincode/tls/server.key",
            "CORE_TLS_CLIENT_CERT_FILE": "/etc/hyperledger/chaincode/msp/client_pem.crt",
            "CORE_TLS_CLIENT_KEY_FILE": "/etc/hyperledger/chaincode/msp/client_pem.key",
            "CORE_PEER_LOCALMSPID": org.name + "MSP",
            "CORE_PEER_MSPCONFIGPATH": "/etc/hyperledger/chaincode/msp",
            "CORE_CHAINCODE_LOGGING_LEVEL": "info",
            "CORE_CHAINCODE_LOGGING_SHIM": "warn",
            "HOSTNAME": peer.name.replace(".", "")
            + "."
            + self.chaincodename
            + ".ccaas."
            + self.domain.name,
        }

        pathnet = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-net-" + peer.name + ".yaml",
            ]
        )

        clientconfig = DockerClient(compose_files=[pathnet]).client_config
        network = Network(clientconfig, self.domain.networkname)

        # Waiting Chaincode Container
        container = whales.run(
            image=self.chaincodename + "_ccaas_image:latest",
            name=peer.name.replace(".", "")
            + "."
            + self.chaincodename
            + ".ccaas."
            + self.domain.name,
            hostname=peer.name.replace(".", "")
            + "."
            + self.chaincodename
            + ".ccaas."
            + self.domain.name,
            networks=[network],
            envs=envs,
            expose=[self.chaincode.ccport],
            publish=[(self.chaincode.ccport, self.chaincode.ccport)],
            remove=True,
            detach=True,
            init=True,
            tty=True,
            volumes=volumes,
            user="root:root",
            log_driver="syslog",
        )

        console.print("# Waiting Chaincode Container...")
        time.sleep(2)
        whales.container.pause(container)

        # Waiting Peer Container
        console.print("# Waiting Peer Container...")
        peercontainer = whales.container.inspect(peer.name + "." + self.domain.name)
        whales.container.restart(peercontainer)
        time.sleep(1)

        whales.container.unpause(container)

    def chaincodeInvokeInit(self, org: Organization, peer: Peer):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        ORDERER_CA = (
            domainpath
            + "/ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        initrequired = ""
        if self.chaincode.invoke:
            fcncall = '{"function":"InitLedger","Args":[]}'
            initrequired = " --isInit -c " + "'" + fcncall + "'"

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
                    + initrequired
                )

                os.system(command)

                console.print("# Waiting Peer...")
                time.sleep(2)

    def chaincodeCrypto(self, org: Organization, peer: Peer, chaincode: Chaincode):
        console.print("[bold]## Registering chaincode " + chaincode.name + " crypto[/]")

        chaincodehost = (
            peer.name.replace(".", "")
            + "."
            + chaincode.name
            + ".ccaas."
            + self.domain.name
        )

        pathcc = Path(
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/"
            + chaincode.name
        )

        if not pathcc.is_dir():
            pathcc.mkdir(parents=True, exist_ok=True)

            pathfabriccaorg = (
                str(Path().absolute())
                + "/domains/"
                + self.domain.name
                + "/fabric-ca/"
                + org.ca.name
                + "/ca-cert.pem"
            )

            pathorg = (
                str(Path().absolute())
                + "/domains/"
                + self.domain.name
                + "/peerOrganizations/"
                + org.name
            )

            os.environ["FABRIC_CA_CLIENT_HOME"] = str(pathorg)

            os.system(
                str(Path().absolute())
                + "/bin/fabric-ca-client register "
                + " --caname "
                + org.ca.name
                + "."
                + self.domain.name
                + " --id.name "
                + peer.name.replace(".", "")
                + "."
                + chaincode.name
                + ".ccaas"
                + " --id.secret chaincodepw"
                + " --tls.certfiles "
                + pathfabriccaorg
            )

            msppath = str(pathcc) + "/msp"
            tlspath = str(pathcc) + "/tls"

            console.print("[bold]## Generating the chaincode-msp certificates[/]")
            os.system(
                str(Path().absolute())
                + "/bin/fabric-ca-client enroll "
                + " -u https://"
                + peer.name.replace(".", "")
                + "."
                + chaincode.name
                + ".ccaas:chaincodepw@localhost:"
                + str(org.ca.serverport)
                + " --caname "
                + org.ca.name
                + "."
                + self.domain.name
                + " -M "
                + str(msppath)
                + " --csr.cn "
                + chaincodehost
                + " --csr.hosts "
                + chaincodehost
                + ","
                + peer.name.replace(".", "")
                + "."
                + chaincode.name
                + ".ccaas"
                + ",localhost"
                + " --tls.certfiles "
                + pathfabriccaorg
            )

            console.print("[bold]## Generating the chaincode-tls certificates[/]")
            os.system(
                str(Path().absolute())
                + "/bin/fabric-ca-client enroll "
                + " -u https://"
                + peer.name.replace(".", "")
                + "."
                + chaincode.name
                + ".ccaas:chaincodepw@localhost:"
                + str(org.ca.serverport)
                + " --caname "
                + org.ca.name
                + "."
                + self.domain.name
                + " -M "
                + str(tlspath)
                + " --csr.cn "
                + chaincodehost
                + " --enrollment.profile tls --csr.hosts "
                + chaincodehost
                + ","
                + peer.name.replace(".", "")
                + "."
                + chaincode.name
                + ".ccaas"
                + ",localhost"
                + " --tls.certfiles "
                + pathfabriccaorg
            )

            shutil.copy(
                str(tlspath) + "/signcerts/cert.pem",
                str(tlspath) + "/server.crt",
            )

            for file_name in os.listdir(str(tlspath) + "/tlscacerts/"):
                shutil.copy(
                    str(tlspath) + "/tlscacerts/" + file_name,
                    str(tlspath) + "/ca.crt",
                )

            for file_name in os.listdir(str(tlspath) + "/keystore/"):
                shutil.copy(
                    str(tlspath) + "/keystore/" + file_name,
                    str(tlspath) + "/server.key",
                )

            shutil.copy(
                str(msppath) + "/signcerts/cert.pem",
                str(msppath) + "/client_pem.crt",
            )

            for file_name in os.listdir(str(msppath) + "/keystore/"):
                shutil.copy(
                    str(msppath) + "/keystore/" + file_name,
                    str(msppath) + "/client_pem.key",
                )

    def removeccbuild(self):
        domainpath = str(Path().absolute()) + "/domains/" + self.domain.name
        buildpath = domainpath + "/chaincodes/build/"
        shutil.rmtree(buildpath)

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
