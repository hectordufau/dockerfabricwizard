import json
import os
import shutil
from pathlib import Path

import ruamel.yaml
from python_on_whales import docker
from rich.console import Console
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from controllers.run import Run
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=2)
yaml.boolean_representation = [f"false", f"true"]
console = Console()


class Build:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        console.print("[bold orange1]BUILD[/]")
        console.print("")
        self.buildFolders()
        self.buildCa()
        self.buildIdentities()
        self.buildOrderer()
        self.buildPeersDatabases()
        self.startingOPD()
        console.print("")

    def buildFolders(self):
        console.print("[bold white]# Preparing folders[/]")

        rmfolders = str(Path("domains/" + self.domain.name + "/fabric-ca"))
        os.system("rm -fR " + rmfolders)

        rmfolders = str(Path("domains/" + self.domain.name + "/peerOrganizations"))
        os.system("rm -fR " + rmfolders)

        rmfolders = str(Path("domains/" + self.domain.name + "/ordererOrganizations"))
        os.system("rm -fR " + rmfolders)

        rmfolders = str(Path("domains/" + self.domain.name + "/channel-artifacts"))
        os.system("rm -fR " + rmfolders)

        pathcompose = Path("domains/" + self.domain.name + "/compose")
        pathcompose.mkdir(parents=True, exist_ok=True)

        pathfabricca = Path(
            "domains/" + self.domain.name + "/fabric-ca/" + self.domain.ca.name
        )
        pathfabricca.mkdir(parents=True, exist_ok=True)

        pathorderer = Path(
            "domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
        )
        pathorderer.mkdir(parents=True, exist_ok=True)

        for org in self.domain.organizations:
            self.buildFoldersOrg(org)

    def buildFoldersOrg(self, org: Organization):
        pathfabriccaorg = Path(
            "domains/" + self.domain.name + "/fabric-ca/" + org.ca.name
        )
        pathfabriccaorg.mkdir(parents=True, exist_ok=True)

        pathorgs = Path(
            "domains/" + self.domain.name + "/peerOrganizations/" + org.name
        )
        pathorgs.mkdir(parents=True, exist_ok=True)

        for peer in org.peers:
            self.buildFolderPeer(org, peer)

    def buildFolderPeer(self, org: Organization, peer: Peer):
        configpeer = str(Path("config/core.yaml"))
        pathpeers = Path(
            "domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/peercfg"
        )
        pathpeers.mkdir(parents=True, exist_ok=True)

        shutil.copy(
            str(Path().absolute()) + "/" + configpeer,
            str(Path().absolute()) + "/" + str(pathpeers) + "/core.yaml",
        )

        self.buildConfig()

    def buildConfig(self):
        console.print("[bold white]# Creating domain config file[/]")
        pathdomains = str(Path().absolute()) + "/domains/" + self.domain.name

        json_object = json.dumps(self.domain, default=lambda x: x.__dict__, indent=4)
        with open(pathdomains + "/setup.json", "w", encoding="utf-8") as outfile:
            outfile.write(json_object)

    def buildCa(self):
        console.print("[bold white]# Building and starting CAs[/]")

        pathfabricca = "domains/" + self.domain.name + "/compose/"
        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
        }

        caorderer = {
            "image": "hyperledger/fabric-ca:latest",
            "user": str(os.geteuid()) + ":" + str(os.getgid()),
            "labels": {"service": "hyperledger-fabric"},
            "environment": [
                "FABRIC_CA_HOME=" + self.domain.ca.FABRIC_CA_HOME,
                "FABRIC_CA_SERVER_CA_NAME="
                + self.domain.ca.FABRIC_CA_SERVER_CA_NAME
                + "."
                + self.domain.name,
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
                "image": "hyperledger/fabric-ca:latest",
                "user": str(os.geteuid()) + ":" + str(os.getgid()),
                "labels": {"service": "hyperledger-fabric"},
                "environment": [
                    "FABRIC_CA_HOME=" + org.ca.FABRIC_CA_HOME,
                    "FABRIC_CA_SERVER_CA_NAME="
                    + org.ca.FABRIC_CA_SERVER_CA_NAME
                    + "."
                    + self.domain.name,
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

        with open(pathfabricca + "compose-ca.yaml", "w", encoding="utf-8") as yaml_file:
            yaml.dump(cafile, yaml_file)

        run = Run(self.domain)
        run.startCA()

    def buildIdentities(self):
        console.print("[bold white]# Creating and registering identities[/]")

        for org in self.domain.organizations:
            self.buildIdentitiesOrg(org)

        ## ORDERER

        console.print("[bold]## Enrolling the CA admin[/]")
        pathorder = Path("domains/" + self.domain.name + "/ordererOrganizations")
        pathfabriccaorderer = Path(
            "domains/" + self.domain.name + "/fabric-ca/" + self.domain.ca.name
        )

        os.environ["FABRIC_CA_CLIENT_HOME"] = str(pathorder)

        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll -u https://admin:adminpw@localhost:"
            + str(self.domain.ca.serverport)
            + " --caname "
            + self.domain.ca.name
            + "."
            + self.domain.name
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorderer)
            + "/ca-cert.pem"
        )
        configfile = {
            "NodeOUs": {
                "Enable": True,
                "ClientOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(self.domain.ca.serverport)
                    + "-"
                    + self.domain.ca.name
                    + "-"
                    + self.domain.name
                    + ".pem",
                    "OrganizationalUnitIdentifier": "client",
                },
                "PeerOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(self.domain.ca.serverport)
                    + "-"
                    + self.domain.ca.name
                    + "-"
                    + self.domain.name
                    + ".pem",
                    "OrganizationalUnitIdentifier": "peer",
                },
                "AdminOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(self.domain.ca.serverport)
                    + "-"
                    + self.domain.ca.name
                    + "-"
                    + self.domain.name
                    + ".pem",
                    "OrganizationalUnitIdentifier": "admin",
                },
                "OrdererOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(self.domain.ca.serverport)
                    + "-"
                    + self.domain.ca.name
                    + "-"
                    + self.domain.name
                    + ".pem",
                    "OrganizationalUnitIdentifier": "orderer",
                },
            }
        }

        configpath = "".join([str(Path().absolute()), "/", str(pathorder), "/msp"])
        with open(configpath + "/config.yaml", "w", encoding="utf-8") as yaml_file:
            yaml.dump(configfile, yaml_file)

        cacert = (
            str(Path().absolute()) + "/" + str(pathfabriccaorderer) + "/ca-cert.pem"
        )

        tlscacerts = Path(
            "domains/" + self.domain.name + "/ordererOrganizations/msp/tlscacerts"
        )
        tlscacerts.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            cacert,
            str(Path().absolute())
            + "/"
            + str(tlscacerts)
            + "/tlsca."
            + self.domain.name
            + "-cert.pem",
        )

        tlsca = Path("domains/" + self.domain.name + "/ordererOrganizations/tlsca")
        tlsca.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            cacert,
            str(Path().absolute())
            + "/"
            + str(tlsca)
            + "/tlsca."
            + self.domain.name
            + "-cert.pem",
        )

        console.print("[bold]## Registering orderer[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + self.domain.ca.name
            + "."
            + self.domain.name
            + " --id.name orderer"
            + " --id.secret ordererpw"
            + " --id.type orderer "
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorderer)
            + "/ca-cert.pem"
        )

        console.print("[bold]## Registering orderer admin[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + self.domain.ca.name
            + "."
            + self.domain.name
            + " --id.name ordererAdmin"
            + " --id.secret ordererAdminpw"
            + " --id.type admin "
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorderer)
            + "/ca-cert.pem"
        )

        console.print("[bold]## Registering orderer msp[/]")
        msppath = Path(
            "domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
            + "/msp"
        )
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://orderer:ordererpw@localhost:"
            + str(self.domain.ca.serverport)
            + " --caname "
            + self.domain.ca.name
            + "."
            + self.domain.name
            + " -M "
            + str(Path().absolute())
            + "/"
            + str(msppath)
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorderer)
            + "/ca-cert.pem"
        )
        shutil.copy(
            configpath + "/config.yaml",
            str(Path().absolute()) + "/" + str(msppath) + "/config.yaml",
        )

        console.print("[bold]## Generating the orderer-tls certificates[/]")
        tlspath = Path(
            "domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
            + "/tls"
        )
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://orderer:ordererpw@localhost:"
            + str(self.domain.ca.serverport)
            + " --caname "
            + self.domain.ca.name
            + "."
            + self.domain.name
            + " -M "
            + str(Path().absolute())
            + "/"
            + str(tlspath)
            + " --enrollment.profile tls --csr.hosts "
            + self.domain.orderer.name
            + "."
            + self.domain.name
            + " --csr.hosts localhost"
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorderer)
            + "/ca-cert.pem"
        )

        shutil.copy(
            str(Path().absolute()) + "/" + str(tlspath) + "/signcerts/cert.pem",
            str(Path().absolute()) + "/" + str(tlspath) + "/server.crt",
        )

        for file_name in os.listdir(
            str(Path().absolute()) + "/" + str(tlspath) + "/tlscacerts/"
        ):
            shutil.copy(
                str(Path().absolute())
                + "/"
                + str(tlspath)
                + "/tlscacerts/"
                + file_name,
                str(Path().absolute()) + "/" + str(tlspath) + "/ca.crt",
            )

        for file_name in os.listdir(
            str(Path().absolute()) + "/" + str(tlspath) + "/keystore/"
        ):
            shutil.copy(
                str(Path().absolute()) + "/" + str(tlspath) + "/keystore/" + file_name,
                str(Path().absolute()) + "/" + str(tlspath) + "/server.key",
            )

        msptlscacerts = Path(
            "domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
            + "/msp/tlscacerts"
        )
        msptlscacerts.mkdir(parents=True, exist_ok=True)

        for file_name in os.listdir(
            str(Path().absolute()) + "/" + str(tlspath) + "/tlscacerts/"
        ):
            shutil.copy(
                str(Path().absolute())
                + "/"
                + str(tlspath)
                + "/tlscacerts/"
                + file_name,
                str(Path().absolute())
                + "/"
                + str(msptlscacerts)
                + "/tlsca."
                + self.domain.name
                + "-cert.pem",
            )

        console.print("[bold]## Generating admin msp[/]")
        adminpath = Path(
            "domains/"
            + self.domain.name
            + "/ordererOrganizations/users"
            + "/Admin@"
            + self.domain.name
            + "/msp"
        )
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://ordererAdmin:ordererAdminpw@localhost:"
            + str(self.domain.ca.serverport)
            + " --caname "
            + self.domain.ca.name
            + "."
            + self.domain.name
            + " -M "
            + str(Path().absolute())
            + "/"
            + str(adminpath)
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorderer)
            + "/ca-cert.pem"
        )

        shutil.copy(
            configpath + "/config.yaml",
            str(Path().absolute()) + "/" + str(adminpath) + "/config.yaml",
        )

    def buildIdentitiesOrg(self, org: Organization):
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

        pathfabriccaorg = Path(
            "domains/" + self.domain.name + "/fabric-ca/" + org.ca.name
        )

        pathorg = Path("domains/" + self.domain.name + "/peerOrganizations/" + org.name)

        os.environ["FABRIC_CA_CLIENT_HOME"] = str(pathorg)
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll -u https://admin:adminpw@localhost:"
            + str(org.ca.serverport)
            + " --caname "
            + org.ca.name
            + "."
            + self.domain.name
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )

        configfile = {
            "NodeOUs": {
                "Enable": True,
                "ClientOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(org.ca.serverport)
                    + "-"
                    + org.ca.name.replace(".", "-")
                    + "-"
                    + self.domain.name.replace(".", "-")
                    + ".pem",
                    "OrganizationalUnitIdentifier": "client",
                },
                "PeerOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(org.ca.serverport)
                    + "-"
                    + org.ca.name.replace(".", "-")
                    + "-"
                    + self.domain.name.replace(".", "-")
                    + ".pem",
                    "OrganizationalUnitIdentifier": "peer",
                },
                "AdminOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(org.ca.serverport)
                    + "-"
                    + org.ca.name.replace(".", "-")
                    + "-"
                    + self.domain.name.replace(".", "-")
                    + ".pem",
                    "OrganizationalUnitIdentifier": "admin",
                },
                "OrdererOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(org.ca.serverport)
                    + "-"
                    + org.ca.name.replace(".", "-")
                    + "-"
                    + self.domain.name.replace(".", "-")
                    + ".pem",
                    "OrganizationalUnitIdentifier": "orderer",
                },
            }
        }

        configpath = "".join([str(Path().absolute()), "/", str(pathorg), "/msp"])
        with open(configpath + "/config.yaml", "w", encoding="utf-8") as yaml_file:
            yaml.dump(configfile, yaml_file)

        cacert = str(Path().absolute()) + "/" + str(pathfabriccaorg) + "/ca-cert.pem"

        tlscacerts = Path(
            "domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/msp/tlscacerts"
        )
        tlscacerts.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            cacert,
            str(Path().absolute()) + "/" + str(tlscacerts) + "/ca.crt",
        )

        tlsca = Path(
            "domains/" + self.domain.name + "/peerOrganizations/" + org.name + "/tlsca"
        )
        tlsca.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            cacert,
            str(Path().absolute())
            + "/"
            + str(tlsca)
            + "/tlsca."
            + org.name
            + "-cert.pem",
        )

        ca = Path(
            "domains/" + self.domain.name + "/peerOrganizations/" + org.name + "/ca"
        )
        ca.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            cacert,
            str(Path().absolute()) + "/" + str(ca) + "/ca." + org.name + "-cert.pem",
        )

        for peer in org.peers:
            self.buildIdentitiesPeer(org, peer)

    def buildIdentitiesPeer(self, org: Organization, peer: Peer):
        console.print("[bold]## Registering " + peer.name + "[/]")

        pathfabriccaorg = Path(
            "domains/" + self.domain.name + "/fabric-ca/" + org.ca.name
        )

        pathorg = Path("domains/" + self.domain.name + "/peerOrganizations/" + org.name)

        configpath = "".join([str(Path().absolute()), "/", str(pathorg), "/msp"])

        os.environ["FABRIC_CA_CLIENT_HOME"] = str(pathorg)

        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + org.ca.name
            + "."
            + self.domain.name
            + " --id.name "
            + peer.name
            + " --id.secret "
            + peer.name
            + "pw"
            + " --id.type peer "
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )
        console.print("[bold]## Registering user[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + org.ca.name
            + "."
            + self.domain.name
            + " --id.name user1"
            + " --id.secret user1pw"
            + " --id.type client "
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )
        console.print("[bold]## Registering org admin[/]")
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client register "
            + " --caname "
            + org.ca.name
            + "."
            + self.domain.name
            + " --id.name "
            + org.name
            + "admin"
            + " --id.secret "
            + org.name
            + "adminpw"
            + " --id.type admin "
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )
        console.print("[bold]## Generating peer msp[/]")
        msppath = Path(
            "domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/msp"
        )
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
            + org.ca.name
            + "."
            + self.domain.name
            + " -M "
            + str(Path().absolute())
            + "/"
            + str(msppath)
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )

        shutil.copy(
            configpath + "/config.yaml",
            str(Path().absolute()) + "/" + str(msppath) + "/config.yaml",
        )

        console.print("[bold]## Generating the peer-tls certificates[/]")
        tlspath = Path(
            "domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/tls"
        )
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
            + org.ca.name
            + "."
            + self.domain.name
            + " -M "
            + str(Path().absolute())
            + "/"
            + str(tlspath)
            + " --enrollment.profile tls --csr.hosts "
            + peer.name
            + "."
            + self.domain.name
            + " --csr.hosts localhost"
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )

        shutil.copy(
            str(Path().absolute()) + "/" + str(tlspath) + "/signcerts/cert.pem",
            str(Path().absolute()) + "/" + str(tlspath) + "/server.crt",
        )

        for file_name in os.listdir(
            str(Path().absolute()) + "/" + str(tlspath) + "/tlscacerts/"
        ):
            shutil.copy(
                str(Path().absolute())
                + "/"
                + str(tlspath)
                + "/tlscacerts/"
                + file_name,
                str(Path().absolute()) + "/" + str(tlspath) + "/ca.crt",
            )

        for file_name in os.listdir(
            str(Path().absolute()) + "/" + str(tlspath) + "/keystore/"
        ):
            shutil.copy(
                str(Path().absolute()) + "/" + str(tlspath) + "/keystore/" + file_name,
                str(Path().absolute()) + "/" + str(tlspath) + "/server.key",
            )

        console.print("[bold]## Generating user msp[/]")
        userpath = Path(
            "domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/users"
            + "/User1@"
            + org.name
            + "."
            + self.domain.name
            + "/msp"
        )
        os.system(
            str(Path().absolute())
            + "/bin/fabric-ca-client enroll "
            + " -u https://user1:user1pw@localhost:"
            + str(org.ca.serverport)
            + " --caname "
            + org.ca.name
            + "."
            + self.domain.name
            + " -M "
            + str(Path().absolute())
            + "/"
            + str(userpath)
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )

        shutil.copy(
            configpath + "/config.yaml",
            str(Path().absolute()) + "/" + str(userpath) + "/config.yaml",
        )

        console.print("[bold]## Generating org admin msp[/]")
        adminpath = Path(
            "domains/"
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
            + org.ca.name
            + "."
            + self.domain.name
            + " -M "
            + str(Path().absolute())
            + "/"
            + str(adminpath)
            + " --tls.certfiles "
            + str(Path().absolute())
            + "/"
            + str(pathfabriccaorg)
            + "/ca-cert.pem"
        )

        shutil.copy(
            configpath + "/config.yaml",
            str(Path().absolute()) + "/" + str(adminpath) + "/config.yaml",
        )

    def buildOrderer(self):
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

    def buildPeersDatabases(self):
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
                    "ports": ["0", "1"],
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

    def buildPeersDatabasesOrg(self, org: Organization):
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
                "ports": ["0", "1"],
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

    def buildPeer(self, peer: Peer):
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
            "ports": ["0", "1"],
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

    def buildNewOrganization(self, org: Organization):
        self.buildNewOrgCa(org)
        self.buildIdentitiesOrg(org)
        self.buildPeersDatabasesOrg(org)
        self.startingPDOrg(org)

    def buildNewOrgCa(self, org: Organization):
        console.print("[bold white]# Building and starting " + org.name + " CA[/]")

        pathfabricca = "domains/" + self.domain.name + "/compose/"

        with open(pathfabricca + "compose-ca.yaml", encoding="utf-8") as yamlca_file:
            cadata = yaml.load(yamlca_file)

        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
        }

        self.buildFoldersOrg(org)
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
        run.startCANew(org.name)

    def buildNewPeer(self, org: Organization, peer: Peer):
        self.buildFolderPeer(org, peer)
        self.buildIdentitiesPeer(org, peer)
        self.buildPeer(peer)
        self.startingNewPeer(peer)

    def startingOPD(self):
        console.print("[bold white]# Starting orderer, peers and databases[/]")

        run = Run(self.domain)
        run.startingOPD()

    def startingPDOrg(self, org: Organization):
        console.print("[bold white]# Starting " + org.name + " peers and databases[/]")

        run = Run(self.domain)
        run.startingPDOrg(org)

    def startingNewPeer(self, peer: Peer):
        console.print("[bold white]# Starting new peer " + peer.name + "[/]")

        run = Run(self.domain)
        run.startingPD(peer)
