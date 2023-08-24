import json
import os
import shutil
import time
from pathlib import Path

import docker
import ruamel.yaml

# from python_on_whales import DockerClient
from rich.console import Console

from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=1)
yaml.boolean_representation = [f"false", f"true"]
console = Console()
client = docker.from_env()


class Blockchain:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        self.genesisBlock()
        console.print("")
        self.createChannel()
        console.print("")
        self.joinChannel()
        console.print("")

    def genesisBlock(self):
        console.print("[bold white]# Creating genesis block[/]")
        console.print("")
        # Preparing configtx
        config = str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"
        pathconfig = Path(config)
        pathconfig.mkdir(parents=True, exist_ok=True)

        origconfig = str(Path().absolute()) + "/config/configtx.yaml"

        shutil.copy(
            origconfig,
            config + "configtx.yaml",
        )

        with open(config + "configtx.yaml") as cftx:
            datacfg = yaml.load(cftx)

        datacfg["Organizations"][0][
            "Name"
        ] = self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
        datacfg["Organizations"][0][
            "ID"
        ] = self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
        datacfg["Organizations"][0]["MSPDir"] = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + "msp"
        )
        datacfg["Organizations"][0]["Policies"]["Readers"]["Rule"] = (
            "OR('"
            + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
            + ".admin', '"
            + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
            + ".peer', '"
            + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
            + ".client')"
        )
        datacfg["Organizations"][0]["Policies"]["Writers"]["Rule"] = (
            "OR('"
            + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
            + ".admin', '"
            + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
            + ".client')"
        )
        datacfg["Organizations"][0]["Policies"]["Admins"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".admin')"
        )
        datacfg["Organizations"][0]["Policies"]["Endorsement"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".peer')"
        )

        datacfg["Organizations"][0]["OrdererEndpoints"] = [
            self.domain.orderer.name
            + "."
            + self.domain.name
            + ":"
            + str(self.domain.orderer.generallistenport)
        ]

        datacfg["Organizations"][0]["AnchorPeers"] = []

        for org in self.domain.organizations:
            for peer in org.peers:
                if peer.name.split(".")[0] == "peer1":
                    anchorpeer = {
                        "Host": peer.name + "." + self.domain.name,
                        "Port": peer.peerlistenport,
                    }
                    datacfg["Organizations"][0]["AnchorPeers"].append(anchorpeer)

                    organization = {
                        "Name": peer.CORE_PEER_LOCALMSPID,
                        "ID": peer.CORE_PEER_LOCALMSPID,
                        "MSPDir": (
                            str(Path().absolute())
                            + "/domains/"
                            + self.domain.name
                            + "/peerOrganizations/"
                            + org.name
                            + "/msp"
                        ),
                        "AnchorPeers": [
                            {
                                "Host": peer.name + "." + self.domain.name,
                                "Port": peer.peerlistenport,
                            }
                        ],
                        "Policies": {
                            "Readers": {
                                "Type": "Signature",
                                "Rule": (
                                    "OR('"
                                    + peer.CORE_PEER_LOCALMSPID
                                    + ".admin', '"
                                    + peer.CORE_PEER_LOCALMSPID
                                    + ".peer', '"
                                    + peer.CORE_PEER_LOCALMSPID
                                    + ".client')"
                                ),
                            },
                            "Writers": {
                                "Type": "Signature",
                                "Rule": (
                                    "OR('"
                                    + peer.CORE_PEER_LOCALMSPID
                                    + ".admin', '"
                                    + peer.CORE_PEER_LOCALMSPID
                                    + ".client')"
                                ),
                            },
                            "Admins": {
                                "Type": "Signature",
                                "Rule": (
                                    "OR('" + peer.CORE_PEER_LOCALMSPID + ".admin')"
                                ),
                            },
                            "Endorsement": {
                                "Type": "Signature",
                                "Rule": (
                                    "OR('" + peer.CORE_PEER_LOCALMSPID + ".peer')"
                                ),
                            },
                        },
                    }

                    datacfg["Organizations"].append(organization)
                    datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"][
                        "Organizations"
                    ].append(organization)

        datacfg["Orderer"]["OrdererType"] = "etcdraft"
        datacfg["Orderer"]["Addresses"] = [
            self.domain.orderer.name
            + "."
            + self.domain.name
            + ":"
            + str(self.domain.orderer.generallistenport)
        ]
        datacfg["Orderer"]["EtcdRaft"]["Consenters"] = [
            {
                "Host": (self.domain.orderer.name + "." + self.domain.name),
                "Port": self.domain.orderer.generallistenport,
                "ClientTLSCert": (
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/ordererOrganizations/"
                    + self.domain.orderer.name
                    + "/tls/server.crt"
                ),
                "ServerTLSCert": (
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/ordererOrganizations/"
                    + self.domain.orderer.name
                    + "/tls/server.crt"
                ),
            },
        ]

        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Orderer"]["Organizations"][0][
            "Policies"
        ]["Admins"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )
        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"]["Organizations"][
            0
        ]["Policies"]["Admins"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )

        out_file = config + "configtx.json"
        with open(out_file, "w") as fpo:
            json.dump(datacfg, fpo, indent=2)

        with open(config + "configtx.yaml", "w") as cftx:
            yaml.dump(datacfg, cftx)

        # Creating gblock
        pathchannel = Path("domains/" + self.domain.name + "/channel-artifacts")
        pathchannel.mkdir(parents=True, exist_ok=True)

        block = (
            str(Path().absolute())
            + "/"
            + str(pathchannel)
            + "/"
            + self.domain.networkname
            + ".block"
        )

        os.system(
            str(Path().absolute())
            + "/bin/configtxgen -configPath "
            + config
            + " -profile SampleAppChannelEtcdRaft -outputBlock "
            + block
            + " -channelID "
            + self.domain.networkname
        )

    def createChannel(self):
        console.print("[bold white]# Creating channel[/]")
        console.print("")
        config = str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"
        pathchannel = Path("domains/" + self.domain.name + "/channel-artifacts")
        block = (
            str(Path().absolute())
            + "/"
            + str(pathchannel)
            + "/"
            + self.domain.networkname
            + ".block"
        )
        os.environ["FABRIC_CFG_PATH"] = config
        os.environ["BLOCKFILE"] = block

        ORDERER_CA = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/tlsca/tlsca."
            + self.domain.name
            + "-cert.pem"
        )
        ORDERER_ADMIN_TLS_SIGN_CERT = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
            + "/tls/server.crt"
        )
        ORDERER_ADMIN_TLS_PRIVATE_KEY = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + self.domain.orderer.name
            + "/tls/server.key"
        )

        console.print("## Waiting Orderer...")
        time.sleep(5)

        os.system(
            str(Path().absolute())
            + "/bin/osnadmin channel join --channelID "
            + self.domain.networkname
            + " --config-block "
            + block
            + " -o localhost:"
            + str(self.domain.orderer.adminlistenport)
            + " --ca-file '"
            + ORDERER_CA
            + "' --client-cert '"
            + ORDERER_ADMIN_TLS_SIGN_CERT
            + "' --client-key '"
            + ORDERER_ADMIN_TLS_PRIVATE_KEY
            + "'"
        )

    def joinChannel(self):
        for org in self.domain.organizations:
            self.joinChannelOrg(org)

    def joinChannelOrg(self, org: Organization):
        for peer in org.peers:
            self.joinChannelPeer(org, peer)

    def joinChannelPeer(self, org: Organization, peer: Peer):
        console.print("[bold white]# Joinning channel " + peer.name + "[/]")
        console.print("")

        pathchannel = "/etc/hyperledger/organizations/channel-artifacts/"

        block = pathchannel + self.domain.networkname + ".block"

        command = "peer channel join -b " + block

        clidocker = client.containers.get(peer.name + "." + self.domain.name)

        clidocker.exec_run(command)

        console.print("## Waiting Peer...")
        console.print("")
        time.sleep(5)

    def buildNewOrganization(self, org: Organization):
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        console.print("[bold white]# Updating configtx file[/]")
        console.print("")
        config = str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"
        with open(config + "configtx.yaml", encoding="utf-8") as cftx:
            datacfg = yaml.load(cftx)

        for peer in org.peers:
            if peer.name.split(".")[0] == "peer1":
                anchorpeer = {
                    "Host": peer.name + "." + self.domain.name,
                    "Port": peer.peerlistenport,
                }
                datacfg["Organizations"][0]["AnchorPeers"].append(anchorpeer)

                organization = {
                    "Name": peer.CORE_PEER_LOCALMSPID,
                    "ID": peer.CORE_PEER_LOCALMSPID,
                    "MSPDir": (
                        str(Path().absolute())
                        + "/domains/"
                        + self.domain.name
                        + "/peerOrganizations/"
                        + org.name
                        + "/msp"
                    ),
                    "AnchorPeers": [
                        {
                            "Host": peer.name + "." + self.domain.name,
                            "Port": peer.peerlistenport,
                        }
                    ],
                    "Policies": {
                        "Readers": {
                            "Type": "Signature",
                            "Rule": (
                                "OR('"
                                + peer.CORE_PEER_LOCALMSPID
                                + ".admin', '"
                                + peer.CORE_PEER_LOCALMSPID
                                + ".peer', '"
                                + peer.CORE_PEER_LOCALMSPID
                                + ".client')"
                            ),
                        },
                        "Writers": {
                            "Type": "Signature",
                            "Rule": (
                                "OR('"
                                + peer.CORE_PEER_LOCALMSPID
                                + ".admin', '"
                                + peer.CORE_PEER_LOCALMSPID
                                + ".client')"
                            ),
                        },
                        "Admins": {
                            "Type": "Signature",
                            "Rule": ("OR('" + peer.CORE_PEER_LOCALMSPID + ".admin')"),
                        },
                        "Endorsement": {
                            "Type": "Signature",
                            "Rule": ("OR('" + peer.CORE_PEER_LOCALMSPID + ".peer')"),
                        },
                    },
                }

                datacfg["Organizations"].append(organization)
                datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"][
                    "Organizations"
                ].append(organization)

        out_file = config + "configtx.json"
        with open(out_file, "w", encoding="utf-8") as fpo:
            json.dump(datacfg, fpo, indent=2)

        with open(config + "configtx.yaml", "w", encoding="utf-8") as cftx:
            yaml.dump(datacfg, cftx)

        self.generateOrgDefinition(org)

        self.fetchChannelConfig(org)

    def generateOrgDefinition(self, org: Organization):
        console.print("[bold white]# Generating org definition[/]")
        console.print("")
        config = str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"

        os.environ["FABRIC_CFG_PATH"] = config

        os.system(
            str(Path().absolute())
            + "/bin/configtxgen -printOrg "
            + org.name
            + "MSP > "
            + config
            + org.name
            + ".json"
        )

    def fetchChannelConfig(self, orgnew: Organization):
        console.print("[bold white]# Fetching channel config[/]")
        console.print("")
        org = self.domain.organizations[0]
        peer = org.peers[0]
        newpeer = orgnew.peers[0]

        orderer = self.domain.orderer.name + "." + self.domain.name

        excorg1 = org.name
        excorg2 = orgnew.name

        clipath = "/etc/hyperledger/organizations/"
        pathchannel = clipath + "channel-artifacts/"
        configupttx = clipath + "config/"

        configupttxlocal = (
            str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"
        )

        ORDERER_CA = (
            clipath
            + "ordererOrganizations/orderer/msp/tlscacerts/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        console.print("[bold white]# Updating config[/]")
        console.print("")

        command = (
            "peer channel fetch config "
            + configupttx
            + "config_block.pb -o "
            + orderer
            + ":"
            + str(self.domain.orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + orderer
            + " -c "
            + self.domain.networkname
            + " --tls --cafile "
            + ORDERER_CA
        )

        clidocker = client.containers.get(peer.name + "." + self.domain.name)

        clidocker.exec_run(command)

        console.print("## Waiting Peer...")
        console.print("")
        time.sleep(5)

        os.system(
            str(Path().absolute())
            + "/bin/configtxlator proto_decode --input "
            + configupttxlocal
            + "config_block.pb --type common.Block --output "
            + configupttxlocal
            + "config_block.json"
        )

        os.system(
            "jq .data.data[0].payload.data.config "
            + configupttxlocal
            + "config_block.json >"
            + configupttxlocal
            + "config.json"
        )

        os.system(
            'jq -s \'.[0] * {"channel_group":{"groups":{"Application":{"groups": {"'
            + orgnew.name
            + "MSP\":.[1]}}}}}' "
            + configupttxlocal
            + "config.json "
            + configupttxlocal
            + orgnew.name
            + ".json > "
            + configupttxlocal
            + "modified_config.json"
        )

        os.system(
            str(Path().absolute())
            + "/bin/configtxlator proto_encode --input "
            + configupttxlocal
            + "config.json --type common.Config --output "
            + configupttxlocal
            + "original_config.pb"
        )

        os.system(
            str(Path().absolute())
            + "/bin/configtxlator proto_encode --input "
            + configupttxlocal
            + "modified_config.json --type common.Config --output "
            + configupttxlocal
            + "modified_config.pb"
        )

        os.system(
            str(Path().absolute())
            + "/bin/configtxlator compute_update --channel_id "
            + self.domain.networkname
            + " --original "
            + configupttxlocal
            + "original_config.pb --updated "
            + configupttxlocal
            + "modified_config.pb --output "
            + configupttxlocal
            + "config_update.pb"
        )

        os.system(
            str(Path().absolute())
            + "/bin/configtxlator proto_decode --input "
            + configupttxlocal
            + "config_update.pb --type common.ConfigUpdate --output "
            + configupttxlocal
            + "config_update.json"
        )

        with open(configupttxlocal + "config_update.json", encoding="utf-8") as f:
            config_update = f.read()

        os.system(
            'echo \'{"payload":{"header":{"channel_header":{"channel_id":"'
            + self.domain.networkname
            + '", "type":2}},"data":{"config_update":'
            + config_update
            + "}}}' | jq . >"
            + configupttxlocal
            + "config_update_in_envelope.json"
        )

        os.system(
            str(Path().absolute())
            + "/bin/configtxlator proto_encode --input "
            + configupttxlocal
            + "config_update_in_envelope.json --type common.Envelope --output "
            + configupttxlocal
            + orgnew.name
            + "_update_in_envelope.pb"
        )

        console.print("[bold white]# Signing config transaction[/]")
        console.print("")
        command = (
            "peer channel signconfigtx -f "
            + configupttx
            + orgnew.name
            + "_update_in_envelope.pb"
        )

        clidocker.exec_run(command)

        console.print("[bold white]# Submitting transaction from peers[/]")
        console.print("")
        for org in self.domain.organizations:
            if (org.name != excorg1) and (org.name != excorg2):
                for peer in org.peers:
                    if peer.name.split(".")[0] == "peer1":
                        command = (
                            "peer channel update -f "
                            + configupttx
                            + orgnew.name
                            + "_update_in_envelope.pb -c "
                            + self.domain.networkname
                            + " -o localhost:"
                            + str(self.domain.orderer.generallistenport)
                            + " --ordererTLSHostnameOverride "
                            + orderer
                            + " --tls --cafile "
                            + ORDERER_CA
                        )

                        clidocker = client.containers.get(
                            peer.name + "." + self.domain.name
                        )
                        clidocker.exec_run(command)

        console.print("[bold white]# Fetching channel config block from orderer[/]")
        console.print("")

        block = pathchannel + self.domain.networkname + ".block"

        command = (
            "peer channel fetch 0 "
            + block
            + " -o localhost:"
            + str(self.domain.orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + orderer
            + " -c "
            + self.domain.networkname
            + " --tls --cafile "
            + ORDERER_CA
        )

        clidocker = client.containers.get(newpeer.name + "." + self.domain.name)
        clidocker.exec_run(command)

        self.joinChannelOrg(orgnew)
