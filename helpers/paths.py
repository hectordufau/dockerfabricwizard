import os
import shutil
from pathlib import Path

from rich.console import Console

from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

console = Console()


class Paths:
    APPPATH = str()
    DOMAINPATH = str()
    FABRICCAPATH = str()
    ORDERERORGPATH = str()
    PEERORGPATH = str()
    CCCRYPTOPATH = str()
    CHANNELARTIFACTSPATH = str()
    COMPOSEPATH = str()
    FIREFLYPATH = str()
    CADOMAINPATH = str()
    ORDDOMAINPATH = str()
    ORDDOMAINMSPPATH = str()
    ORDDOMAINTLSPATH = str()
    PEERCFGPATH = str()
    ORGPATH = str()
    PEERPATH = str()
    CONFIGPATH = str()
    CONFIGPEER = str()
    CONFIGTX = str()
    CONFIGORDERER = str()
    CACERTDOMAINFILE = str()
    ORDDOMAINADMINMSPPATH = str()
    CADOMAINNAME = str()
    ORDERERORGMSPPATH = str()
    CCCRYPTOTLSPATH = str()
    ORDDOMAINMSPCAPATH = str()
    TLSCERTDOMAINFILE = str()
    CAORGNAME = str()
    CAORGPATH = str()
    TLSCERTORGFILE = str()
    CACERTORGFILE = str()
    ORGMSPPATH = str()
    PEERNAME = str()
    PEERMSPPATH = str()
    PEERTLSPATH = str()
    ORGNAME = str()
    ORGUSERMSPPATH = str()
    ORGADMINMSPPATH = str()
    ORDERERNAME = str()
    PEERTLSCAPATH = str()

    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain
        # Application Path
        Paths.APPPATH = str(Path().absolute()) + "/"

        # Domain Path
        Paths.DOMAINPATH = Paths.APPPATH + "domains/" + self.domain.name + "/"

        # Fabric CAs Paths
        Paths.FABRICCAPATH = Paths.DOMAINPATH + "fabricca/"
        ## Fabric CA Domain
        Paths.CADOMAINNAME = self.domain.ca.name + "." + self.domain.name
        Paths.CADOMAINPATH = Paths.FABRICCAPATH + self.domain.ca.name + "/"
        ## Fabric CA Domain Cert Files
        Paths.CACERTDOMAINFILE = Paths.CADOMAINPATH + "ca-cert.pem"
        Paths.TLSCERTDOMAINFILE = Paths.CADOMAINPATH + "tls-cert.pem"

        # Orderer Organization Paths
        Paths.ORDERERNAME = self.domain.orderer.name + "." + self.domain.name
        Paths.ORDERERORGPATH = Paths.DOMAINPATH + "ordererOrganizations/"
        Paths.ORDERERORGMSPPATH = Paths.ORDERERORGPATH + "msp/"
        ## Orderer Organization Admin MSP
        Paths.ORDDOMAINADMINMSPPATH = (
            Paths.ORDERERORGPATH + "users" + "/Admin@" + self.domain.name + "/msp/"
        )

        ## Orderer Domain Paths
        Paths.ORDDOMAINPATH = Paths.ORDERERORGPATH + self.domain.orderer.name + "/"
        Paths.ORDDOMAINMSPPATH = Paths.ORDDOMAINPATH + "msp/"
        Paths.ORDDOMAINMSPCAPATH = Paths.ORDDOMAINMSPPATH + "tlscacerts/"
        Paths.ORDDOMAINTLSPATH = Paths.ORDDOMAINPATH + "tls/"

        # Peer Organizations Paths
        Paths.PEERORGPATH = Paths.DOMAINPATH + "peerOrganizations/"

        # Chaincode Crypto Path (under review)
        Paths.CCCRYPTOPATH = Paths.DOMAINPATH + "chaincodecrypto/"
        Paths.CCCRYPTOTLSPATH = Paths.CCCRYPTOPATH + "tls/"
        Paths.CCCRYPTOTLSCAPATH = Paths.CCCRYPTOTLSPATH + "tlscacerts/"

        # Channel Artifacts Path
        Paths.CHANNELARTIFACTSPATH = Paths.DOMAINPATH + "channelartifacts/"

        # Compose Files Path
        Paths.COMPOSEPATH = Paths.DOMAINPATH + "compose/"

        # Firefly Git Path
        Paths.FIREFLYPATH = Paths.DOMAINPATH + "firefly/"

        # Config Path and Files
        Paths.CONFIGPATH = Paths.APPPATH + "config/"
        Paths.CONFIGPEER = Paths.CONFIGPATH + "core.yaml"
        Paths.CONFIGTX = Paths.CONFIGPATH + "configtx.yaml"
        Paths.CONFIGORDERER = Paths.CONFIGPATH + "orderer.yaml"

    def build_folders(self):
        console.print("[bold white]# Preparing folders[/]")

        os.system("rm -fR " + Paths.FABRICCAPATH)
        os.system("rm -fR " + Paths.PEERORGPATH)
        os.system("rm -fR " + Paths.ORDERERORGPATH)
        os.system("rm -fR " + Paths.CCCRYPTOPATH)
        os.system("rm -fR " + Paths.CHANNELARTIFACTSPATH)

        pathcompose = Path(Paths.COMPOSEPATH)
        pathcompose.mkdir(parents=True, exist_ok=True)

        pathfirefly = Path(Paths.FIREFLYPATH)
        pathfirefly.mkdir(parents=True, exist_ok=True)

        pathfabricca = Path(Paths.CADOMAINPATH)
        pathfabricca.mkdir(parents=True, exist_ok=True)

        pathorderer = Path(Paths.ORDDOMAINPATH)
        pathorderer.mkdir(parents=True, exist_ok=True)

        pathchaincode = Path(Paths.CCCRYPTOPATH)
        pathchaincode.mkdir(parents=True, exist_ok=True)

        for org in self.domain.organizations:
            self.build_folders_org(org)

    def build_folders_org(self, org: Organization):
        pathfabriccaorg = Path(Paths.FABRICCAPATH + org.ca.name)
        pathfabriccaorg.mkdir(parents=True, exist_ok=True)

        pathorgs = Path(Paths.PEERORGPATH + org.name)
        pathorgs.mkdir(parents=True, exist_ok=True)

        for peer in org.peers:
            self.build_folder_peer(org, peer)

    def build_folder_peer(self, org: Organization, peer: Peer):
        Paths.PEERCFGPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/peercfg/"
        pathpeers = Path(Paths.PEERCFGPATH)
        pathpeers.mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Paths.CONFIGPEER,
            Paths.PEERCFGPATH + "core.yaml",
        )

    def set_org_paths(self, org: Organization):
        Paths.ORGPATH = Paths.PEERORGPATH + org.name + "/"
        Paths.CAORGNAME = org.ca.name + "." + self.domain.name
        Paths.CAORGPATH = Paths.FABRICCAPATH + org.ca.name + "/"
        Paths.TLSCERTORGFILE = Paths.CAORGPATH + "tls-cert.pem"
        Paths.CACERTORGFILE = Paths.CAORGPATH + "ca-cert.pem"
        Paths.ORGMSPPATH = Paths.ORGPATH + "msp/"
        Paths.ORGNAME = org.name + "." + self.domain.name

        Paths.ORGUSERMSPPATH = Paths.ORGPATH + "users/User1@" + Paths.ORGNAME + "/msp/"
        userpath = Path(Paths.ORGUSERMSPPATH)
        userpath.mkdir(parents=True, exist_ok=True)

        Paths.ORGADMINMSPPATH = Paths.ORGPATH + "users/Admin@" + Paths.ORGNAME + "/msp/"
        adminpath = Path(Paths.ORGADMINMSPPATH)
        adminpath.mkdir(parents=True, exist_ok=True)

    def set_peer_paths(self, org: Organization, peer: Peer):
        Paths.PEERPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/"
        Paths.PEERNAME = peer.name + "." + self.domain.name
        Paths.PEERMSPPATH = Paths.PEERPATH + "msp/"
        Paths.PEERTLSPATH = Paths.PEERPATH + "tls/"
        Paths.PEERTLSCAPATH = Paths.PEERTLSPATH + "tlscacerts/"
