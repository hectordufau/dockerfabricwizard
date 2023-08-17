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
        console.print("[bold white]# Preparing folders[/]")
        self.buildFolders()
        console.print("[bold white]# Creating domain config file[/]")
        self.buildConfig()
        console.print("[bold white]# Building and starting CAs[/]")
        self.buildCa()
        console.print("[bold white]# Creating and registering identities[/]")
        self.buildIdentities()
        console.print("[bold white]# Building orderer[/]")
        self.buildOrderer()
        console.print("[bold white]# Building peers[/]")
        self.buildPeers()
        console.print("[bold white]# Building databases[/]")
        self.buildDatabases()
        console.print("[bold white]# Starting orderer, peers and databases[/]")
        self.startingOPD()
        console.print("")

    def buildFolders(self):
        rmfolders = str(Path("domains/" + self.domain.name + "/fabric-ca"))
        os.system("rm -fR " + rmfolders)

        rmfolders = str(Path("domains/" + self.domain.name + "/peerOrganizations"))
        os.system("rm -fR " + rmfolders)

        rmfolders = str(Path("domains/" + self.domain.name + "/ordererOrganizations"))
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
            pathfabriccaorg = Path(
                "domains/" + self.domain.name + "/fabric-ca/" + org.ca.name
            )
            pathfabriccaorg.mkdir(parents=True, exist_ok=True)

            pathorgs = Path(
                "domains/" + self.domain.name + "/peerOrganizations/" + org.name
            )
            pathorgs.mkdir(parents=True, exist_ok=True)

            for peer in org.peers:
                pathpeers = Path(
                    "domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/"
                    + peer.name
                )
                pathpeers.mkdir(parents=True, exist_ok=True)

    def buildConfig(self):
        pathdomains = "domains/" + self.domain.name

        json_object = json.dumps(self.domain, default=lambda x: x.__dict__, indent=4)
        with open(pathdomains + "/setup.json", "w") as outfile:
            outfile.write(json_object)

    def buildCa(self):
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
                "FABRIC_CA_SERVER_CA_NAME=" + self.domain.ca.FABRIC_CA_SERVER_CA_NAME,
                "FABRIC_CA_SERVER_TLS_ENABLED="
                + str(self.domain.ca.FABRIC_CA_SERVER_TLS_ENABLED).lower(),
                "FABRIC_CA_SERVER_PORT=" + str(self.domain.ca.FABRIC_CA_SERVER_PORT),
                "FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS="
                + self.domain.ca.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS,
            ],
            "ports": ["0", "1"],
            "command": "sh -c 'fabric-ca-server start -b admin:adminpw -d'",
            "volumes": [self.domain.ca.volumes],
            "container_name": self.domain.ca.name,
            "networks": [self.domain.networkname],
        }

        caorderer["ports"][0] = DoubleQuotedScalarString(
            f'{str(self.domain.ca.serverport)+":"+str(self.domain.ca.serverport)}'
        )
        caorderer["ports"][1] = DoubleQuotedScalarString(
            f'{str(self.domain.ca.operationslistenport)+":"+str(self.domain.ca.operationslistenport)}'
        )

        cafile["services"][self.domain.ca.name] = caorderer

        for org in self.domain.organizations:
            caorg = {
                "image": "hyperledger/fabric-ca:latest",
                "user": str(os.geteuid()) + ":" + str(os.getgid()),
                "labels": {"service": "hyperledger-fabric"},
                "environment": [
                    "FABRIC_CA_HOME=" + org.ca.FABRIC_CA_HOME,
                    "FABRIC_CA_SERVER_CA_NAME=" + org.ca.FABRIC_CA_SERVER_CA_NAME,
                    "FABRIC_CA_SERVER_TLS_ENABLED="
                    + str(org.ca.FABRIC_CA_SERVER_TLS_ENABLED).lower(),
                    "FABRIC_CA_SERVER_PORT=" + str(org.ca.FABRIC_CA_SERVER_PORT),
                    "FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS="
                    + org.ca.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS,
                ],
                "ports": ["0", "1"],
                "command": "sh -c 'fabric-ca-server start -b admin:adminpw -d'",
                "volumes": [org.ca.volumes],
                "container_name": org.ca.name,
                "networks": [self.domain.networkname],
            }

            caorg["ports"][0] = DoubleQuotedScalarString(
                f'{str(org.ca.serverport)+":"+str(org.ca.serverport)}'
            )
            caorg["ports"][1] = DoubleQuotedScalarString(
                f'{str(org.ca.operationslistenport)+":"+str(org.ca.operationslistenport)}'
            )

            cafile["services"][org.ca.name] = caorg

        with open(pathfabricca + "compose-ca.yaml", "w") as yaml_file:
            yaml.dump(cafile, yaml_file)

        run = Run(self.domain)
        run.startCA()

    def buildIdentities(self):
        for org in self.domain.organizations:
            while True:
                try:
                    container = docker.container.inspect(org.ca.name)
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

            pathorg = Path(
                "domains/" + self.domain.name + "/peerOrganizations/" + org.name
            )

            os.environ["FABRIC_CA_CLIENT_HOME"] = str(pathorg)
            os.system(
                str(Path().absolute())
                + "/bin/fabric-ca-client enroll -u https://admin:adminpw@localhost:"
                + str(org.ca.serverport)
                + " --caname "
                + org.ca.name
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
                        + org.ca.name
                        + ".pem",
                        "OrganizationalUnitIdentifier": "client",
                    },
                    "PeerOUIdentifier": {
                        "Certificate": "cacerts/localhost-"
                        + str(org.ca.serverport)
                        + "-"
                        + org.ca.name
                        + ".pem",
                        "OrganizationalUnitIdentifier": "peer",
                    },
                    "AdminOUIdentifier": {
                        "Certificate": "cacerts/localhost-"
                        + str(org.ca.serverport)
                        + "-"
                        + org.ca.name
                        + ".pem",
                        "OrganizationalUnitIdentifier": "admin",
                    },
                    "OrdererOUIdentifier": {
                        "Certificate": "cacerts/localhost-"
                        + str(org.ca.serverport)
                        + "-"
                        + org.ca.name
                        + ".pem",
                        "OrganizationalUnitIdentifier": "orderer",
                    },
                }
            }

            configpath = "".join([str(Path().absolute()), "/", str(pathorg), "/msp"])
            with open(configpath + "/config.yaml", "w") as yaml_file:
                yaml.dump(configfile, yaml_file)

            cacert = (
                str(Path().absolute()) + "/" + str(pathfabriccaorg) + "/ca-cert.pem"
            )

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
                "domains/"
                + self.domain.name
                + "/peerOrganizations/"
                + org.name
                + "/tlsca"
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
                str(Path().absolute())
                + "/"
                + str(ca)
                + "/ca."
                + org.name
                + "-cert.pem",
            )

            for peer in org.peers:
                console.print("[bold]## Registering " + peer.name + "[/]")
                os.system(
                    str(Path().absolute())
                    + "/bin/fabric-ca-client register "
                    + " --caname "
                    + org.ca.name
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
                        str(Path().absolute())
                        + "/"
                        + str(tlspath)
                        + "/keystore/"
                        + file_name,
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
                    + ".pem",
                    "OrganizationalUnitIdentifier": "client",
                },
                "PeerOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(self.domain.ca.serverport)
                    + "-"
                    + self.domain.ca.name
                    + ".pem",
                    "OrganizationalUnitIdentifier": "peer",
                },
                "AdminOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(self.domain.ca.serverport)
                    + "-"
                    + self.domain.ca.name
                    + ".pem",
                    "OrganizationalUnitIdentifier": "admin",
                },
                "OrdererOUIdentifier": {
                    "Certificate": "cacerts/localhost-"
                    + str(self.domain.ca.serverport)
                    + "-"
                    + self.domain.ca.name
                    + ".pem",
                    "OrganizationalUnitIdentifier": "orderer",
                },
            }
        }

        configpath = "".join([str(Path().absolute()), "/", str(pathorder), "/msp"])
        with open(configpath + "/config.yaml", "w") as yaml_file:
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

    def buildOrderer(self):
        pathorderer = "domains/" + self.domain.name + "/compose/"

        ordfile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "volumes": {self.domain.orderer.name + "." + self.domain.name},
            "services": {},
        }

        orderer = {
            "image": "hyperledger/fabric-orderer:latest",
            # "user": str(os.geteuid()) + ":" + str(os.getgid()),
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

        ordfile["services"][self.domain.ca.name] = orderer

        with open(pathorderer + "compose-orderer.yaml", "w") as yaml_file:
            yaml.dump(ordfile, yaml_file)

    def buildPeers(self):
        pass

    def buildDatabases(self):
        pass

    def startingOPD(self):
        run = Run(self.domain)
        run.startingOPD()
