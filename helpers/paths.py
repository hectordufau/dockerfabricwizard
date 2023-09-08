import os
import shutil
from pathlib import Path

from rich.console import Console

from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

console = Console()

APPPATH = str()
DOMAINPATH = str()
FABRICCAPATH = str()
ORDERERORGPATH = str()
FABRICCAPATH = str()
ORDERERORGPATH = str()
PEERORGPATH = str()
CCCRYPTOPATH = str()
CHANNELARTIFACTSPATH = str()
COMPOSEPATH = str()
FIREFLYPATH = str()
FCADOMAINPATH = str()
ORDDOMAINPATH = str()
PEERCFGPATH = str()
ORGPATH = str()
PEERPATH = str()

CONFIGPATH = APPPATH + "config/"
CONFIGPEER = CONFIGPATH + "core.yaml"
CONFIGTX = CONFIGPATH + "configtx.yaml"
CONFIGORDERER = CONFIGPATH + "orderer.yaml"


class Paths:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain
        APPPATH = str(Path().absolute()) + "/"
        DOMAINPATH = APPPATH + self.domain.name + "/"
        FABRICCAPATH = DOMAINPATH + "fabricca/"
        ORDERERORGPATH = DOMAINPATH + "ordererOrganizations/"
        PEERORGPATH = DOMAINPATH + "peerOrganizations/"
        CCCRYPTOPATH = DOMAINPATH + "chaincodecrypto/"
        CHANNELARTIFACTSPATH = DOMAINPATH + "channelartifacts/"
        COMPOSEPATH = DOMAINPATH + "compose/"
        FIREFLYPATH = DOMAINPATH + "firefly/"
        FCADOMAINPATH = FABRICCAPATH + "/" + self.domain.ca.name + "/"
        ORDDOMAINPATH = ORDERERORGPATH + "/" + self.domain.orderer.name + "/"

    def build_folders(self):
        console.print("[bold white]# Preparing folders[/]")

        os.system("rm -fR " + FABRICCAPATH)
        os.system("rm -fR " + PEERORGPATH)
        os.system("rm -fR " + ORDERERORGPATH)
        os.system("rm -fR " + CCCRYPTOPATH)
        os.system("rm -fR " + CHANNELARTIFACTSPATH)

        pathcompose = Path(COMPOSEPATH)
        pathcompose.mkdir(parents=True, exist_ok=True)

        pathfirefly = Path(FIREFLYPATH)
        pathfirefly.mkdir(parents=True, exist_ok=True)

        pathfabricca = Path(FCADOMAINPATH)
        pathfabricca.mkdir(parents=True, exist_ok=True)

        pathorderer = Path(ORDDOMAINPATH)
        pathorderer.mkdir(parents=True, exist_ok=True)

        pathchaincode = Path(CCCRYPTOPATH)
        pathchaincode.mkdir(parents=True, exist_ok=True)

        for org in self.domain.organizations:
            self.build_folders_org(org)

    def build_folders_org(self, org: Organization):
        pathfabriccaorg = Path(FABRICCAPATH + org.ca.name)
        pathfabriccaorg.mkdir(parents=True, exist_ok=True)

        pathorgs = Path(PEERORGPATH + org.name)
        pathorgs.mkdir(parents=True, exist_ok=True)

        for peer in org.peers:
            self.build_folder_peer(org, peer)

    def build_folder_peer(self, org: Organization, peer: Peer):
        PEERCFGPATH = PEERORGPATH + "/" + org.name + "/" + peer.name + "/peercfg/"
        pathpeers = Path(PEERCFGPATH)
        pathpeers.mkdir(parents=True, exist_ok=True)

        shutil.copy(
            CONFIGPEER,
            PEERCFGPATH + "core.yaml",
        )
