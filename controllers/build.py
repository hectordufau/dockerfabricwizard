import json
import os
import shutil
from pathlib import Path

import ruamel.yaml
from python_on_whales import docker
from rich.console import Console
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from controllers.header import Header
from controllers.run import Run
from helpers.commands import Commands
from helpers.paths import Paths
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=2)
yaml.boolean_representation = [f"false", f"true"]
console = Console()
header = Header()
commands = Commands()


class Build:
    def __init__(self, domain: Domain, paths: Paths) -> None:
        self.domain: Domain = domain
        self.paths = paths

    def build_all(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]BUILD[/]")
        console.print("")
        self.build_ca()
        self.build_identities()
        self.build_orderer()
        self.build_peers_databases()
        self.prepare_firefly()
        self.build_config()
        self.starting_opd()
        console.print("")

    def build_config(self):
        console.print("[bold white]# Creating domain config file[/]")
        pathdomains = str(Path().absolute()) + "/domains/" + self.domain.name

        json_object = json.dumps(self.domain, default=lambda x: x.__dict__, indent=4)
        with open(pathdomains + "/setup.json", "w", encoding="utf-8") as outfile:
            outfile.write(json_object)

    def build_ca(self):
        console.print("[bold white]# Building and starting CAs[/]")

        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
        }

        caorderer = {
            "hostname": self.domain.ca.FABRIC_CA_SERVER_CA_NAME
            + "."
            + self.domain.name,
            "image": "hyperledger/fabric-ca:latest",
            "user": str(os.geteuid()) + ":" + str(os.getgid()),
            "labels": {"service": "hyperledger-fabric"},
            "environment": [
                "FABRIC_CA_HOME=" + self.domain.ca.FABRIC_CA_HOME,
                "FABRIC_CA_SERVER_CA_NAME="
                + self.domain.ca.FABRIC_CA_SERVER_CA_NAME
                + "."
                + self.domain.name,
                "FABRIC_CA_SERVER_CSR_CN="
                + self.domain.ca.name
                + "."
                + self.domain.name,
                "FABRIC_CA_SERVER_CSR_HOSTS="
                + self.domain.ca.name
                + "."
                + self.domain.name
                + ","
                + self.domain.ca.name
                + ",localhost",
                "FABRIC_CA_SERVER_TLS_ENABLED="
                + str(self.domain.ca.FABRIC_CA_SERVER_TLS_ENABLED).lower(),
                "FABRIC_CA_SERVER_PORT=" + str(self.domain.ca.FABRIC_CA_SERVER_PORT),
                "FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS="
                + self.domain.ca.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS,
            ],
            "ports": ["0", "1"],
            "command": "sh -c 'fabric-ca-server start -b admin:adminpw -d'",
            "volumes": [self.domain.ca.volumes],
            "container_name": self.domain.ca.name + "." + self.domain.name,
            "networks": [self.domain.networkname],
        }

        caorderer["ports"][0] = DoubleQuotedScalarString(
            f'{str(self.domain.ca.serverport)+":"+str(self.domain.ca.serverport)}'
        )
        caorderer["ports"][1] = DoubleQuotedScalarString(
            f'{str(self.domain.ca.operationslistenport)+":"+str(self.domain.ca.operationslistenport)}'
        )

        cafile["services"][self.domain.ca.name + "." + self.domain.name] = caorderer

        for org in self.domain.organizations:
            caorg = {
                "hostname": org.ca.FABRIC_CA_SERVER_CA_NAME + "." + self.domain.name,
                "image": "hyperledger/fabric-ca:latest",
                "user": str(os.geteuid()) + ":" + str(os.getgid()),
                "labels": {"service": "hyperledger-fabric"},
                "environment": [
                    "FABRIC_CA_HOME=" + org.ca.FABRIC_CA_HOME,
                    "FABRIC_CA_SERVER_CA_NAME="
                    + org.ca.FABRIC_CA_SERVER_CA_NAME
                    + "."
                    + self.domain.name,
                    "FABRIC_CA_SERVER_CSR_CN=" + org.ca.name + "." + self.domain.name,
                    "FABRIC_CA_SERVER_CSR_HOSTS="
                    + org.ca.name
                    + "."
                    + self.domain.name
                    + ","
                    + org.ca.name
                    + ",localhost",
                    "FABRIC_CA_SERVER_TLS_ENABLED="
                    + str(org.ca.FABRIC_CA_SERVER_TLS_ENABLED).lower(),
                    "FABRIC_CA_SERVER_PORT=" + str(org.ca.FABRIC_CA_SERVER_PORT),
                    "FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS="
                    + org.ca.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS,
                ],
                "ports": ["0", "1"],
                "command": "sh -c 'fabric-ca-server start -b admin:adminpw -d'",
                "volumes": [org.ca.volumes],
                "container_name": org.ca.name + "." + self.domain.name,
                "networks": [self.domain.networkname],
            }

            caorg["ports"][0] = DoubleQuotedScalarString(
                f'{str(org.ca.serverport)+":"+str(org.ca.serverport)}'
            )
            caorg["ports"][1] = DoubleQuotedScalarString(
                f'{str(org.ca.operationslistenport)+":"+str(org.ca.operationslistenport)}'
            )

            cafile["services"][org.ca.name + "." + self.domain.name] = caorg

        with open(
            self.paths.COMPOSEPATH + "compose-ca.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(cafile, yaml_file)

        run = Run(self.domain)
        run.start_ca()

    def build_identities(self):
        console.print("[bold white]# Creating and registering identities[/]")

        ## ORDERER

        console.print("[bold]## Enrolling the CA admin[/]")

        os.environ["FABRIC_CA_CLIENT_HOME"] = self.paths.ORDERERORGPATH

        commands.enroll(
            self.paths.APPPATH,
            self.paths.ORDERERORGPATH,
            "admin",
            "adminpw",
            self.domain.ca.serverport,
            self.paths.CADOMAINNAME,
            self.paths.TLSCERTDOMAINFILE,
        )

        CACERTPEMFILE = (
            "cacerts/localhost-"
            + str(self.domain.ca.serverport)
            + "-"
            + self.domain.ca.name.replace(".", "-")
            + "-"
            + self.domain.name.replace(".", "-")
            + ".pem"
        )
        configfile = {
            "NodeOUs": {
                "Enable": True,
                "ClientOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "client",
                },
                "PeerOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "peer",
                },
                "AdminOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "admin",
                },
                "OrdererOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "orderer",
                },
            }
        }

        with open(
            self.paths.ORDERERORGMSPPATH + "config.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(configfile, yaml_file)

        console.print("[bold]## Registering orderer[/]")
        commands.register_orderer(
            self.paths.APPPATH,
            self.paths.ORDERERORGPATH,
            "orderer",
            "ordererpw",
            self.paths.CADOMAINNAME,
            self.paths.TLSCERTDOMAINFILE,
        )

        console.print("[bold]## Registering orderer admin[/]")
        commands.register_admin(
            self.paths.APPPATH,
            self.paths.ORDERERORGPATH,
            "ordererAdmin",
            "ordererAdminpw",
            self.paths.CADOMAINNAME,
            self.paths.TLSCERTDOMAINFILE,
        )

        console.print("[bold]## Registering orderer msp[/]")
        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.ORDERERORGPATH,
            "orderer",
            "ordererpw",
            self.domain.ca.serverport,
            self.paths.CADOMAINNAME,
            self.paths.ORDDOMAINMSPPATH,
            self.paths.TLSCERTDOMAINFILE,
        )

        shutil.copy(
            self.paths.ORDERERORGMSPPATH + "config.yaml",
            self.paths.ORDDOMAINMSPPATH + "config.yaml",
        )

        console.print("[bold]## Generating the orderer-tls certificates[/]")
        hosts = [self.paths.ORDERERNAME, self.domain.orderer.name, "localhost"]
        commands.enroll_tls(
            self.paths.APPPATH,
            self.paths.ORDERERORGPATH,
            "orderer",
            "ordererpw",
            self.domain.ca.serverport,
            self.paths.CADOMAINNAME,
            self.paths.ORDDOMAINTLSPATH,
            hosts,
            self.paths.ORDERERNAME,
            self.paths.TLSCERTDOMAINFILE,
        )

        console.print("[bold]## Generating admin msp[/]")
        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.ORDERERORGPATH,
            "ordererAdmin",
            "ordererAdminpw",
            self.domain.ca.serverport,
            self.paths.CADOMAINNAME,
            self.paths.ORDDOMAINADMINMSPPATH,
            self.paths.TLSCERTDOMAINFILE,
        )

        shutil.copy(
            self.paths.ORDERERORGMSPPATH + "config.yaml",
            self.paths.ORDDOMAINADMINMSPPATH + "config.yaml",
        )

        for org in self.domain.organizations:
            self.build_identities_org(org)

    def build_identities_org(self, org: Organization):
        console.print("[bold white]## Registering organization " + org.name + "[/]")
        while True:
            try:
                container = docker.container.inspect(
                    org.ca.name + "." + self.domain.name
                )
                break
            except:
                continue

        while True:
            if container.state.running:
                break
            continue

        self.paths.set_org_paths(org)

        os.environ["FABRIC_CA_CLIENT_HOME"] = self.paths.ORGPATH
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll -u https://admin:adminpw@localhost:"
            + str(org.ca.serverport)
            + " --caname "
            + self.paths.CAORGNAME
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )

        CACERTPEMFILE = (
            "cacerts/localhost-"
            + str(org.ca.serverport)
            + "-"
            + org.ca.name.replace(".", "-")
            + "-"
            + self.domain.name.replace(".", "-")
            + ".pem",
        )

        configfile = {
            "NodeOUs": {
                "Enable": True,
                "ClientOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "client",
                },
                "PeerOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "peer",
                },
                "AdminOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "admin",
                },
                "OrdererOUIdentifier": {
                    "Certificate": CACERTPEMFILE,
                    "OrganizationalUnitIdentifier": "orderer",
                },
            }
        }

        with open(Paths.ORGMSPPATH + "config.yaml", "w", encoding="utf-8") as yaml_file:
            yaml.dump(configfile, yaml_file)

        for peer in org.peers:
            self.build_identities_peer(org, peer)

    def build_identities_peer(self, org: Organization, peer: Peer):
        console.print("[bold]## Registering " + peer.name + "[/]")

        self.paths.set_peer_paths(org, peer)

        os.environ["FABRIC_CA_CLIENT_HOME"] = self.paths.ORGPATH

        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + self.paths.CAORGNAME
            + " --id.name "
            + peer.name
            + " --id.secret "
            + peer.name
            + "pw"
            + " --id.type peer "
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )
        console.print("[bold]## Registering user[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + self.paths.CAORGNAME
            + " --id.name user1"
            + " --id.secret user1pw"
            + " --id.type client "
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )
        console.print("[bold]## Registering org admin[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + self.paths.CAORGNAME
            + " --id.name "
            + org.name
            + "admin"
            + " --id.secret "
            + org.name
            + "adminpw"
            + " --id.type admin "
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )
        console.print("[bold]## Generating peer msp[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://"
            + peer.name
            + ":"
            + peer.name
            + "pw@localhost:"
            + str(org.ca.serverport)
            + " --caname "
            + self.paths.CAORGNAME
            + " -M "
            + self.paths.PEERMSPPATH
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )

        shutil.copy(
            self.paths.ORGMSPPATH + "config.yaml",
            self.paths.PEERMSPPATH + "config.yaml",
        )

        console.print("[bold]## Generating the peer-tls certificates[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://"
            + peer.name
            + ":"
            + peer.name
            + "pw@localhost:"
            + str(org.ca.serverport)
            + " --caname "
            + self.paths.CAORGNAME
            + " -M "
            + self.paths.PEERTLSPATH
            + " --enrollment.profile tls --csr.hosts "
            + self.paths.PEERNAME
            + " --csr.hosts "
            + peer.name
            + " --csr.hosts localhost"
            + " --myhost "
            + self.paths.PEERNAME
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )

        console.print("[bold]## Generating user msp[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://user1:user1pw@localhost:"
            + str(org.ca.serverport)
            + " --caname "
            + self.paths.CAORGNAME
            + " -M "
            + self.paths.ORGUSERMSPPATH
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )

        shutil.copy(
            self.paths.ORGMSPPATH + "config.yaml",
            self.paths.ORGUSERMSPPATH + "config.yaml",
        )

        console.print("[bold]## Generating org admin msp[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://"
            + org.name
            + "admin:"
            + org.name
            + "adminpw@localhost:"
            + str(org.ca.serverport)
            + " --caname "
            + self.paths.CAORGNAME
            + " -M "
            + self.paths.ORGADMINMSPPATH
            + " --tls.certfiles "
            + self.paths.TLSCERTORGFILE
        )

        shutil.copy(
            self.paths.ORGMSPPATH + "config.yaml",
            self.paths.ORGADMINMSPPATH + "config.yaml",
        )

    def build_orderer(self):
        console.print("[bold white]# Building " + self.domain.name + " orderer[/]")

        pathorderer = "domains/" + self.domain.name + "/compose/"

        ordfile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "volumes": {self.domain.orderer.name + "." + self.domain.name},
            "services": {},
        }

        orderer = {
            "image": "hyperledger/fabric-orderer:latest",
            "labels": {"service": "hyperledger-fabric"},
            "environment": [
                "FABRIC_LOGGING_SPEC=" + self.domain.orderer.FABRIC_LOGGING_SPEC,
                "ORDERER_GENERAL_LISTENADDRESS="
                + self.domain.orderer.ORDERER_GENERAL_LISTENADDRESS,
                "ORDERER_GENERAL_LISTENPORT="
                + str(self.domain.orderer.ORDERER_GENERAL_LISTENPORT),
                "ORDERER_GENERAL_LOCALMSPID="
                + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID,
                "ORDERER_GENERAL_LOCALMSPDIR="
                + self.domain.orderer.ORDERER_GENERAL_LOCALMSPDIR,
                "ORDERER_GENERAL_TLS_ENABLED="
                + str(self.domain.orderer.ORDERER_GENERAL_TLS_ENABLED).lower(),
                "ORDERER_GENERAL_TLS_PRIVATEKEY="
                + self.domain.orderer.ORDERER_GENERAL_TLS_PRIVATEKEY,
                "ORDERER_GENERAL_TLS_CERTIFICATE="
                + self.domain.orderer.ORDERER_GENERAL_TLS_CERTIFICATE,
                "ORDERER_GENERAL_TLS_ROOTCAS="
                + self.domain.orderer.ORDERER_GENERAL_TLS_ROOTCAS,
                "ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE="
                + self.domain.orderer.ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE,
                "ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY="
                + self.domain.orderer.ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY,
                "ORDERER_GENERAL_CLUSTER_ROOTCAS="
                + self.domain.orderer.ORDERER_GENERAL_CLUSTER_ROOTCAS,
                "ORDERER_GENERAL_BOOTSTRAPMETHOD=none",
                "ORDERER_CHANNELPARTICIPATION_ENABLED="
                + str(self.domain.orderer.ORDERER_CHANNELPARTICIPATION_ENABLED).lower(),
                "ORDERER_ADMIN_TLS_ENABLED="
                + str(self.domain.orderer.ORDERER_ADMIN_TLS_ENABLED).lower(),
                "ORDERER_ADMIN_TLS_CERTIFICATE="
                + self.domain.orderer.ORDERER_ADMIN_TLS_CERTIFICATE,
                "ORDERER_ADMIN_TLS_PRIVATEKEY="
                + self.domain.orderer.ORDERER_ADMIN_TLS_PRIVATEKEY,
                "ORDERER_ADMIN_TLS_ROOTCAS="
                + self.domain.orderer.ORDERER_ADMIN_TLS_ROOTCAS,
                "ORDERER_ADMIN_TLS_CLIENTROOTCAS="
                + self.domain.orderer.ORDERER_ADMIN_TLS_CLIENTROOTCAS,
                "ORDERER_ADMIN_LISTENADDRESS="
                + self.domain.orderer.ORDERER_ADMIN_LISTENADDRESS,
                "ORDERER_OPERATIONS_LISTENADDRESS="
                + self.domain.orderer.ORDERER_OPERATIONS_LISTENADDRESS,
                "ORDERER_METRICS_PROVIDER=prometheus",
            ],
            "ports": ["0", "1", "2"],
            "working_dir": "/root",
            "command": "orderer",
            "volumes": self.domain.orderer.volumes,
            "container_name": self.domain.orderer.name + "." + self.domain.name,
            "networks": [self.domain.networkname],
        }

        orderer["ports"][0] = DoubleQuotedScalarString(
            f'{str(self.domain.orderer.adminlistenport)+":"+str(self.domain.orderer.adminlistenport)}'
        )
        orderer["ports"][1] = DoubleQuotedScalarString(
            f'{str(self.domain.orderer.operationslistenport)+":"+str(self.domain.orderer.operationslistenport)}'
        )
        orderer["ports"][2] = DoubleQuotedScalarString(
            f'{str(self.domain.orderer.generallistenport)+":"+str(self.domain.orderer.generallistenport)}'
        )

        ordfile["services"][self.domain.orderer.name + "." + self.domain.name] = orderer

        with open(
            pathorderer + "compose-orderer.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(ordfile, yaml_file)

    def build_peers_databases(self):
        console.print("[bold white]# Building peers and databases[/]")

        pathdomains = str(Path().absolute()) + "/domains/" + self.domain.name

        pathpeer = pathdomains + "/compose/"

        cliorg = self.domain.organizations[0]
        clipeer = self.domain.organizations[0].peers[0]

        peerfile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "volumes": {},
            "services": {},
        }

        clidataORDERER_CA = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/tlsca/tlsca."
            + self.domain.name
            + "-cert.pem"
        )
        clidataORDERER_ADMIN_TLS_SIGN_CERT = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/orderer/tls/server.crt"
        clidataORDERER_ADMIN_TLS_PRIVATE_KEY = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/orderer/tls/server.key"
        clidataORDERER_GENERAL_LOCALMSPDIR = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/orderer/users/Admin@"
            + self.domain.name
            + "/msp"
        )
        clidataCORE_PEER_LOCALMSPID = self.domain.organizations[0].name + "MSP"
        clidataCORE_PEER_TLS_ROOTCERT_FILE = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/"
            + cliorg.name
            + "/tlsca/tlsca."
            + cliorg.name
            + "-cert.pem"
        )
        clidataCORE_PEER_MSPCONFIGPATH = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/"
            + cliorg.name
            + "/users/Admin@"
            + cliorg.name
            + "."
            + self.domain.name
            + "/msp"
        )
        clidataCORE_PEER_ADDRESS = (
            clipeer.name + "." + self.domain.name + ":" + str(clipeer.peerlistenport)
        )
        clidataCHANNEL_NAME = self.domain.networkname

        clidata = {
            "container_name": "cli." + self.domain.name,
            "image": "hyperledger/fabric-tools:latest",
            "labels": {"service": "hyperledger-fabric"},
            "tty": True,
            "stdin_open": True,
            "environment": [
                "GOPATH=/opt/gopath",
                "FABRIC_LOGGING_SPEC=INFO",
                "FABRIC_CFG_PATH=/etc/hyperledger/peercfg",
                "CORE_PEER_TLS_ENABLED=true",
                "ORDERER_CA=" + clidataORDERER_CA,
                "ORDERER_ADMIN_TLS_SIGN_CERT=" + clidataORDERER_ADMIN_TLS_SIGN_CERT,
                "ORDERER_ADMIN_TLS_PRIVATE_KEY=" + clidataORDERER_ADMIN_TLS_PRIVATE_KEY,
                "ORDERER_GENERAL_LOCALMSPID=OrdererMSP",
                "ORDERER_GENERAL_LOCALMSPDIR=" + clidataORDERER_GENERAL_LOCALMSPDIR,
                "CORE_PEER_LOCALMSPID=" + clidataCORE_PEER_LOCALMSPID,
                "CORE_PEER_MSPCONFIGPATH=" + clidataCORE_PEER_MSPCONFIGPATH,
                "CORE_PEER_TLS_ROOTCERT_FILE=" + clidataCORE_PEER_TLS_ROOTCERT_FILE,
                "CORE_PEER_ADDRESS=" + clidataCORE_PEER_ADDRESS,
                "CHANNEL_NAME=" + clidataCHANNEL_NAME,
            ],
            "working_dir": "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            "command": "/bin/bash",
            "volumes": [
                pathdomains
                + ":/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations",
                str(Path().absolute()) + "/config:/etc/hyperledger/peercfg",
            ],
            "depends_on": [],
            "networks": [self.domain.networkname],
        }

        peerfile["services"]["cli" + "." + self.domain.name] = clidata

        for org in self.domain.organizations:
            for peer in org.peers:
                peerdata = {
                    "hostname": peer.name + "." + self.domain.name,
                    "container_name": peer.name + "." + self.domain.name,
                    "image": "hyperledger/fabric-peer:latest",
                    "labels": {"service": "hyperledger-fabric"},
                    # "user": str(os.geteuid()) + ":" + str(os.getgid()),
                    "environment": [
                        "FABRIC_CFG_PATH=" + peer.FABRIC_CFG_PATH,
                        "FABRIC_LOGGING_SPEC=" + peer.FABRIC_LOGGING_SPEC,
                        "CORE_PEER_TLS_ENABLED="
                        + str(peer.CORE_PEER_TLS_ENABLED).lower(),
                        "CORE_PEER_PROFILE_ENABLED="
                        + str(peer.CORE_PEER_PROFILE_ENABLED).lower(),
                        "CORE_PEER_TLS_CERT_FILE=" + peer.CORE_PEER_TLS_CERT_FILE,
                        "CORE_PEER_TLS_KEY_FILE=" + peer.CORE_PEER_TLS_KEY_FILE,
                        "CORE_PEER_TLS_ROOTCERT_FILE="
                        + peer.CORE_PEER_TLS_ROOTCERT_FILE,
                        "CORE_PEER_ID=" + peer.CORE_PEER_ID,
                        "CORE_PEER_ADDRESS=" + peer.CORE_PEER_ADDRESS,
                        "CORE_PEER_LISTENADDRESS=" + peer.CORE_PEER_LISTENADDRESS,
                        "CORE_PEER_CHAINCODEADDRESS=" + peer.CORE_PEER_CHAINCODEADDRESS,
                        "CORE_PEER_CHAINCODELISTENADDRESS="
                        + peer.CORE_PEER_CHAINCODELISTENADDRESS,
                        "CORE_PEER_GOSSIP_BOOTSTRAP=" + peer.CORE_PEER_GOSSIP_BOOTSTRAP,
                        "CORE_PEER_GOSSIP_EXTERNALENDPOINT="
                        + peer.CORE_PEER_GOSSIP_EXTERNALENDPOINT,
                        "CORE_PEER_LOCALMSPID=" + peer.CORE_PEER_LOCALMSPID,
                        "CORE_PEER_MSPCONFIGPATH=" + peer.CORE_PEER_MSPCONFIGPATH,
                        "CORE_OPERATIONS_LISTENADDRESS="
                        + peer.CORE_OPERATIONS_LISTENADDRESS,
                        "CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG="
                        + peer.CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG,
                        "CORE_CHAINCODE_EXECUTETIMEOUT="
                        + peer.CORE_CHAINCODE_EXECUTETIMEOUT,
                        "CORE_VM_ENDPOINT=" + peer.CORE_VM_ENDPOINT,
                        "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE="
                        + peer.CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE,
                        "CORE_LEDGER_STATE_STATEDATABASE="
                        + peer.CORE_LEDGER_STATE_STATEDATABASE,
                        "CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS="
                        + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS,
                        "CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME="
                        + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME,
                        "CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD="
                        + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD,
                        "CORE_METRICS_PROVIDER=prometheus",
                    ],
                    "ports": ["0", "1", "2"],
                    "working_dir": "/opt/gopath/src/github.com/hyperledger/fabric/peer",
                    "command": "peer node start",
                    "volumes": peer.volumes,
                    "networks": [self.domain.networkname],
                    "depends_on": [
                        peer.database.name + "." + self.domain.name,
                        self.domain.orderer.name + "." + self.domain.name,
                    ],
                }

                peerdata["ports"][0] = DoubleQuotedScalarString(
                    f'{str(peer.peerlistenport)+":"+str(peer.peerlistenport)}'
                )
                peerdata["ports"][1] = DoubleQuotedScalarString(
                    f'{str(peer.operationslistenport)+":"+str(peer.operationslistenport)}'
                )
                peerdata["ports"][2] = DoubleQuotedScalarString(
                    f'{str(peer.chaincodelistenport)+":"+str(peer.chaincodelistenport)}'
                )

                clidata["depends_on"].append(peer.name + "." + self.domain.name)

                peerfile["volumes"][peer.name + "." + self.domain.name] = {}

                peerfile["services"][peer.name + "." + self.domain.name] = peerdata

                databasedata = {
                    "image": "couchdb:3.3.2",
                    "labels": {"service": "hyperledger-fabric"},
                    "environment": [
                        "COUCHDB_USER=" + peer.database.COUCHDB_USER,
                        "COUCHDB_PASSWORD=" + peer.database.COUCHDB_PASSWORD,
                    ],
                    "ports": ["0"],
                    "container_name": peer.database.name + "." + self.domain.name,
                    "networks": [self.domain.networkname],
                }

                databasedata["ports"][0] = DoubleQuotedScalarString(
                    f'{str(peer.database.port)+":5984"}'
                )

                peerfile["services"][
                    peer.database.name + "." + self.domain.name
                ] = databasedata

        with open(pathpeer + "compose-net.yaml", "w", encoding="utf-8") as yaml_file:
            yaml.dump(peerfile, yaml_file)

    def build_peers_databases_org(self, org: Organization):
        console.print("[bold white]# Building " + org.name + " peers and databases[/]")

        pathpeer = "domains/" + self.domain.name + "/compose/"

        with open(pathpeer + "compose-net.yaml", encoding="utf-8") as yamlpeer_file:
            datapeer = yaml.load(yamlpeer_file)

        peerfile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "volumes": {},
            "services": {},
        }

        for peer in org.peers:
            peerdata = {
                "hostname": peer.name + "." + self.domain.name,
                "container_name": peer.name + "." + self.domain.name,
                "image": "hyperledger/fabric-peer:latest",
                "labels": {"service": "hyperledger-fabric"},
                # "user": str(os.geteuid()) + ":" + str(os.getgid()),
                "environment": [
                    "FABRIC_CFG_PATH=" + peer.FABRIC_CFG_PATH,
                    "FABRIC_LOGGING_SPEC=" + peer.FABRIC_LOGGING_SPEC,
                    "CORE_PEER_TLS_ENABLED=" + str(peer.CORE_PEER_TLS_ENABLED),
                    "CORE_PEER_PROFILE_ENABLED=" + str(peer.CORE_PEER_PROFILE_ENABLED),
                    "CORE_PEER_TLS_CERT_FILE=" + peer.CORE_PEER_TLS_CERT_FILE,
                    "CORE_PEER_TLS_KEY_FILE=" + peer.CORE_PEER_TLS_KEY_FILE,
                    "CORE_PEER_TLS_ROOTCERT_FILE=" + peer.CORE_PEER_TLS_ROOTCERT_FILE,
                    "CORE_PEER_ID=" + peer.CORE_PEER_ID,
                    "CORE_PEER_ADDRESS=" + peer.CORE_PEER_ADDRESS,
                    "CORE_PEER_LISTENADDRESS=" + peer.CORE_PEER_LISTENADDRESS,
                    "CORE_PEER_CHAINCODEADDRESS=" + peer.CORE_PEER_CHAINCODEADDRESS,
                    "CORE_PEER_CHAINCODELISTENADDRESS="
                    + peer.CORE_PEER_CHAINCODELISTENADDRESS,
                    "CORE_PEER_GOSSIP_BOOTSTRAP=" + peer.CORE_PEER_GOSSIP_BOOTSTRAP,
                    "CORE_PEER_GOSSIP_EXTERNALENDPOINT="
                    + peer.CORE_PEER_GOSSIP_EXTERNALENDPOINT,
                    "CORE_PEER_LOCALMSPID=" + peer.CORE_PEER_LOCALMSPID,
                    "CORE_PEER_MSPCONFIGPATH=" + peer.CORE_PEER_MSPCONFIGPATH,
                    "CORE_OPERATIONS_LISTENADDRESS="
                    + peer.CORE_OPERATIONS_LISTENADDRESS,
                    "CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG="
                    + peer.CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG,
                    "CORE_CHAINCODE_EXECUTETIMEOUT="
                    + peer.CORE_CHAINCODE_EXECUTETIMEOUT,
                    "CORE_VM_ENDPOINT=" + peer.CORE_VM_ENDPOINT,
                    "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE="
                    + peer.CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE,
                    "CORE_LEDGER_STATE_STATEDATABASE="
                    + peer.CORE_LEDGER_STATE_STATEDATABASE,
                    "CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS="
                    + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS,
                    "CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME="
                    + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME,
                    "CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD="
                    + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD,
                    "CORE_METRICS_PROVIDER=prometheus",
                ],
                "ports": ["0", "1", "2"],
                "working_dir": "/root",
                "command": "peer node start",
                "volumes": peer.volumes,
                "networks": [self.domain.networkname],
                "depends_on": [peer.database.name],
            }

            peerdata["ports"][0] = DoubleQuotedScalarString(
                f'{str(peer.peerlistenport)+":"+str(peer.peerlistenport)}'
            )
            peerdata["ports"][1] = DoubleQuotedScalarString(
                f'{str(peer.operationslistenport)+":"+str(peer.operationslistenport)}'
            )
            peerdata["ports"][2] = DoubleQuotedScalarString(
                f'{str(peer.chaincodelistenport)+":"+str(peer.chaincodelistenport)}'
            )

            peerfile["volumes"][peer.name + "." + self.domain.name] = {}
            datapeer["volumes"][peer.name + "." + self.domain.name] = {}

            peerfile["services"][peer.name + "." + self.domain.name] = peerdata
            datapeer["services"][peer.name + "." + self.domain.name] = peerdata

            databasedata = {
                "image": "couchdb:3.3.2",
                "labels": {"service": "hyperledger-fabric"},
                "environment": [
                    "COUCHDB_USER=" + peer.database.COUCHDB_USER,
                    "COUCHDB_PASSWORD=" + peer.database.COUCHDB_PASSWORD,
                ],
                "ports": ["0"],
                "container_name": peer.database.name + "." + self.domain.name,
                "networks": [self.domain.networkname],
            }

            databasedata["ports"][0] = DoubleQuotedScalarString(
                f'{str(peer.database.port)+":5984"}'
            )

            peerfile["services"][
                peer.database.name + "." + self.domain.name
            ] = databasedata
            datapeer["services"][
                peer.database.name + "." + self.domain.name
            ] = databasedata

        with open(pathpeer + "compose-net-" + org.name + ".yaml", "w") as yaml_file:
            yaml.dump(peerfile, yaml_file)

        with open(
            pathpeer + "compose-net.yaml", "w", encoding="utf-8"
        ) as yamlpeer_file:
            yaml.dump(datapeer, yamlpeer_file)

    def build_peer(self, peer: Peer):
        console.print("[bold white]# Building " + peer.name + " and database[/]")

        pathpeer = "domains/" + self.domain.name + "/compose/"

        with open(pathpeer + "compose-net.yaml") as yamlpeer_file:
            datapeer = yaml.load(yamlpeer_file)

        peerfile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "volumes": {},
            "services": {},
        }

        peerdata = {
            "container_name": peer.name + "." + self.domain.name,
            "image": "hyperledger/fabric-peer:latest",
            "labels": {"service": "hyperledger-fabric"},
            # "user": str(os.geteuid()) + ":" + str(os.getgid()),
            "environment": [
                "FABRIC_CFG_PATH=" + peer.FABRIC_CFG_PATH,
                "FABRIC_LOGGING_SPEC=" + peer.FABRIC_LOGGING_SPEC,
                "CORE_PEER_TLS_ENABLED=" + str(peer.CORE_PEER_TLS_ENABLED),
                "CORE_PEER_PROFILE_ENABLED=" + str(peer.CORE_PEER_PROFILE_ENABLED),
                "CORE_PEER_TLS_CERT_FILE=" + peer.CORE_PEER_TLS_CERT_FILE,
                "CORE_PEER_TLS_KEY_FILE=" + peer.CORE_PEER_TLS_KEY_FILE,
                "CORE_PEER_TLS_ROOTCERT_FILE=" + peer.CORE_PEER_TLS_ROOTCERT_FILE,
                "CORE_PEER_ID=" + peer.CORE_PEER_ID,
                "CORE_PEER_ADDRESS=" + peer.CORE_PEER_ADDRESS,
                "CORE_PEER_LISTENADDRESS=" + peer.CORE_PEER_LISTENADDRESS,
                "CORE_PEER_CHAINCODEADDRESS=" + peer.CORE_PEER_CHAINCODEADDRESS,
                "CORE_PEER_CHAINCODELISTENADDRESS="
                + peer.CORE_PEER_CHAINCODELISTENADDRESS,
                "CORE_PEER_GOSSIP_BOOTSTRAP=" + peer.CORE_PEER_GOSSIP_BOOTSTRAP,
                "CORE_PEER_GOSSIP_EXTERNALENDPOINT="
                + peer.CORE_PEER_GOSSIP_EXTERNALENDPOINT,
                "CORE_PEER_LOCALMSPID=" + peer.CORE_PEER_LOCALMSPID,
                "CORE_PEER_MSPCONFIGPATH=" + peer.CORE_PEER_MSPCONFIGPATH,
                "CORE_OPERATIONS_LISTENADDRESS=" + peer.CORE_OPERATIONS_LISTENADDRESS,
                "CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG="
                + peer.CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG,
                "CORE_CHAINCODE_EXECUTETIMEOUT=" + peer.CORE_CHAINCODE_EXECUTETIMEOUT,
                "CORE_VM_ENDPOINT=" + peer.CORE_VM_ENDPOINT,
                "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE="
                + peer.CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE,
                "CORE_LEDGER_STATE_STATEDATABASE="
                + peer.CORE_LEDGER_STATE_STATEDATABASE,
                "CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS="
                + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS,
                "CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME="
                + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME,
                "CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD="
                + peer.CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD,
                "CORE_METRICS_PROVIDER=prometheus",
            ],
            "ports": ["0", "1", "2"],
            "working_dir": "/root",
            "command": "peer node start",
            "volumes": peer.volumes,
            "networks": [self.domain.networkname],
            "depends_on": [peer.database.name],
        }

        peerdata["ports"][0] = DoubleQuotedScalarString(
            f'{str(peer.peerlistenport)+":"+str(peer.peerlistenport)}'
        )
        peerdata["ports"][1] = DoubleQuotedScalarString(
            f'{str(peer.operationslistenport)+":"+str(peer.operationslistenport)}'
        )
        peerdata["ports"][2] = DoubleQuotedScalarString(
            f'{str(peer.chaincodelistenport)+":"+str(peer.chaincodelistenport)}'
        )

        peerfile["volumes"][peer.name + "." + self.domain.name] = {}
        datapeer["volumes"][peer.name + "." + self.domain.name] = {}

        peerfile["services"][peer.name + "." + self.domain.name] = peerdata
        datapeer["services"][peer.name + "." + self.domain.name] = peerdata

        databasedata = {
            "image": "couchdb:3.3.2",
            "labels": {"service": "hyperledger-fabric"},
            "environment": [
                "COUCHDB_USER=" + peer.database.COUCHDB_USER,
                "COUCHDB_PASSWORD=" + peer.database.COUCHDB_PASSWORD,
            ],
            "ports": ["0"],
            "container_name": peer.database.name + "." + self.domain.name,
            "networks": [self.domain.networkname],
        }

        databasedata["ports"][0] = DoubleQuotedScalarString(
            f'{str(peer.database.port)+":5984"}'
        )

        peerfile["services"][peer.database.name + "." + self.domain.name] = databasedata
        datapeer["services"][peer.database.name + "." + self.domain.name] = databasedata

        with open(
            pathpeer + "compose-net-" + peer.name + ".yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(peerfile, yaml_file)

        with open(
            pathpeer + "compose-net.yaml", "w", encoding="utf-8"
        ) as yamlpeer_file:
            yaml.dump(datapeer, yamlpeer_file)

    def build_new_organization(self, org: Organization):
        self.build_new_org_ca(org)
        self.build_identities_org(org)
        self.build_peers_databases_org(org)
        self.prepare_firefly()
        self.build_config()
        self.starting_pd_org(org)

    def build_new_org_ca(self, org: Organization):
        console.print("[bold white]# Building and starting " + org.name + " CA[/]")

        pathfabricca = "domains/" + self.domain.name + "/compose/"

        with open(pathfabricca + "compose-ca.yaml", encoding="utf-8") as yamlca_file:
            cadata = yaml.load(yamlca_file)

        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
        }

        self.paths.set_org_paths(org)
        caorg = {
            "image": "hyperledger/fabric-ca:latest",
            "user": str(os.geteuid()) + ":" + str(os.getgid()),
            "labels": {"service": "hyperledger-fabric"},
            "environment": [
                "FABRIC_CA_HOME=" + org.ca.FABRIC_CA_HOME,
                "FABRIC_CA_SERVER_CA_NAME="
                + org.ca.FABRIC_CA_SERVER_CA_NAME
                + "."
                + self.domain.name,
                "FABRIC_CA_SERVER_CSR_CN=" + org.ca.name + "." + self.domain.name,
                "FABRIC_CA_SERVER_CSR_HOSTS="
                + org.ca.name
                + "."
                + self.domain.name
                + ","
                + org.ca.name
                + ",localhost",
                "FABRIC_CA_SERVER_TLS_ENABLED="
                + str(org.ca.FABRIC_CA_SERVER_TLS_ENABLED).lower(),
                "FABRIC_CA_SERVER_PORT=" + str(org.ca.FABRIC_CA_SERVER_PORT),
                "FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS="
                + org.ca.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS,
            ],
            "ports": ["0", "1"],
            "command": "sh -c 'fabric-ca-server start -b admin:adminpw -d'",
            "volumes": [org.ca.volumes],
            "container_name": org.ca.name + "." + self.domain.name,
            "networks": [self.domain.networkname],
        }

        caorg["ports"][0] = DoubleQuotedScalarString(
            f'{str(org.ca.serverport)+":"+str(org.ca.serverport)}'
        )
        caorg["ports"][1] = DoubleQuotedScalarString(
            f'{str(org.ca.operationslistenport)+":"+str(org.ca.operationslistenport)}'
        )

        cafile["services"][org.ca.name + "." + self.domain.name] = caorg
        cadata["services"][org.ca.name + "." + self.domain.name] = caorg

        with open(
            pathfabricca + "compose-ca-" + org.name + ".yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(cafile, yaml_file)

        with open(
            pathfabricca + "compose-ca.yaml", "w", encoding="utf-8"
        ) as cayaml_file:
            yaml.dump(cadata, cayaml_file)

        run = Run(self.domain)
        run.start_ca_new(org.name)

    def build_new_peer(self, org: Organization, peer: Peer):
        self.build_identities_peer(org, peer)
        self.build_peer(peer)
        self.build_config()
        self.starting_new_peer(peer)

    def prepare_firefly(self):
        for i, org in enumerate(self.domain.organizations):
            ## Copy MSP Users
            mspadminpath = Path(
                "domains/"
                + self.domain.name
                + "/peerOrganizations/"
                + org.name
                + "/msp/users"
                + "/Admin@"
                + org.name
                + "."
                + self.domain.name
                + "/msp"
            )

            shutil.copytree(
                str(Path().absolute())
                + str(
                    Path(
                        "/domains/"
                        + self.domain.name
                        + "/peerOrganizations/"
                        + org.name
                        + "/users"
                    )
                ),
                str(Path().absolute())
                + str(
                    Path(
                        "/domains/"
                        + self.domain.name
                        + "/peerOrganizations/"
                        + org.name
                        + "/msp/users"
                    )
                ),
            )
            ## Copy Orderer
            orderercrypto = (
                str(Path().absolute())
                + "/domains/"
                + self.domain.name
                + "/ordererOrganizations/orderer"
            )
            shutil.copytree(
                orderercrypto,
                str(Path().absolute())
                + "/domains/"
                + self.domain.name
                + "/peerOrganizations/"
                + org.name
                + "/msp/orderer",
            )

            dir_path = str(Path().absolute()) + "/" + str(mspadminpath) + "/keystore/"
            filelst = os.listdir(dir_path)
            for keystore in filelst:
                if os.path.isfile(dir_path + keystore):
                    self.domain.organizations[i].keystore = (
                        "/etc/firefly/organizations/users/Admin@"
                        + org.name
                        + "."
                        + self.domain.name
                        + "/msp/keystore/"
                        + keystore
                    )

            for peer in org.peers:
                shutil.copytree(
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/"
                    + peer.name,
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/msp/"
                    + peer.name,
                )

    def starting_opd(self):
        console.print("[bold white]# Starting orderer, peers and databases[/]")

        run = Run(self.domain)
        run.starting_opd()

    def starting_pd_org(self, org: Organization):
        console.print("[bold white]# Starting " + org.name + " peers and databases[/]")

        run = Run(self.domain)
        run.starting_pd_org(org)

    def starting_new_peer(self, peer: Peer):
        console.print("[bold white]# Starting new peer " + peer.name + "[/]")

        run = Run(self.domain)
        run.starting_pd(peer)
