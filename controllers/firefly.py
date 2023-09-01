import os
import subprocess
import tempfile
import time
import webbrowser
from pathlib import Path

import ruamel.yaml
from rich.console import Console

from controllers.chaincode import ChaincodeDeploy
from models.domain import Domain

console = Console()
yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=2)
yaml.boolean_representation = [f"false", f"true"]


class Firefly:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        console.print("[bold orange1]FIREFLY[/]")
        console.print("")
        if self.checkInstall():
            self.startStack()
        else:
            self.buildConnectionProfiles()
            self.deployFFChaincode()
            self.createStack()
            self.startStack()

    def checkInstall(self) -> bool:
        console.print("[bold white]# Checking Firefly install[/]")
        return os.path.isdir(
            str(Path().home()) + "/.firefly/stacks/" + self.domain.networkname
        )

    def remove(self):
        console.print("[bold white]# Starting Firefly stack[/]")
        os.system(str(Path().absolute()) + "/bin/ff stop " + self.domain.networkname)
        os.system(
            str(Path().absolute()) + "/bin/ff remove -f " + self.domain.networkname
        )

    def buildConnectionProfiles(self):
        console.print("[bold white]# Preparing connection profiles[/]")

        msppath = str(Path().absolute()) + "/domains/" + self.domain.name
        fireflypath = msppath + "/firefly/"

        for org in self.domain.organizations:
            ccp = {
                "certificateAuthorities": {
                    org.name
                    + "."
                    + self.domain.name: {
                        "tlsCACerts": {
                            "path": msppath
                            + "/peerOrganizations/"
                            + org.name
                            + "/msp/tlscacerts/ca.crt"
                        },
                        "url": "https://"
                        + org.ca.name
                        + "."
                        + self.domain.name
                        + ":"
                        + str(org.ca.serverport),
                        "grpcOptions": {
                            "ssl-target-name-override": org.name
                            + "."
                            + self.domain.name
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
                        "cryptoStore": {
                            "path": msppath + "/peerOrganizations/" + org.name + "/msp"
                        },
                        "path": msppath + "/peerOrganizations/" + org.name + "/msp",
                    },
                    "cryptoconfig": {
                        "path": msppath + "/peerOrganizations/" + org.name + "/msp"
                    },
                    "logging": {"level": "info"},
                    "organization": org.name + "." + self.domain.name,
                    "tlsCerts": {
                        "client": {
                            "cert": {
                                "path": msppath
                                + "/peerOrganizations/"
                                + org.name
                                + "/users/Admin@"
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
                            "path": msppath
                            + "/ordererOrganizations/orderer/tls/tlscacerts/tls-localhost-"
                            + str(self.domain.ca.serverport)
                            + "-"
                            + self.domain.ca.name
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
                        "cryptoPath": msppath
                        + "/peerOrganizations/"
                        + org.name
                        + "/msp",
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
                        "path": msppath
                        + "/peerOrganizations/"
                        + org.name
                        + "/"
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
                fireflypath + org.name + "_ccp.yaml", "w", encoding="utf-8"
            ) as yaml_file:
                yaml.dump(ccp, yaml_file)

    def deployFFChaincode(self):
        console.print("[bold white]# Deploy Firefly chaincode[/]")
        fireflycc = str(Path().absolute()) + "/chaincodes/firefly-go"
        chaincode = ChaincodeDeploy(self.domain, fireflycc)
        chaincode.buildFirefly()

    def createStack(self):
        console.print("[bold white]# Creating Firefly stack[/]")

        msppath = str(Path().absolute()) + "/domains/" + self.domain.name
        fireflypath = msppath + "/firefly/"
        ccpstring = ""
        for org in self.domain.organizations:
            ccpstring = (
                ccpstring
                + " --ccp "
                + fireflypath
                + org.name
                + "_ccp.yaml"
                + " --msp "
                + msppath
                + "/peerOrganizations/"
                + org.name
                + "/msp"
            )

        command = (
            str(Path().absolute())
            + "/bin/ff init fabric "
            + self.domain.networkname
            + " 1"
            + ccpstring
            + " --channel "
            + self.domain.networkname
            + " --chaincode firefly-go"
            + " --sandbox-enabled=false"
            + " -v"
        )

        res = subprocess.call(command, shell=True, universal_newlines=True)

        if res == 0:
            override = {
                "version": "2.1",
                "networks": {
                    "default": {"name": self.domain.networkname, "external": True}
                },
            }

            overridepath = (
                os.environ["HOME"]
                + "/.firefly/stacks/"
                + self.domain.networkname
                + "/docker-compose.override.yml"
            )
            with open(overridepath, "w", encoding="utf-8") as yaml_file:
                yaml.dump(override, yaml_file)

    def startStack(self):
        console.print("[bold white]# Starting Firefly stack[/]")
        command = (
            str(Path().absolute()) + "/bin/ff start " + self.domain.networkname + " --no-rollback -v"
        )
        console.print("# Waiting Firefly start...")

        res = subprocess.call(command, shell=True, universal_newlines=True)

        if res == 0:
            webbrowser.open("http://127.0.0.1:5000/ui")
            webbrowser.open_new_tab("http://127.0.0.1:5000/api")
