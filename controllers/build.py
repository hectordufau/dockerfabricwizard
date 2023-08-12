import json
import os
from pathlib import Path

import ruamel.yaml
from rich.console import Console
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from models.domain import Domain

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=2)
console = Console()


class Build:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        console.print("[bold orange1]BUILD[/]")
        console.print("")
        console.print("[bold]Building resources[/]")
        self.buildFolders()
        self.buildConfig()
        self.buildCa()
        self.buildCrypto()
        console.print("")

    def buildFolders(self):
        rmfolders = str(Path("domains/" + self.domain.name + "/fabric-ca"))
        os.system("rm -fR " + rmfolders)

        pathcompose = Path("domains/" + self.domain.name + "/compose")
        pathcompose.mkdir(parents=True, exist_ok=True)

        pathfabricca = Path(
            "domains/" + self.domain.name + "/fabric-ca/" + self.domain.ca.name
        )
        pathfabricca.mkdir(parents=True, exist_ok=True)

        for org in self.domain.organizations:
            pathfabriccaorg = Path(
                "domains/" + self.domain.name + "/fabric-ca/" + org.ca.name
            )
            pathfabriccaorg.mkdir(parents=True, exist_ok=True)

    def buildConfig(self):
        pathdomains = "domains/" + self.domain.name

        json_object = json.dumps(self.domain, default=lambda x: x.__dict__, indent=4)
        with open(pathdomains + "/setup.json", "w") as outfile:
            outfile.write(json_object)

    def buildCrypto(self):
        pass

    def buildCa(self):
        pathfabricca = "domains/" + self.domain.name + "/compose/"

        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
            #"volumes": {"volume-" + self.domain.ca.name:{}}
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
            #cafile["volumes"]["volume-" + org.ca.name] = {}

        with open(pathfabricca + "compose-ca.yaml", "w") as yaml_file:
            yaml.dump(cafile, yaml_file)
