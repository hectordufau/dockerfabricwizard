import os
import subprocess
import webbrowser

import ruamel.yaml
from rich.console import Console

from controllers.chaincode import ChaincodeDeploy
from controllers.header import Header
from helpers.paths import Paths
from models.chaincode import Chaincode
from models.domain import Domain

console = Console()
yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=2)
yaml.boolean_representation = [f"false", f"true"]
header = Header()


class Firefly:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain
        self.paths: Paths = Paths(domain)

    def build_all(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]FIREFLY[/]")
        console.print("")
        if self.check_install():
            self.start_stack()
        else:
            self.build_connection_profiles()
            self.deploy_firefly_chaincode()
            self.create_stack()
            self.start_stack()

    def check_install(self) -> bool:
        console.print("[bold white]# Checking Firefly install[/]")
        return os.path.isdir(
            self.paths.FIREFLYPATH + "stacks/" + self.domain.networkname
        )

    def remove(self):
        console.print("[bold white]# Stoping Firefly stack[/]")
        os.environ["FIREFLY_HOME"] = self.paths.FIREFLYPATH
        os.system(self.paths.APPPATH + "bin/ff stop " + self.domain.networkname)
        os.system(self.paths.APPPATH + "bin/ff remove -f " + self.domain.networkname)

    def build_connection_profiles(self):
        console.print("[bold white]# Preparing connection profiles[/]")

        for org in self.domain.organizations:
            ccp = {
                "certificateAuthorities": {
                    org.name
                    + "."
                    + self.domain.name: {
                        "tlsCACerts": {
                            "path": "/etc/firefly/organizations/tlscacerts/ca.crt"
                        },
                        "url": "https://"
                        + org.ca.name
                        + "."
                        + self.domain.name
                        + ":"
                        + str(org.ca.serverport),
                        "grpcOptions": {
                            "ssl-target-name-override": "localhost"  #  org.name + "." + self.domain.name
                        },
                        "registrar": {"enrollId": "admin", "enrollSecret": "adminpw"},
                    }
                },
                "channels": {
                    self.domain.networkname: {
                        "orderers": [self.domain.orderer.name + "." + self.domain.name],
                        "peers": {},
                    }
                },
                "client": {
                    "BCCSP": {
                        "security": {
                            "default": {"provider": "SW"},
                            "enabled": True,
                            "hashAlgorithm": "SHA2",
                            "level": 256,
                            "softVerify": True,
                        }
                    },
                    "credentialStore": {
                        "cryptoStore": {"path": "/etc/firefly/organizations"},
                        "path": "/etc/firefly/organizations",
                    },
                    "cryptoconfig": {"path": "/etc/firefly/organizations"},
                    "logging": {"level": "debug"},
                    "organization": org.name + "." + self.domain.name,
                    "tlsCerts": {
                        "client": {
                            "cert": {
                                "path": "/etc/firefly/organizations/users/Admin@"
                                + org.name
                                + "."
                                + self.domain.name
                                + "/msp/signcerts/cert.pem"
                            },
                            "key": {"path": org.keystore},
                        }
                    },
                },
                "orderers": {
                    self.domain.orderer.name
                    + "."
                    + self.domain.name: {
                        "tlsCACerts": {
                            "path": "/etc/firefly/organizations/orderer/tls/tlscacerts/tls-localhost-"
                            + str(self.domain.ca.serverport)
                            + "-"
                            + self.domain.ca.name.replace(".", "-")
                            + "-"
                            + self.domain.name.replace(".", "-")
                            + ".pem"
                        },
                        "url": "grpcs://"
                        + self.domain.orderer.name
                        + "."
                        + self.domain.name
                        + ":"
                        + str(self.domain.orderer.generallistenport),
                    }
                },
                "organizations": {
                    org.name
                    + "."
                    + self.domain.name: {
                        "certificateAuthorities": [org.name + "." + self.domain.name],
                        "cryptoPath": "/etc/firefly/organizations",
                        "mspid": org.name + "MSP",
                        "peers": [],
                    }
                },
                "peers": {},
                "version": "1.1.0%",
            }

            for peer in org.peers:
                ccp["channels"][self.domain.networkname]["peers"][
                    peer.name + "." + self.domain.name
                ] = {
                    "chaincodeQuery": True,
                    "endorsingPeer": True,
                    "eventSource": True,
                    "ledgerQuery": True,
                }

                ccp["organizations"][org.name + "." + self.domain.name]["peers"].append(
                    peer.name + "." + self.domain.name
                )

                ccp["peers"][peer.name + "." + self.domain.name] = {
                    "tlsCACerts": {
                        "path": "/etc/firefly/organizations/"
                        + peer.name
                        + "/tls/tlscacerts/tls-localhost-"
                        + str(org.ca.serverport)
                        + "-"
                        + org.ca.name.replace(".", "-")
                        + "-"
                        + self.domain.name.replace(".", "-")
                        + ".pem"
                    },
                    "url": "grpcs://"
                    + peer.name
                    + "."
                    + self.domain.name
                    + ":"
                    + str(peer.peerlistenport),
                }

            with open(
                self.paths.FIREFLYPATH + org.name + "_ccp.yaml", "w", encoding="utf-8"
            ) as yaml_file:
                yaml.dump(ccp, yaml_file)

    def deploy_firefly_chaincode(self):
        console.print("[bold white]# Deploy Firefly chaincode[/]")
        chaincode = Chaincode()
        chaincode.name = "firefly"
        chaincode.ccport = 9999
        chaincode.invoke = False
        chaincode.usetls = True
        chaincodedeploy = ChaincodeDeploy(self.domain, chaincode)
        chaincodedeploy.build_firefly()

    def create_stack(self):
        console.print("[bold white]# Creating Firefly stack[/]")

        ccpstring = ""
        nffmembers = len(self.domain.organizations)
        for org in self.domain.organizations:
            ccpstring = (
                ccpstring
                + " --ccp "
                + self.paths.FIREFLYPATH
                + org.name
                + "_ccp.yaml"
                + " --msp "
                + self.paths.DOMAINPATH
                + "peerOrganizations/"
                + org.name
                + "/admin/msp"
            )

        os.environ["FIREFLY_HOME"] = self.paths.FIREFLYPATH

        command = (
            self.paths.APPPATH
            + "bin/ff init fabric "
            + self.domain.networkname
            + " "
            + str(nffmembers)
            + ccpstring
            + " --channel "
            + self.domain.networkname
            + " --chaincode firefly"
            + " --sandbox-enabled=false"
            + " -v"
        )

        res = subprocess.call(command, shell=True, universal_newlines=True)

        override = {
            "version": "2.1",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
        }

        overridepath = (
            self.paths.FIREFLYPATH
            + "stacks/"
            + self.domain.networkname
            + "/docker-compose.override.yml"
        )
        with open(overridepath, "w", encoding="utf-8") as yaml_file:
            yaml.dump(override, yaml_file)

    def start_stack(self):
        console.print("[bold white]# Starting Firefly stack[/]")
        os.environ["FIREFLY_HOME"] = self.paths.FIREFLYPATH
        command = (
            self.paths.APPPATH
            + "bin/ff start "
            + self.domain.networkname
            + " --no-rollback -v"
        )
        console.print("# Waiting Firefly start...")

        subprocess.call(command, shell=True, universal_newlines=True)
        webbrowser.open("http://127.0.0.1:5000/ui")
        webbrowser.open("http://127.0.0.1:5000/api")
