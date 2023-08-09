import json
import os

import ruamel.yaml
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from models.domain import Domain

yaml = ruamel.yaml.YAML()
# yaml.preserve_quotes = True
yaml.indent(sequence=3, offset=2)


class Build:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        self.buildConfig()
        self.buildCa()
        self.buildCrypto()

    def buildConfig(self):
        pathdomains = "domains/" + self.domain.name
        isFolderDomainsExist = os.path.exists(pathdomains)

        if not isFolderDomainsExist:
            os.mkdir(pathdomains)

        json_object = json.dumps(self.domain, default=lambda x: x.__dict__, indent=4)
        with open(pathdomains + "/setup.json", "w") as outfile:
            outfile.write(json_object)

        pathfabricca = "domains/" + self.domain.name + "/fabric-ca"
        isFolderCAExist = os.path.exists(pathfabricca)

        if not isFolderCAExist:
            os.mkdir(pathfabricca)

    def buildCrypto(self):
        pass

    def buildCa(self):
        ## ${CONTAINER_CLI_COMPOSE} -f compose/$COMPOSE_FILE_CA -f compose/$CONTAINER_CLI/${CONTAINER_CLI}-$COMPOSE_FILE_CA up -d 2>&1
        pathfabricca = "domains/" + self.domain.name + "/fabric-ca"

        cafile = {
            "version": "3.7",
            "networks": {self.domain.networkname: {"name": self.domain.networkname}},
            "services": {},
        }

        caorderer = {
            "image": "hyperledger/fabric-ca:latest",
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
            "volumes": [
                "../organizations/fabric-ca/ordererOrg:/etc/hyperledger/fabric-ca-server"
            ],
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

        with open(pathfabricca + "/compose-ca.yaml", "w") as yaml_file:
            yaml.dump(cafile, yaml_file)
