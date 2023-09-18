import json
import os
import shutil
import time
from pathlib import Path

import docker
import ruamel.yaml
from rich.console import Console

from controllers.header import Header
from helpers.commands import Commands
from helpers.paths import Paths
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=1)
yaml.boolean_representation = [f"false", f"true"]
console = Console()
client = docker.from_env()
header = Header()
commands = Commands()


class Blockchain:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain
        self.paths = Paths(domain)
        self.configtxyaml = "configtx.yaml"

    def build_all(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        self.genesis_block()
        console.print("")
        self.create_channel()
        console.print("")
        self.join_channel()
        console.print("")

    def genesis_block(self):
        console.print("[bold white]# Creating genesis block[/]")
        console.print("")
        # Preparing configtx
        shutil.copy(
            self.paths.CONFIGTX,
            self.paths.DOMAINCONFIGTXFILE,
        )

        with open(self.paths.DOMAINCONFIGTXFILE, encoding="utf-8") as cftx:
            datacfg = yaml.load(cftx)

        datacfg["Organizations"][0][
            "Name"
        ] = self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
        datacfg["Organizations"][0][
            "ID"
        ] = self.domain.orderer.ORDERER_GENERAL_LOCALMSPID
        datacfg["Organizations"][0]["MSPDir"] = self.paths.ORDDOMAINMSPPATH

        datacfg["Organizations"][0]["Policies"]["Readers"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )
        datacfg["Organizations"][0]["Policies"]["Writers"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )
        datacfg["Organizations"][0]["Policies"]["Admins"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".admin')"
        )
        datacfg["Organizations"][0]["Policies"]["Endorsement"]["Rule"] = (
            "OR('" + self.domain.orderer.ORDERER_GENERAL_LOCALMSPID + ".member')"
        )

        datacfg["Organizations"][0]["OrdererEndpoints"] = [
            self.paths.ORDERERNAME + ":" + str(self.domain.orderer.generallistenport)
        ]

        datacfg["Application"]["Policies"]["LifecycleEndorsement"][
            "Rule"
        ] = "ANY Endorsement"

        datacfg["Application"]["Policies"]["Endorsement"]["Rule"] = "ANY Endorsement"

        datacfg["Organizations"][0]["AnchorPeers"] = []
        datacfg["Application"]["Organizations"] = []

        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Orderer"]["Organizations"] = [
            datacfg["Organizations"][0]
        ]

        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"][
            "Organizations"
        ] = []

        for org in self.domain.organizations:
            for peer in org.peers:
                self.paths.set_peer_paths(org, peer)
                if peer.name.split(".")[0] == "peer1":
                    anchorpeer = {
                        "Host": self.paths.PEERNAME,
                        "Port": peer.peerlistenport,
                    }
                    datacfg["Organizations"][0]["AnchorPeers"].append(anchorpeer)

                    organization = self.organization_yaml(org, peer)

                    datacfg["Organizations"].append(organization)
                    datacfg["Application"]["Organizations"].append(organization)
                    datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"][
                        "Organizations"
                    ].append(organization)

        datacfg["Orderer"]["OrdererType"] = "etcdraft"
        datacfg["Orderer"]["Addresses"] = [
            self.paths.ORDERERNAME + ":" + str(self.domain.orderer.generallistenport)
        ]
        datacfg["Orderer"]["EtcdRaft"]["Consenters"] = [
            {
                "Host": (self.domain.orderer.name + "." + self.domain.name),
                "Port": self.domain.orderer.generallistenport,
                # "ClientTLSCert": (self.paths.ORDDOMAINADMINCERTPATH + "server.crt"),
                "ClientTLSCert": (self.paths.ORDSIGNCERTPATH + "cert.pem"),
                # "ServerTLSCert": (self.paths.ORDDOMAINADMINCERTPATH + "server.crt"),
                "ServerTLSCert": (self.paths.ORDSIGNCERTPATH + "cert.pem"),
            },
        ]

        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Orderer"][
            "Capabilities"
        ] = datacfg["Capabilities"]["Orderer"]

        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"][
            "Capabilities"
        ] = datacfg["Capabilities"]["Application"]

        with open(self.paths.DOMAINCONFIGTXJSONFILE, "w", encoding="utf-8") as fpo:
            json.dump(datacfg, fpo, indent=2)

        with open(self.paths.DOMAINCONFIGTXFILE, "w", encoding="utf-8") as cftx:
            yaml.dump(datacfg, cftx)

        time.sleep(1)

        # Creating gblock
        commands.configtxgen_config_path(
            self.paths.APPPATH,
            self.paths.DOMAINCONFIGPATH,
            self.paths.BLOCKFILE,
            self.domain.networkname,
        )

    def organization_yaml(self, org: Organization, peer: Peer) -> dict:
        self.paths.set_peer_paths(org, peer)
        organization = {
            "Name": peer.CORE_PEER_LOCALMSPID,
            "ID": peer.CORE_PEER_LOCALMSPID,
            "MSPDir": self.paths.PEERMSPPATH,
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

        return organization

    def create_channel(self):
        console.print("[bold white]# Creating channel[/]")
        console.print("")

        commands.osnadmin(
            self.paths.APPPATH,
            self.paths.DOMAINCONFIGPATH,
            self.paths.BLOCKFILE,
            self.domain.networkname,
            self.domain.orderer,
            self.paths.ORDTLSCAPATH
            + "tls-cert.pem",  # ORDDOMAINTLSPATH + "ca-root.crt",
            self.paths.ORDSIGNCERTPATH + "cert.crt",  # ORDDOMAINTLSPATH + "server.crt",
            self.paths.ORDKEYSTOREPATH + "key.pem",  # ORDDOMAINTLSPATH + "server.key",
        )

        console.print("## Waiting Orderer joining channel")
        time.sleep(2)

    def join_channel(self):
        for org in self.domain.organizations:
            self.paths.set_org_paths(org)
            self.join_channel_org(org)

    def join_channel_org(self, org: Organization):
        for peer in org.peers:
            self.paths.set_peer_paths(org, peer)
            self.join_channel_peer(org, peer)

    def join_channel_peer(self, org: Organization, peer: Peer):
        console.print("[bold white]# Joinning channel " + peer.name + "[/]")
        console.print("")

        commands.peer_channel_join(
            org,
            peer,
            self.paths.APPPATH,
            self.paths.BLOCKFILE,
            self.paths.PEERCFGPATH,
            self.paths.PEERTLSCAPATH + "tls-cert.pem",
            self.paths.ORGMSPPATH,
        )

        console.print("")
        console.print("## Waiting Peer...")
        console.print("")
        time.sleep(1)

    def build_new_organization(self, org: Organization):
        os.system("clear")
        header.header()
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        console.print("[bold white]# Creating org configtx file[/]")
        console.print("")

        datacfg = {"Organizations": []}

        for peer in org.peers:
            if peer.name.split(".")[0] == "peer1":
                organization = self.organization_yaml(org, peer)

                datacfg["Organizations"].append(organization)

        with open(
            self.paths.DOMAINCONFIGBUILDPATH + self.configtxyaml, "w", encoding="utf-8"
        ) as cftx:
            yaml.dump(datacfg, cftx)

        self.generate_org_definition(org)

        self.fetch_channel_config(org)

        self.merge_configtx()

    def generate_org_definition(self, org: Organization):
        console.print("[bold white]# Generating org definition[/]")
        console.print("")

        commands.configtxgen_print_org(
            self.paths.APPPATH, self.paths.DOMAINCONFIGBUILDPATH, org
        )

        with open(
            self.paths.DOMAINCONFIGBUILDPATH + org.name + ".json", encoding="utf-8"
        ) as f:
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

        with open(
            self.paths.DOMAINCONFIGBUILDPATH + org.name + ".json", "w", encoding="utf-8"
        ) as f:
            json.dump(configjson, f, indent=2)

    def fetch_channel_config(self, orgnew: Organization):
        console.print("")
        console.print("[bold white]# Fetching channel config[/]")
        console.print("")

        newpeer = orgnew.peers[0]

        CLIORDERER_CA = self.paths.CLIEXTPATH + self.paths.CLIROOTCA

        ORDERER_CA = self.paths.CLIPATH + self.paths.CLIROOTCA

        console.print("[bold white]# Updating config[/]")
        console.print("")

        command = (
            "peer channel fetch config "
            + self.paths.EXTCONFIGTX
            + "config_block.pb -o "
            + self.paths.ORDERERNAME
            + ":"
            + str(self.domain.orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + self.paths.ORDERERNAME
            + " -c "
            + self.domain.networkname
            + " --tls --cafile "
            + CLIORDERER_CA
        )

        clidocker = client.containers.get(self.paths.CLIHOSTNAME)
        envvar = self.env_variables()
        clidocker.exec_run(command, environment=envvar)

        console.print("## Waiting Peer...")
        console.print("")
        time.sleep(1)

        commands.configtxlator_proto_decode(
            self.paths.APPPATH, self.paths.DOMAINCONFIGBUILDPATH, "config_block"
        )
        time.sleep(1)

        commands.jq_export_config(self.paths.DOMAINCONFIGBUILDPATH)
        time.sleep(1)

        commands.jq_export_modified_config(orgnew, self.paths.DOMAINCONFIGBUILDPATH)
        time.sleep(1)

        commands.configtxlator_proto_encode(
            self.paths.APPPATH, self.paths.DOMAINCONFIGBUILDPATH, "config"
        )
        time.sleep(1)

        commands.configtxlator_proto_encode(
            self.paths.APPPATH, self.paths.DOMAINCONFIGBUILDPATH, "modified_config"
        )
        time.sleep(1)

        commands.configtxlator_compute_update(
            self.paths.APPPATH,
            self.domain.networkname,
            self.paths.DOMAINCONFIGBUILDPATH,
        )
        time.sleep(1)

        commands.configtxlator_proto_decode(
            self.paths.APPPATH, self.paths.DOMAINCONFIGBUILDPATH, "config_update", True
        )
        time.sleep(1)

        with open(
            self.paths.DOMAINCONFIGBUILDPATH + "config_update.json", encoding="utf-8"
        ) as f:
            config_update = f.read()
        time.sleep(1)

        commands.echo_payload(
            self.domain.networkname,
            config_update,
            self.paths.DOMAINCONFIGBUILDPATH,
            orgnew,
        )
        time.sleep(1)

        commands.configtxlator_proto_encode(
            self.paths.APPPATH,
            self.paths.DOMAINCONFIGBUILDPATH,
            orgnew.name + "_update_in_envelope",
            True,
        )
        time.sleep(1)

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
                            + self.paths.EXTCONFIGTX
                            + orgnew.name
                            + "_update_in_envelope.pb"
                        )

                        clidocker = client.containers.get(
                            self.paths.CLIHOSTNAME
                        )
                        envvar = self.env_variables(org)
                        clidocker.exec_run(command, environment=envvar)

                        console.print("# Waiting Peer...")
                        console.print("")
                        time.sleep(1)

        console.print("[bold white]# Updating channel[/]")
        console.print("")

        command = (
            "peer channel update -f "
            + self.paths.EXTCONFIGTX
            + orgnew.name
            + "_update_in_envelope.pb -c "
            + self.domain.networkname
            + " -o "
            + self.paths.ORDERERNAME
            + ":"
            + str(self.domain.orderer.generallistenport)
            + " --tls --cafile "
            + CLIORDERER_CA
        )

        clidocker = client.containers.get(self.paths.CLIHOSTNAME)
        envvar = self.env_variables()
        clidocker.exec_run(command, environment=envvar)

        console.print("# Waiting Peers...")
        console.print("")
        time.sleep(1)

        console.print(
            "[bold white]# Fetching channel config block from orderer to org "
            + orgnew.name
            + "[/]"
        )
        console.print("")

        command = (
            "peer channel fetch 0 "
            + self.paths.CLIBLOCKPATH
            + self.domain.networkname
            + ".block"
            + " -o "
            + self.paths.ORDERERNAME
            + ":"
            + str(self.domain.orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + self.paths.ORDERERNAME
            + " -c "
            + self.domain.networkname
            + " --tls --cafile "
            + ORDERER_CA
        )

        clidocker = client.containers.get(newpeer.name + "." + self.domain.name)
        envvar = self.env_variables(orgnew, newpeer)
        clidocker.exec_run(command, environment=envvar)

        console.print("# Waiting Peer...")
        console.print("")
        time.sleep(1)

        self.join_channel_org(orgnew)

    def env_variables(
        self, org: Organization = None, peer: Peer = None, ord: bool = None
    ):
        path = self.paths.CLIEXTPATH

        if org is None:
            org = self.domain.organizations[0]

        if peer is None:
            peer = org.peers[0]
        else:
            path = self.paths.CLIPATH

        clidataORDERER_CA = path + self.paths.CLIROOTCA
        clidataORDERER_ADMIN_TLS_SIGN_CERT = path + self.paths.CLISERVERCRT
        clidataORDERER_ADMIN_TLS_PRIVATE_KEY = path + self.paths.CLISERVERKEY

        clidataORDERER_GENERAL_LOCALMSPDIR = path + "ordererOrganizations/admin/msp"
        clidataCORE_PEER_LOCALMSPID = org.name + "MSP"
        clidataCORE_PEER_TLS_ROOTCERT_FILE = (
            path
            + "organizations/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/tls/tlscacerts/tls-cert.pem"
        )
        clidataCORE_PEER_MSPCONFIGPATH = (
            path + "peerOrganizations/" + org.name + "/admin/msp"
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

    def merge_configtx(self):
        with open(
            self.paths.DOMAINCONFIGPATH + self.configtxyaml, encoding="utf-8"
        ) as cftx:
            datacfg = yaml.load(cftx)

        with open(
            self.paths.DOMAINCONFIGBUILDPATH + self.configtxyaml, encoding="utf-8"
        ) as bcftx:
            databuild = yaml.load(bcftx)

        neworg = databuild["Organizations"][0]

        datacfg["Organizations"].append(neworg)
        anchorpeer = neworg["AnchorPeers"][0]
        datacfg["Application"]["Organizations"].append(neworg)
        datacfg["Profiles"]["SampleAppChannelEtcdRaft"]["Application"][
            "Organizations"
        ].append(neworg)

        datacfg["Organizations"][0]["AnchorPeers"].append(
            {"Host": anchorpeer["Host"], "Port": anchorpeer["Port"]}
        )

        with open(
            self.paths.DOMAINCONFIGPATH + self.configtxyaml, "w", encoding="utf-8"
        ) as cftx:
            yaml.dump(datacfg, cftx)

        with open(
            self.paths.DOMAINCONFIGPATH + "configtx.json", "w", encoding="utf-8"
        ) as fpo:
            json.dump(datacfg, fpo, indent=2)

        # os.system("rm -fR " + self.paths.DOMAINCONFIGBUILDPATH)

        for filename in os.listdir(self.paths.DOMAINCONFIGBUILDPATH):
            file_path = os.path.join(self.paths.DOMAINCONFIGBUILDPATH, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print("Failed to delete %s. Reason: %s" % (file_path, e))

    def rebuild(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]BLOCKCHAIN[/]")
        console.print("")
        self.create_channel()
        console.print("")
        self.join_channel()
        console.print("")
