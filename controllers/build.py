import json
import os
import shutil
from pathlib import Path

import ruamel.yaml
from rich.console import Console
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from controllers.header import Header
from controllers.run import Run
from helpers.commands import Commands
from helpers.paths import Paths
from models.ca import Ca
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
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain
        self.paths = Paths(domain)
        self.configyaml = "config.yaml"
        self.composecayaml = "compose-ca.yaml"

    def build_all(self):
        """Build all config files for hosts and identities to start a Hyperledger Fabric network"""
        os.system("clear")
        header.header()
        console.print("[bold orange1]BUILD[/]")
        console.print("")
        self.paths.build_folders()
        self.build_ca()
        self.build_identities()
        self.build_orderer()
        self.build_peers_databases()
        # self.prepare_firefly() TODO
        self.build_config()
        self.starting_opd()
        console.print("")

    def build_new_organization(self, org: Organization):
        """Build all config files for hosts and identities of a new organization added in a running Hyperledger Fabric network"""
        self.build_new_org_ca(org)
        self.build_identities_org(org)
        self.build_peers_databases_org(org)
        self.prepare_firefly()
        self.build_config()
        self.starting_pd_org(org)

    def build_new_peer(self, org: Organization, peer: Peer):
        """Build all config files and identities for a new peer added in a organization added in a running Hyperledger Fabric network"""
        self.build_identities_peer(org, peer)
        self.build_peer(peer)
        self.build_config()
        self.starting_new_peer(peer)

    def build_ca(self):
        """_summary_"""
        console.print("[bold white]# Building and starting CAs[/]")

        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
        }

        cadomain = self.ca_org_yaml(self.domain.ca)

        caorderer = self.ca_org_yaml(self.domain.caorderer)

        cafile["services"][self.domain.ca.name + "." + self.domain.name] = cadomain
        cafile["services"][
            self.domain.caorderer.name + "." + self.domain.name
        ] = caorderer

        for org in self.domain.organizations:
            caorg = self.ca_org_yaml(org.ca)
            cafile["services"][org.ca.name + "." + self.domain.name] = caorg

        with open(
            self.paths.COMPOSEPATH + self.composecayaml, "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(cafile, yaml_file)

        run = Run(self.domain)
        run.start_ca()

    def build_new_org_ca(self, org: Organization):
        """_summary_"""
        console.print("[bold white]# Building and starting " + org.name + " CA[/]")

        with open(
            self.paths.COMPOSEPATH + self.composecayaml, encoding="utf-8"
        ) as yamlca_file:
            cadata = yaml.load(yamlca_file)

        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
        }

        self.paths.set_org_paths(org)
        caorg = self.ca_org_yaml(org.ca)

        cafile["services"][org.ca.name + "." + self.domain.name] = caorg
        cadata["services"][org.ca.name + "." + self.domain.name] = caorg

        with open(
            self.paths.COMPOSEPATH + "compose-ca-" + org.name + ".yaml",
            "w",
            encoding="utf-8",
        ) as yaml_file:
            yaml.dump(cafile, yaml_file)

        with open(
            self.paths.COMPOSEPATH + self.composecayaml, "w", encoding="utf-8"
        ) as cayaml_file:
            yaml.dump(cadata, cayaml_file)

        run = Run(self.domain)
        run.start_ca_new(org.name)

    def ca_org_yaml(self, ca: Ca) -> dict:
        """_summary_"""
        caorg = {
            "image": "hyperledger/fabric-ca:latest",
            "user": str(os.geteuid()) + ":" + str(os.getgid()),
            "labels": {"service": "hyperledger-fabric"},
            "environment": [
                "FABRIC_CA_HOME=" + ca.FABRIC_CA_HOME,
                "FABRIC_CA_SERVER_CA_NAME="
                + ca.FABRIC_CA_SERVER_CA_NAME
                + "."
                + self.domain.name,
                "FABRIC_CA_SERVER_CSR_CN=" + ca.name + "." + self.domain.name,
                "FABRIC_CA_SERVER_CSR_HOSTS="
                + ca.name
                + "."
                + self.domain.name
                + ","
                + ca.name
                + ",localhost",
                "FABRIC_CA_SERVER_TLS_ENABLED="
                + str(ca.FABRIC_CA_SERVER_TLS_ENABLED).lower(),
                "FABRIC_CA_SERVER_PORT=" + str(ca.FABRIC_CA_SERVER_PORT),
                "FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS="
                + ca.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS,
            ],
            "ports": ["0", "1"],
            "command": "sh -c 'fabric-ca-server start -b admin:adminpw -d'",
            "volumes": [ca.volumes],
            "container_name": ca.name + "." + self.domain.name,
            "networks": [self.domain.networkname],
        }

        caorg["ports"][0] = DoubleQuotedScalarString(
            f'{str(ca.serverport)+":"+str(ca.serverport)}'
        )
        caorg["ports"][1] = DoubleQuotedScalarString(
            f'{str(ca.operationslistenport)+":"+str(ca.operationslistenport)}'
        )

        return caorg

    def config_yaml(self, serverport: int, servername: str, path: str):
        CACERTPEMFILE = (
            "cacerts/localhost-"
            + str(serverport)
            # + "-"
            # + servername.replace(".", "-")
            # + "-"
            # + self.domain.name.replace(".", "-")
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

        with open(path + self.configyaml, "w", encoding="utf-8") as yaml_file:
            yaml.dump(configfile, yaml_file)

    def peer_yaml(self, peer: Peer) -> dict:
        peerdata = {
            "hostname": peer.name + "." + self.domain.name,
            "container_name": peer.name + "." + self.domain.name,
            "image": "hyperledger/fabric-peer:latest",
            "labels": {"service": "hyperledger-fabric"},
            # "user": str(os.geteuid()) + ":" + str(os.getgid()),
            "environment": [
                "FABRIC_CFG_PATH=" + peer.FABRIC_CFG_PATH,
                "FABRIC_LOGGING_SPEC=" + peer.FABRIC_LOGGING_SPEC,
                "CORE_PEER_TLS_ENABLED=" + str(peer.CORE_PEER_TLS_ENABLED).lower(),
                "CORE_PEER_PROFILE_ENABLED="
                + str(peer.CORE_PEER_PROFILE_ENABLED).lower(),
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

        return peerdata

    def database_yaml(self, peer: Peer) -> dict:
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

        return databasedata

    def build_config(self):
        """_summary_"""
        console.print("[bold white]# Creating domain config file[/]")

        json_object = json.dumps(self.domain, default=lambda x: x.__dict__, indent=4)
        with open(
            self.paths.DOMAINPATH + "setup.json", "w", encoding="utf-8"
        ) as outfile:
            outfile.write(json_object)

    def build_identities(self):
        """_summary_"""
        console.print("[bold white]# Creating and registering identities[/]")

        console.print("[bold]## Enroll TLS CA Admin[/]")

        self.config_yaml(
            self.domain.ca.serverport,
            self.domain.ca.name,
            self.paths.CACLIENTDOMAINMSPPATH,
        )

        self.config_yaml(
            self.domain.caorderer.serverport,
            self.domain.caorderer.name,
            self.paths.CAORDERERCACLIENTMSPPATH,
        )

        commands.enroll(
            self.paths.APPPATH,
            self.paths.CACLIENTDOMAINPATH,
            "admin",
            "adminpw",
            self.domain.ca.serverport,
            self.paths.CACERTDOMAINFILE,
        )

        console.print("[bold]## Registering TLS CA Admin Orderer[/]")
        commands.register_orderer(
            self.paths.APPPATH,
            self.paths.CACLIENTDOMAINPATH,
            "orderer",
            "ordererpw",
            self.domain.ca.serverport,
            self.paths.TLSCERTDOMAINFILE,
        )

        console.print("[bold]## Enroll Orderer Org CA Admin [/]")
        commands.enroll(
            self.paths.APPPATH,
            self.paths.CAORDERERCACLIENTPATH,
            "admin",
            "adminpw",
            self.domain.caorderer.serverport,
            self.paths.CACERTORDERERFILE,
        )

        console.print("[bold]## Registering Orderer Org CA Admin :: Orderer[/]")
        commands.register_orderer(
            self.paths.APPPATH,
            self.paths.CAORDERERCACLIENTPATH,
            "orderer",
            "ordererpw",
            self.domain.caorderer.serverport,
            self.paths.CACERTORDERERFILE,
        )

        console.print("[bold]## Registering Orderer Org CA Admin :: Admin[/]")
        commands.register_orderer_admin(
            self.paths.APPPATH,
            self.paths.CAORDERERCACLIENTPATH,
            "ordereradmin",
            "ordereradminpw",
            self.domain.caorderer.serverport,
            self.paths.CACERTORDERERFILE,
        )

        console.print("[bold]## Enroll Orderer Org Admin MSP[/]")
        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.ORDERERORGADMINPATH,
            "admin",
            "adminpw",
            self.domain.caorderer.serverport,
            self.paths.CACERTORDERERFILE,
        )

        commands.enroll_tls(
            self.paths.APPPATH,
            self.paths.ORDERERORGADMINPATH,
            "admin",
            "adminpw",
            self.domain.caorderer.serverport,
            ["localhost"],
            "localhost",
            self.paths.TLSCERTORDERERFILE,
        )

        console.print("[bold]## Enroll Orderer[/]")
        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.ORDDOMAINPATH,
            "orderer",
            "ordererpw",
            self.domain.caorderer.serverport,
            self.paths.CACERTORDERERFILE,
        )

        console.print("[bold]## Enroll Orderer TLS[/]")
        hosts = [
            self.domain.orderer.name + "." + self.domain.name,
            self.domain.orderer.name,
            "localhost",
        ]
        commands.enroll_tls(
            self.paths.APPPATH,
            self.paths.ORDDOMAINPATH,
            "admin",
            "adminpw",
            self.domain.ca.serverport,
            hosts,
            self.domain.orderer.name + "." + self.domain.name,
            self.paths.TLSCERTDOMAINFILE,
        )

        shutil.copy(
            self.paths.CAORDERERCACLIENTMSPPATH + self.configyaml,
            self.paths.ORDDOMAINMSPPATH + self.configyaml,
        )

        shutil.copy(
            self.paths.CAORDERERCACLIENTMSPPATH + self.configyaml,
            self.paths.ORDERERORGMSPPATH + self.configyaml,
        )

        shutil.copy(
            self.paths.ORDERERORGSIGNCERTPATH + "cert.pem",
            self.paths.ORDDOMAINADMINCERTPATH + "cert.pem",
        )
        shutil.copy(
            self.paths.ORDSIGNCERTPATH + "cert.pem",
            self.paths.ORDSIGNCERTPATH + "cert.crt",
        )

        for file_name in os.listdir(self.paths.ORDKEYSTOREPATH):
            shutil.copy(
                self.paths.ORDKEYSTOREPATH + file_name,
                self.paths.ORDKEYSTOREPATH + "key.pem",
            )

        for file_name in os.listdir(self.paths.ORDTLSCAPATH):
            shutil.copy(
                self.paths.ORDTLSCAPATH + file_name,
                self.paths.ORDTLSCAPATH + "tls-cert.pem",
            )
            shutil.copy(
                self.paths.ORDTLSCAPATH + file_name,
                self.paths.ORDTLSCAMSPPATH + "tlsca-cert.pem",
            )

        for org in self.domain.organizations:
            self.build_identities_org(org)

    def build_identities_org(self, org: Organization):
        """_summary_"""

        self.paths.set_org_paths(org)

        self.config_yaml(
            org.ca.serverport,
            org.ca.name,
            self.paths.CAORGCACLIENTMSPPATH,
        )

        console.print("[bold]## Enroll Org CA Admin[/]")
        commands.enroll(
            self.paths.APPPATH,
            self.paths.CAORGCACLIENTPATH,
            "admin",
            "adminpw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        console.print("[bold]## Enroll Org CA Admin MSP[/]")
        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.CAORGCACLIENTPATH,
            "admin",
            "adminpw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        console.print("[bold]## Register Org CA Admin :: Admin[/]")
        commands.register_admin(
            self.paths.APPPATH,
            self.paths.CAORGCACLIENTPATH,
            org.name + "admin",
            org.name + "adminpw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        console.print("[bold]## Register Org CA Admin :: User[/]")
        commands.register_user(
            self.paths.APPPATH,
            self.paths.CAORGCACLIENTPATH,
            "user",
            "userpw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        console.print("[bold]## Enroll Org Admin[/]")
        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.ORGCACLIENTPATH,
            "admin",
            "adminpw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        commands.enroll_tls(
            self.paths.APPPATH,
            self.paths.ORGCACLIENTPATH,
            "admin",
            "adminpw",
            org.ca.serverport,
            ["localhost"],
            "localhost",
            self.paths.TLSCERTORGFILE,
        )

        shutil.copy(
            self.paths.CAORGCACLIENTMSPPATH + self.configyaml,
            self.paths.ORGMSPPATH + self.configyaml,
        )

        for peer in org.peers:
            self.build_identities_peer(org, peer)

    def build_identities_peer(self, org: Organization, peer: Peer):
        """_summary_"""

        self.paths.set_peer_paths(org, peer)
        peername = peer.name.replace(".", "")

        console.print("[bold]## Registering TLS CA Admin Peer[/]")
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
            peername,
            peername + "pw",
            self.domain.ca.serverport,
            self.paths.TLSCERTDOMAINFILE,
        )

        console.print("[bold]## Register Org CA Admin :: Peer[/]")
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
            peername,
            peername + "pw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        console.print("[bold]## Enroll Peer MSP[/]")
        commands.enroll_msp(
            self.paths.APPPATH,
            self.paths.PEERPATH,
            peername,
            peername + "pw",
            org.ca.serverport,
            self.paths.CACERTORGFILE,
        )

        console.print("[bold]## Enroll Peer TLS[/]")
        hosts = [peer.name + "." + self.domain.name, peer.name, "localhost"]
        commands.enroll_tls(
            self.paths.APPPATH,
            self.paths.PEERPATH,
            "admin",
            "adminpw",
            self.domain.ca.serverport,
            hosts,
            peer.name + "." + self.domain.name,
            self.paths.TLSCERTDOMAINFILE,
        )

        shutil.copy(
            self.paths.CAORGCACLIENTMSPPATH + self.configyaml,
            self.paths.PEERMSPPATH + self.configyaml,
        )

        shutil.copy(
            self.paths.ORGSIGNCERTPATH + "cert.pem",
            self.paths.PEERADMINCERTPATH + "cert.pem",
        )

        shutil.copy(
            self.paths.PEERSIGNCERTPATH + "cert.pem",
            self.paths.PEERSIGNCERTPATH + "cert.crt",
        )

        for file_name in os.listdir(self.paths.PEERKEYSTOREPATH):
            shutil.copy(
                self.paths.PEERKEYSTOREPATH + file_name,
                self.paths.PEERKEYSTOREPATH + "key.pem",
            )

        for file_name in os.listdir(self.paths.PEERTLSCAPATH):
            shutil.copy(
                self.paths.PEERTLSCAPATH + file_name,
                self.paths.PEERTLSCAPATH + "tls-cert.pem",
            )
            shutil.copy(
                self.paths.PEERTLSCAPATH + file_name,
                self.paths.PEERTLSCAMSPPATH + "tlsca-cert.pem",
            )

        shutil.copy(
            self.paths.TLSCERTDOMAINFILE,
            self.paths.ORDERERORGTLSCAMSPPATH + "tls-cert.pem",
        )

    def build_orderer(self):
        """_summary_"""
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
        """_summary_"""
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

        clidataORDERER_CA = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/orderer/tls/ca-root"
        clidataORDERER_ADMIN_TLS_SIGN_CERT = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/orderer/tls/server.crt"
        clidataORDERER_ADMIN_TLS_PRIVATE_KEY = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/orderer/tls/server.key"
        clidataORDERER_GENERAL_LOCALMSPDIR = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/admin/msp"
        clidataCORE_PEER_LOCALMSPID = self.domain.organizations[0].name + "MSP"
        clidataCORE_PEER_TLS_ROOTCERT_FILE = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/"
            + cliorg.name
            + "/"
            + clipeer.name
            + "/tls/ca-root.crt"
        )
        clidataCORE_PEER_MSPCONFIGPATH = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/"
            + cliorg.name
            + "/"
            + clipeer.name
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
                "CORE_PEER_ID=" + "cli." + self.domain.name,
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
                peerdata = self.peer_yaml(peer)

                clidata["depends_on"].append(peer.name + "." + self.domain.name)

                peerfile["volumes"][peer.name + "." + self.domain.name] = {}

                peerfile["services"][peer.name + "." + self.domain.name] = peerdata

                databasedata = self.database_yaml(peer)

                peerfile["services"][
                    peer.database.name + "." + self.domain.name
                ] = databasedata

        with open(pathpeer + "compose-net.yaml", "w", encoding="utf-8") as yaml_file:
            yaml.dump(peerfile, yaml_file)

    def build_peers_databases_org(self, org: Organization):
        """_summary_"""
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
            peerdata = self.peer_yaml(peer)

            peerfile["volumes"][peer.name + "." + self.domain.name] = {}
            datapeer["volumes"][peer.name + "." + self.domain.name] = {}

            peerfile["services"][peer.name + "." + self.domain.name] = peerdata
            datapeer["services"][peer.name + "." + self.domain.name] = peerdata

            databasedata = self.database_yaml(peer)

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
        """_summary_"""
        console.print("[bold white]# Building " + peer.name + " and database[/]")

        with open(
            self.paths.COMPOSEPATH + "compose-net.yaml", encoding="utf-8"
        ) as yamlpeer_file:
            datapeer = yaml.load(yamlpeer_file)

        peerfile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "volumes": {},
            "services": {},
        }

        peerdata = self.peer_yaml(peer)

        peerfile["volumes"][peer.name + "." + self.domain.name] = {}
        datapeer["volumes"][peer.name + "." + self.domain.name] = {}

        peerfile["services"][peer.name + "." + self.domain.name] = peerdata
        datapeer["services"][peer.name + "." + self.domain.name] = peerdata

        databasedata = self.database_yaml(peer)

        peerfile["services"][peer.database.name + "." + self.domain.name] = databasedata
        datapeer["services"][peer.database.name + "." + self.domain.name] = databasedata

        with open(
            self.paths.COMPOSEPATH + "compose-net-" + peer.name + ".yaml",
            "w",
            encoding="utf-8",
        ) as yaml_file:
            yaml.dump(peerfile, yaml_file)

        with open(
            self.paths.COMPOSEPATH + "compose-net.yaml", "w", encoding="utf-8"
        ) as yamlpeer_file:
            yaml.dump(datapeer, yamlpeer_file)

    def prepare_firefly(self):
        """_summary_"""
        # TODO
        for i, org in enumerate(self.domain.organizations):
            ## Copy MSP Users
            self.paths.set_org_paths(org)
            
            ## Copy Orderer
            shutil.copytree(
                self.paths.ORDDOMAINPATH,
                self.paths.ORGMSPPATH + "orderer",
            )

            dir_path = self.paths.ORGMSPPATH + "keystore/"
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
                self.paths.set_peer_paths(org, peer)
                shutil.copytree(
                    self.paths.PEERPATH,
                    self.paths.ORGMSPPATH + peer.name,
                )

    def starting_opd(self):
        """_summary_"""
        console.print("[bold white]# Starting orderer, peers and databases[/]")

        run = Run(self.domain)
        run.starting_opd()

    def starting_pd_org(self, org: Organization):
        """_summary_"""
        console.print("[bold white]# Starting " + org.name + " peers and databases[/]")

        run = Run(self.domain)
        run.starting_pd_org(org)

    def starting_new_peer(self, peer: Peer):
        """_summary_"""
        console.print("[bold white]# Starting new peer " + peer.name + "[/]")

        run = Run(self.domain)
        run.starting_pd(peer)
