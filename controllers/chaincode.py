import json
import os
import shutil
import tarfile
import time
from pathlib import Path

import docker
import ruamel.yaml
from rich.console import Console

from controllers.build import Build
from controllers.header import Header
from helpers.commands import Commands
from helpers.paths import Paths
from models.chaincode import Chaincode
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=1)
yaml.boolean_representation = [f"false", f"true"]

console = Console()
from python_on_whales import DockerClient
from python_on_whales.components.network.cli_wrapper import Network

whales = DockerClient()
client = docker.DockerClient()

header = Header()
commands = Commands()


class ChaincodeDeploy:
    def __init__(self, domain: Domain, chaincode: Chaincode) -> None:
        self.domain: Domain = domain
        self.paths = Paths(domain)
        self.chaincode = chaincode
        self.pathccsrc = self.paths.CHAINCODEPATH + chaincode.name
        self.chaincodename = chaincode.name
        self.chaincodeversion = 0
        self.packageid = None

    def build_all(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]CHAINCODE DEPLOY[/]")
        console.print("")

        orgpkg = self.domain.organizations[0]
        peerpkg = orgpkg.peers[0]

        self.package_chaincode(orgpkg, peerpkg)
        console.print("")

        if self.build_docker_image():
            for org in self.domain.organizations:
                for peer in org.peers:
                    self.chaincode_crypto(org, peer, self.chaincode)
                    console.print("")

            for org in self.domain.organizations:
                for peer in org.peers:
                    self.install_chaincode(org, peer)
                    console.print("")

            for org in self.domain.organizations:
                for peer in org.peers:
                    self.approve_org(org, peer)
                    console.print("")

            self.commit_chaincode_definition()
            console.print("")

            for org in self.domain.organizations:
                for peer in org.peers:
                    self.start_docker_container(org, peer)
                    console.print("")

            self.chaincode_invoke_init()
            console.print("")

        shutil.rmtree(self.paths.CHAINCODEBUILDPATH)

    def build_firefly(self):
        for org in self.domain.organizations:
            for peer in org.peers:
                self.chaincode = self.package_chaincode_firefly(org, peer)
                console.print("")
                self.install_chaincode_firefly(org, peer)
                console.print("")
                self.approve_org(org, peer)
                console.print("")
                self.commit_chaincode_definition(org, peer)
                console.print("")
        shutil.rmtree(self.paths.CHAINCODEBUILDPATH)
        return self.chaincode

    def build_docker_image(self) -> bool:
        console.print("[bold white]# Building Docker Image[/]")
        console.print("")

        builded = False
        for cc in self.domain.chaincodes:
            if cc.name == self.chaincodename:
                builded = True

        if builded:
            for org in self.domain.organizations:
                for peer in org.peers:
                    self.paths.set_chaincode_paths(org, peer, self.chaincode)
                    container = whales.container.exists(self.paths.CCNAME)
                    if container:
                        whales.container.stop(
                            whales.container.inspect(self.paths.CCNAME)
                        )

            imagename = self.chaincodename + "_ccaas_image:latest"
            image = whales.image.exists(imagename)
            if image:
                whales.image.remove(
                    whales.image.inspect(imagename),
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

    def package_chaincode(self, org: Organization, peer: Peer):
        console.print("[bold white]# Packaging chaincode[/]")
        self.paths.set_org_paths(org)
        self.paths.set_peer_paths(org, peer)

        pathsrc = Path(self.paths.CHAINCODESRC)
        pathsrc.mkdir(parents=True, exist_ok=True)

        pathpkg = Path(self.paths.CHAINCODEPKG)
        pathpkg.mkdir(parents=True, exist_ok=True)

        connectionfile = self.paths.CHAINCODESRC + "/connection.json"
        metadatafile = self.paths.CHAINCODEPKG + "/metadata.json"
        ccversion = 1
        ccindex = None

        for i, cc in enumerate(self.domain.chaincodes):
            if cc.name == self.chaincodename:
                ccindex = i
                ccversion = cc.version + 1

        with open(self.paths.PEERSERVERCRT) as cert:
            certdata = cert.read()

        with open(self.paths.PEERSERVERKEY) as key:
            keydata = key.read()

        with open(self.paths.PEERCAROOT) as cacert:
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
            # "client_auth_required": False,
            # "client_key": keydata,
            # "client_cert": certdata,
            # "root_cert": carootdata,
        }

        metadata = {
            "path": "",
            "type": "ccaas",
            "label": self.chaincodename + "_" + str(ccversion),
        }

        tarcode = self.paths.CHAINCODEPKG + "code.tar.gz"
        tarchaincode = self.paths.CHAINCODEBUILDPATH + self.chaincodename + ".tar.gz"

        with open(connectionfile, "w", encoding="UTF-8") as connfile:
            json.dump(connectiondata, connfile, indent=2)

        with open(metadatafile, "w", encoding="UTF-8") as metafile:
            json.dump(metadata, metafile, indent=2)

        old_dir = os.getcwd()
        os.chdir(self.paths.CHAINCODESRC)
        filessrc = sorted(os.listdir())
        with tarfile.open(tarcode, "w:gz") as tar:
            for filename in filessrc:
                tar.add(filename)

        os.chdir(self.paths.CHAINCODEPKG)
        filespkg = sorted(os.listdir())
        with tarfile.open(tarchaincode, "w:gz") as tar:
            for filename in filespkg:
                tar.add(filename)

        os.chdir(old_dir)

        self.peer_env_variables(org, peer)

        commands.peer_lifecycle_chaincode_calculatepackageid(
            self.paths.APPPATH, tarchaincode, self.paths.CHAINCODEBUILDPATH
        )

        console.print("## Waiting Peer...")
        time.sleep(1)

        with open(
            self.paths.CHAINCODEBUILDPATH + "PACKAGEID.txt", encoding="utf-8"
        ) as f:
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
        build.build_config()

    def install_chaincode(self, org: Organization, peer: Peer):
        console.print("[bold white]# Installing chaincode[/]")

        self.paths.set_org_paths(org)
        self.paths.set_peer_paths(org, peer)

        chaincodepkg = self.paths.CHAINCODEBUILDPATH + self.chaincodename + ".tar.gz"

        console.print("[bold]# Installing chaincode on " + peer.name + "[/]")
        self.peer_env_variables(org, peer, True)

        commands.peer_lifecycle_chaincode_install(self.paths.APPPATH, chaincodepkg)

        console.print("# Waiting Peer...")
        time.sleep(1)

        console.print("[bold]# Result chaincode installation on " + peer.name + "[/]")

        commands.peer_lifecycle_chaincode_queryinstalled(
            self.paths.APPPATH, self.packageid
        )

        console.print("# Waiting Peer...")
        time.sleep(1)

    def package_chaincode_firefly(self, org: Organization, peer: Peer) -> Chaincode:
        console.print("[bold white]# Packaging chaincode[/]")

        self.paths.set_org_paths(org)
        self.paths.set_peer_paths(org, peer)

        pathpkg = Path(self.paths.CHAINCODEPKG)
        pathpkg.mkdir(parents=True, exist_ok=True)

        old_dir = os.getcwd()
        os.chdir(self.paths.FIREFLYCCPATH)
        os.system("go mod vendor")
        os.chdir(self.paths.CHAINCODEPKG)

        console.print(
            "[bold]# Generating and registering chaincode package on "
            + org.name
            + "[/]"
        )
        self.peer_env_variables(org, peer)
        commands.peer_lifecycle_chaincode_package(
            self.paths.APPPATH, self.paths.FIREFLYCCPATH, self.chaincode
        )
        os.chdir(old_dir)

        self.peer_env_variables(org, peer)

        tarchaincode = self.paths.CHAINCODEPKG + self.chaincodename + ".tar.gz"
        commands.peer_lifecycle_chaincode_calculatepackageid(
            self.paths.APPPATH, tarchaincode, self.paths.CHAINCODEPKG
        )

        with open(self.paths.CHAINCODEPKG + "PACKAGEID.txt", encoding="utf-8") as f:
            packageid = f.read().strip()

        ccversion = 1
        ccindex = None

        self.chaincode.version = ccversion
        self.chaincode.servicename = self.chaincodename  # + "_ccaas"
        self.chaincode.packageid = packageid
        self.packageid = packageid
        self.chaincodeversion = ccversion

        if ccindex is None:
            self.domain.chaincodes.append(self.chaincode)
        else:
            self.domain.chaincodes[ccindex] = self.chaincode

        build = Build(self.domain)
        build.build_config()

        console.print("# Waiting Peer...")
        time.sleep(1)
        return self.chaincode

    def install_chaincode_firefly(self, org: Organization, peer: Peer):
        console.print("[bold white]# Installing chaincode[/]")

        self.paths.set_org_paths(org)
        self.paths.set_peer_paths(org, peer)

        chaincodepkg = self.paths.CHAINCODEPKG + self.chaincodename + ".tar.gz"

        console.print("[bold]# Installing chaincode on " + peer.name + "[/]")
        self.peer_env_variables(org, peer, True)

        commands.peer_lifecycle_chaincode_install(self.paths.APPPATH, chaincodepkg)

        console.print("# Waiting Peer...")
        time.sleep(1)

        console.print("[bold]# Result chaincode installation on " + peer.name + "[/]")

        commands.peer_lifecycle_chaincode_queryinstalled(
            self.paths.APPPATH, self.packageid
        )

        console.print("# Waiting Peer...")
        time.sleep(1)

    def approve_org(self, org: Organization, peer: Peer):
        self.paths.set_org_paths(org)
        self.paths.set_peer_paths(org, peer)

        if peer.name.split(".")[0] == "peer1":
            console.print(
                "[bold]# Approving chaincode definition for " + org.name + "[/]"
            )
            self.peer_env_variables(org, peer, True)

            self.check_commit(org, peer)

            self.peer_env_variables(org, peer, True)

            commands.peer_lifecycle_chaincode_approveformyorg(
                self.paths.APPPATH,
                self.chaincode.invoke,
                self.domain.orderer,
                self.paths.ORDERERNAME,
                self.paths.ORDTLSCAPATH + "tls-cert.pem",
                self.domain.networkname,
                self.chaincodename,
                self.chaincodeversion,
                self.packageid,
            )

            console.print("# Waiting Peer...")
            time.sleep(1)
            self.peer_env_variables(org, peer, True)
            self.check_commit(org, peer)

    def check_commit(self, org: Organization, peer: Peer):
        console.print("[bold]# Checking commit[/]")

        self.peer_env_variables(org, peer, True)

        commands.peer_lifecycle_chaincode_checkcommitreadiness(
            self.paths.APPPATH,
            self.chaincode.invoke,
            self.domain.orderer,
            self.paths.ORDERERNAME,
            self.paths.ORDTLSCAPATH + "tls-cert.pem",
            self.domain.networkname,
            self.chaincodename,
            self.chaincodeversion,
        )
        time.sleep(1)

    def commit_chaincode_definition(self):
        org = self.domain.organizations[0]
        peer = org.peers[0]

        console.print("[bold]# Commiting chaincode definition[/]")
        self.peer_env_variables(org, peer, True)

        commands.peer_lifecycle_chaincode_commit(
            self.paths.APPPATH,
            self.chaincode.invoke,
            self.domain.orderer,
            self.paths.ORDERERNAME,
            self.paths.ORDTLSCAPATH + "tls-cert.pem",
            self.domain.networkname,
            self.chaincodename,
            self.domain,
            self.chaincodeversion,
        )

        console.print("# Waiting Peer...")
        time.sleep(1)

    def start_docker_container(self, org: Organization, peer: Peer):
        console.print("[bold]# Starting the CCAAS container[/]")
        self.paths.set_chaincode_paths(org, peer, self.chaincode)

        volumes = [
            (self.paths.CCPATH, "/etc/hyperledger/chaincode/"),
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
            "CORE_PEER_TLS_ENABLED": str(self.chaincode.usetls).lower(),
            "CORE_PEER_CHAINCODEADDRESS": peer.name
            + "."
            + self.domain.name
            + ":"
            + str(peer.chaincodelistenport),
            "CORE_PEER_TLS_ROOTCERT_FILE": "/etc/hyperledger/chaincode/tls/tlscacerts/tlsca-cert.pem",
            "CORE_TLS_CLIENT_CERT_PATH": "/etc/hyperledger/chaincode/tls/signcerts/cert.crt",
            "CORE_TLS_CLIENT_KEY_PATH": "/etc/hyperledger/chaincode/tls/keystore/key.pem",
            "CORE_TLS_CLIENT_CERT_FILE": "/etc/hyperledger/chaincode/tls/signcerts/cert.crt",
            "CORE_TLS_CLIENT_KEY_FILE": "/etc/hyperledger/chaincode/tls/keystore/key.pem",
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
            # expose=[self.chaincode.ccport],
            # publish=[(self.chaincode.ccport, self.chaincode.ccport)],
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

        # Waiting Peer Container
        # console.print("# Waiting Peer Container...")
        # peercontainer = whales.container.inspect(peer.name + "." + self.domain.name)
        # whales.container.restart(peercontainer)
        # time.sleep(1)

    def chaincode_invoke_init(self):
        org = self.domain.organizations[0]
        peer = org.peers[0]

        console.print("[bold]# Invoking chaincode[/]")
        self.peer_env_variables(org, peer, True)

        commands.peer_chaincode_invoke(
            self.paths.APPPATH,
            self.chaincode.invoke,
            self.domain.orderer,
            self.paths.ORDERERNAME,
            self.paths.ORDTLSCAPATH + "tls-cert.pem",
            self.domain.networkname,
            self.chaincodename,
            self.domain,
        )

        console.print("# Waiting Peer...")
        time.sleep(1)

    def chaincode_crypto(self, org: Organization, peer: Peer, chaincode: Chaincode):
        console.print("[bold]## Registering chaincode " + chaincode.name + " crypto[/]")

        self.paths.set_org_paths(org)
        self.paths.set_peer_paths(org, peer)
        self.paths.set_chaincode_paths(org, peer, self.chaincode)
        self.peer_env_variables(org, peer)

        pathcc = Path(self.paths.PEERPATH + chaincode.name)

        if pathcc.is_dir():
            shutil.rmtree(str(pathcc))

        if not pathcc.is_dir():
            pathcc.mkdir(parents=True, exist_ok=True)

        console.print("[bold]## Registering TLS CA Admin Chaincode[/]")

        commands.enroll(
            self.paths.APPPATH,
            self.paths.CACLIENTDOMAINPATH,
            "admin",
            "adminpw",
            self.domain.ca.serverport,
            self.paths.CACERTDOMAINFILE,
        )
        commands.register_peer(
            self.paths.APPPATH,
            self.paths.CACLIENTDOMAINPATH,
            self.chaincode.name,
            self.chaincode.name + "pw",
            self.domain.ca.serverport,
            self.paths.TLSCERTDOMAINFILE,
        )

        console.print("[bold]## Register Org CA Admin :: Chaincode[/]")
        commands.enroll(
            self.paths.APPPATH,
            self.paths.CAORGCACLIENTPATH,
            "admin",
            "adminpw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        commands.register_peer(
            self.paths.APPPATH,
            self.paths.CAORGCACLIENTPATH,
            self.chaincode.name,
            self.chaincode.name + "pw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        msppath = str(pathcc) + "/msp/"
        tlspath = str(pathcc) + "/tls/"

        console.print("[bold]## Generating the chaincode-msp certificates[/]")

        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.PEERPATH + chaincode.name,
            self.chaincode.name,
            self.chaincode.name + "pw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        console.print("[bold]## Generating the chaincode-tls certificates[/]")

        commands.enroll_tls(
            self.paths.APPPATH,
            self.paths.PEERPATH + chaincode.name,
            "admin",
            "adminpw",
            self.domain.ca.serverport,
            [self.paths.CCNAME, self.paths.CCSMALLNAME, "localhost"],
            peer.name + "." + self.domain.name,
            self.paths.TLSCERTDOMAINFILE,
        )

        admincerts = Path(msppath + "admincerts")
        admincerts.mkdir(parents=True, exist_ok=True)
        tlscacerts = Path(msppath + "tlscacerts")
        tlscacerts.mkdir(parents=True, exist_ok=True)

        # TLS
        shutil.copy(
            tlspath + "signcerts/cert.pem",
            tlspath + "signcerts/cert.crt",
        )

        for file_name in os.listdir(tlspath + "tlscacerts/"):
            shutil.copy(
                tlspath + "tlscacerts/" + file_name,
                tlspath + "tlscacerts/tlsca-cert.pem",
            )

            shutil.copy(
                tlspath + "tlscacerts/" + file_name,
                msppath + "tlscacerts/tlsca-cert.pem",
            )

        for file_name in os.listdir(tlspath + "keystore/"):
            shutil.copy(
                tlspath + "keystore/" + file_name,
                tlspath + "keystore/key.pem",
            )

        # MSP
        shutil.copy(
            self.paths.ORGSIGNCERTPATH + "cert.pem",
            msppath + "admincerts/cert.pem",
        )

    def peer_env_variables(
        self, org: Organization, peer: Peer, orgadm: bool = None, ord: bool = None
    ):
        self.paths.set_org_paths(org)
        self.paths.set_peer_paths(org, peer)

        os.environ["FABRIC_CFG_PATH"] = self.paths.PEERCFGPATH
        os.environ["CORE_PEER_TLS_ENABLED"] = "true"
        os.environ["CORE_PEER_LOCALMSPID"] = "OrdererMSP" if ord else org.name + "MSP"
        os.environ["CORE_PEER_TLS_ROOTCERT_FILE"] = self.paths.PEERCAROOT
        os.environ["CORE_PEER_MSPCONFIGPATH"] = (
            self.paths.ORGMSPPATH
            if orgadm
            else self.paths.ORDERERORGMSPPATH
            if ord
            else self.paths.PEERMSPPATH  # ORGMSPPATH
        )
        os.environ["CORE_PEER_ADDRESS"] = "localhost:" + str(peer.peerlistenport)
        os.environ["ORDERER_CA"] = self.paths.ORDTLSCAPATH + "tls-cert.pem"
        os.environ["ORDERER_ADMIN_TLS_SIGN_CERT"] = (
            self.paths.ORDSIGNCERTPATH + "cert.crt"
        )
        os.environ["ORDERER_ADMIN_TLS_PRIVATE_KEY"] = (
            self.paths.ORDKEYSTOREPATH + "key.pem"
        )
