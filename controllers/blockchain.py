import json
import os
import shutil
import time
from pathlib import Path

import docker
import ruamel.yaml
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

        with open(config + "configtx.yaml", encoding="utf-8") as cftx:
            datacfg = yaml.load(cftx)

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
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )
        datacfg["Organizations"][0]["Policies"]["Writers"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )
        datacfg["Organizations"][0]["Policies"]["Admins"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )

        datacfg["Organizations"][0]["OrdererEndpoints"] = [
            self.domain.orderer.name
            + "."
            + self.domain.name
            + ":"
            + str(self.domain.orderer.generallistenport)
        ]

        datacfg["Organizations"][0]["AnchorPeers"] = []
        datacfg["Application"]["Organizations"] = []

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
                    datacfg["Application"]["Organizations"].append(organization)
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

        out_file = config + "configtx.json"
        with open(out_file, "w", encoding="utf-8") as fpo:
            json.dump(datacfg, fpo, indent=2)

        with open(config + "configtx.yaml", "w", encoding="utf-8") as cftx:
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

        pathchannel = Path("domains/" + self.domain.name + "/channel-artifacts")
        block = (
            str(Path().absolute())
            + "/"
            + str(pathchannel)
            + "/"
            + self.domain.networkname
            + ".block"
        )

        os.environ["BLOCKFILE"] = block

        config = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/peercfg"
        )

        PEER_CA = (
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/peerOrganizations/"
            + org.name
            + "/tlsca"
            + "/tlsca."
            + org.name
            + "-cert.pem"
        )

        PEER_MSP = (
            str(Path().absolute())
            + "/domains/"
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

        PEER_ADDRESS = "localhost:" + str(peer.peerlistenport)

        os.environ["FABRIC_CFG_PATH"] = config
        os.environ["CORE_PEER_TLS_ENABLED"] = "true"
        os.environ["CORE_PEER_LOCALMSPID"] = org.name + "MSP"
        os.environ["CORE_PEER_TLS_ROOTCERT_FILE"] = PEER_CA
        os.environ["CORE_PEER_MSPCONFIGPATH"] = PEER_MSP
        os.environ["CORE_PEER_ADDRESS"] = PEER_ADDRESS

        os.system(str(Path().absolute()) + "/bin/peer channel join -b " + block)

        console.print("")
        console.print("## Waiting Peer...")
        console.print("")
        time.sleep(5)

    def buildNewOrganization(self, org: Organization):
        console.print("")
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        console.print("[bold white]# Creating org configtx file[/]")
        console.print("")
        config = str(Path().absolute()) + "/domains/" + self.domain.name + "/config/"

        configbuild = config + "build/"

        pathconfigbuild = Path(configbuild)
        pathconfigbuild.mkdir(parents=True, exist_ok=True)

        datacfg = {"Organizations": []}

        for peer in org.peers:
            if peer.name.split(".")[0] == "peer1":
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

        with open(configbuild + "configtx.yaml", "w", encoding="utf-8") as cftx:
            yaml.dump(datacfg, cftx)

        self.generateOrgDefinition(org)

        self.fetchChannelConfig(org)

        self.mergeConfigtx()

    def generateOrgDefinition(self, org: Organization):
        console.print("[bold white]# Generating org definition[/]")
        console.print("")
        configbuild = (
            str(Path().absolute()) + "/domains/" + self.domain.name + "/config/build/"
        )

        os.environ["FABRIC_CFG_PATH"] = configbuild

        os.system(
            str(Path().absolute())
            + "/bin/configtxgen -printOrg "
            + org.name
            + "MSP > "
            + configbuild
            + org.name
            + ".json"
        )

        with open(configbuild + org.name + ".json", encoding="utf-8") as f:
            configjson = json.load(f)

        configjson["values"]["AnchorPeers"] = {
            "mod_policy": "Admins",
            "value": {
                "anchor_peers": [
                    {
                        "host": org.peers[0].name + "." + self.domain.name,
                        "port": org.peers[0].peerlistenport,
                    }
                ]
            },
            "version": "0",
        }

        with open(configbuild + org.name + ".json", "w", encoding="utf-8") as f:
            json.dump(configjson, f, indent=2)

    def fetchChannelConfig(self, orgnew: Organization):
        console.print("")
        console.print("[bold white]# Fetching channel config[/]")
        console.print("")

        orderer = self.domain.orderer.name + "." + self.domain.name
        newpeer = orgnew.peers[0]

        cliextpath = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/"
        extconfigupttx = cliextpath + "config/build/"

        clipath = "/etc/hyperledger/organizations/"
        # configupttx = clipath + "config/"
        blockpath = clipath + "channel-artifacts/"

        configupttxlocal = (
            str(Path().absolute()) + "/domains/" + self.domain.name + "/config/build/"
        )

        CLIORDERER_CA = (
            cliextpath
            + "ordererOrganizations/tlsca/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        ORDERER_CA = (
            clipath
            + "ordererOrganizations/tlsca/tlsca."
            + self.domain.name
            + "-cert.pem"
        )

        console.print("[bold white]# Updating config[/]")
        console.print("")

        command = (
            "peer channel fetch config "
            + extconfigupttx
            + "config_block.pb -o "
            + orderer
            + ":"
            + str(self.domain.orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + orderer
            + " -c "
            + self.domain.networkname
            + " --tls --cafile "
            + CLIORDERER_CA
        )

        clidocker = client.containers.get("cli")
        envvar = self.envVariables()
        clidocker.exec_run(command, environment=envvar)

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
            + "config_block.json > "
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
            + "config.pb"
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
            + "config.pb --updated "
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

        for org in self.domain.organizations:
            if org.name != orgnew.name:
                for peer in org.peers:
                    if peer.name.split(".")[0] == "peer1":
                        ### SIGN AS OTHER ORG ADMINS
                        console.print(
                            "[bold white]# Signing config transaction by org "
                            + org.name
                            + "[/]"
                        )
                        console.print("")
                        command = (
                            "peer channel signconfigtx -f "
                            + extconfigupttx
                            + orgnew.name
                            + "_update_in_envelope.pb"
                        )

                        clidocker = client.containers.get("cli")
                        envvar = self.envVariables(org)
                        clidocker.exec_run(command, environment=envvar)

                        console.print("# Waiting Peer...")
                        console.print("")
                        time.sleep(5)

        ### SEND AS ORDERER ADMIN
        console.print("[bold white]# Updating channel[/]")
        console.print("")

        command = (
            "peer channel update -f "
            + extconfigupttx
            + orgnew.name
            + "_update_in_envelope.pb -c "
            + self.domain.networkname
            + " -o "
            + orderer
            + ":"
            + str(self.domain.orderer.generallistenport)
            + " --tls --cafile "
            + CLIORDERER_CA
        )

        clidocker = client.containers.get("cli")
        envvar = self.envVariables(ord=True)
        clidocker.exec_run(command, environment=envvar)

        console.print("# Waiting Orderer...")
        console.print("")
        time.sleep(5)

        block = blockpath + self.domain.networkname + ".block"

        console.print(
            "[bold white]# Fetching channel config block from orderer to org "
            + orgnew.name
            + "[/]"
        )
        console.print("")

        command = (
            "peer channel fetch 0 "
            + block
            + " -o "
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

        clidocker = client.containers.get(newpeer.name + "." + self.domain.name)
        envvar = self.envVariables(orgnew, newpeer)
        clidocker.exec_run(command, environment=envvar)

        console.print("# Waiting Peer...")
        console.print("")
        time.sleep(5)

        self.joinChannelOrg(orgnew)

    def envVariables(
        self, org: Organization = None, peer: Peer = None, ord: bool = None
    ):
        path = "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/"

        if org is None:
            org = self.domain.organizations[0]

        if peer is None:
            peer = org.peers[0]
        else:
            path = "/etc/hyperledger/organizations/"

        clidataORDERER_CA = (
            path + "ordererOrganizations/tlsca/tlsca." + self.domain.name + "-cert.pem"
        )
        clidataORDERER_ADMIN_TLS_SIGN_CERT = (
            path + "ordererOrganizations/orderer/tls/server.crt"
        )
        clidataORDERER_ADMIN_TLS_PRIVATE_KEY = (
            path + "ordererOrganizations/orderer/tls/server.key"
        )

        clidataORDERER_GENERAL_LOCALMSPDIR = (
            path + "ordererOrganizations/users/Admin@" + self.domain.name + "/msp"
        )
        clidataCORE_PEER_LOCALMSPID = org.name + "MSP"
        clidataCORE_PEER_TLS_ROOTCERT_FILE = (
            path
            + "organizations/peerOrganizations/"
            + org.name
            + "/tlsca/tlsca."
            + org.name
            + "-cert.pem"
        )
        clidataCORE_PEER_MSPCONFIGPATH = (
            path
            + "peerOrganizations/"
            + org.name
            + "/users/Admin@"
            + org.name
            + "."
            + self.domain.name
            + "/msp"
        )
        clidataCORE_PEER_ADDRESS = (
            peer.name + "." + self.domain.name + ":" + str(peer.peerlistenport)
        )
        clidataCHANNEL_NAME = self.domain.networkname

        envvar = {
            "GOPATH": "/opt/gopath",
            "FABRIC_LOGGING_SPEC": "INFO",
            "FABRIC_CFG_PATH": "/etc/hyperledger/peercfg",
            "CORE_PEER_TLS_ENABLED": "true",
            "ORDERER_CA": clidataORDERER_CA,
            "ORDERER_ADMIN_TLS_SIGN_CERT": clidataORDERER_ADMIN_TLS_SIGN_CERT,
            "ORDERER_ADMIN_TLS_PRIVATE_KEY": clidataORDERER_ADMIN_TLS_PRIVATE_KEY,
            "CORE_PEER_LOCALMSPID": "OrdererMSP"
            if ord
            else clidataCORE_PEER_LOCALMSPID,
            "CORE_PEER_TLS_ROOTCERT_FILE": clidataCORE_PEER_TLS_ROOTCERT_FILE,
            "CORE_PEER_MSPCONFIGPATH": clidataORDERER_GENERAL_LOCALMSPDIR
            if ord
            else clidataCORE_PEER_MSPCONFIGPATH,
            "CORE_PEER_ADDRESS": clidataCORE_PEER_ADDRESS,
            "CHANNEL_NAME": clidataCHANNEL_NAME,
        }

        return envvar

    def mergeConfigtx(self):
        path = str(Path().absolute()) + "/domains/" + self.domain.name
        config = path + "/config/"
        build = config + "build/"

        with open(config + "configtx.yaml", encoding="utf-8") as cftx:
            datacfg = yaml.load(cftx)

        with open(build + "configtx.yaml", encoding="utf-8") as bcftx:
            databuild = yaml.load(bcftx)

        neworg = databuild["Organizations"][0]

        datacfg["Organizations"].append(neworg)
        datacfg["Organizations"][0]["AnchorPeers"].append(neworg["AnchorPeers"][0])
        datacfg["Application"]["Organizations"].append(neworg)
        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"][
            "Organizations"
        ].append(neworg)

        with open(config + "configtx.yaml", "w", encoding="utf-8") as cftx:
            datacfg = yaml.dump(datacfg, cftx)

        os.system("rm -fR " + build)
