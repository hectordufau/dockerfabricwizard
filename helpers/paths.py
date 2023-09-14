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
    DOMAINCONFIGPATH = str()
    DOMAINCONFIGTXFILE = str()
    DOMAINCONFIGTXJSONFILE = str()
    DOMAINCONFIGBUILDPATH = str()
    FABRICCAPATH = str()
    CADOMAINNAME = str()
    CADOMAINPATH = str()
    CADOMAINCRYPTOPATH = str()
    CACLIENTDOMAINPATH = str()
    CACLIENTDOMAINMSPPATH = str()
    CACERTDOMAINFILE = str()
    TLSCERTDOMAINFILE = str()
    CAORDERERNAME = str()
    CAORDERERPATH = str()
    CAORDERERCRYPTOPATH = str()
    CAORDERERCACLIENTPATH = str()
    CAORDERERCACLIENTMSPPATH = str()
    CACERTORDERERFILE = str()
    TLSCERTORDERERFILE = str()
    ORDERERNAME = str()
    ORDERERORGPATH = str()
    ORDERERORGADMINPATH = str()
    ORDERERORGMSPPATH = str()
    ORDERERORGSIGNCERTPATH = str()
    ORDDOMAINPATH = str()
    ORDDOMAINMSPPATH = str()
    ORDTLSCAMSPPATH = str()
    ORDDOMAINCACERTPATH = str()
    ORDSIGNCERTMSPPATH = str()
    ORDKEYSTOREMSPPATH = str()
    ORDDOMAINTLSPATH = str()
    ORDDOMAINADMINCERTPATH = str()
    ORDTLSCAPATH = str()
    ORDSIGNCERTPATH = str()
    ORDKEYSTOREPATH = str()
    PEERORGPATH = str()
    CCCRYPTOPATH = str()
    CCCRYPTOTLSPATH = str()
    CCCRYPTOTLSCAPATH = str()
    CHANNELARTIFACTSPATH = str()
    BLOCKFILE = str()
    COMPOSEPATH = str()
    FIREFLYPATH = str()
    CONFIGPATH = str()
    CONFIGPEER = str()
    CONFIGTX = str()
    CONFIGORDERER = str()
    CLIEXTPATH = str()
    CLIPATH = str()
    EXTCONFIGTX = str()
    CLIBLOCKPATH = str()
    CLIROOTCA = str()
    CLISERVERCRT = str()
    CLISERVERKEY = str()
    PEERCFGPATH = str()
    ORGPATH = str()
    ORGCRYPTOPATH = str()
    ORGCACLIENTPATH = str()
    ORGMSPPATH = str()
    CAORGNAME = str()
    CAORGPATH = str()
    CAORGCRYPTOPATH = str()
    CAORGCACLIENTPATH = str()
    CAORGCACLIENTMSPPATH = str()
    TLSCERTORGFILE = str()
    CACERTORGFILE = str()
    ORGNAME = str()
    ORGUSERSPATH = str()
    ORGMSPUSERSPATH = str()
    ORGADMINCERTPATH = str()
    PEERPATH = str()
    PEERNAME = str()
    PEERMSPPATH = str()
    PEERTLSCAMSPPATH = str()
    PEERTLSPATH = str()
    PEERCACERTPATH = str()
    PEERTLSCAPATH = str()
    PEERSIGNCERTPATH = str()
    PEERKEYSTOREPATH = str()
    PEERADMINCERTPATH = str()

    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain
        # Application Path
        Paths.APPPATH = str(Path().absolute()) + "/"

        # Domain Path
        Paths.DOMAINPATH = Paths.APPPATH + "domains/" + self.domain.name + "/"
        Paths.DOMAINCONFIGPATH = Paths.DOMAINPATH + "config/"
        Paths.DOMAINCONFIGTXFILE = Paths.DOMAINCONFIGPATH + "configtx.yaml"
        Paths.DOMAINCONFIGTXJSONFILE = Paths.DOMAINCONFIGPATH + "configtx.json"
        Paths.DOMAINCONFIGBUILDPATH = Paths.DOMAINCONFIGPATH + "build/"

        # Fabric CAs Paths
        Paths.FABRICCAPATH = Paths.DOMAINPATH + "fabricca/"
        ## Fabric CA Domain
        Paths.CADOMAINNAME = self.domain.ca.name + "." + self.domain.name
        Paths.CADOMAINPATH = Paths.FABRICCAPATH + self.domain.ca.name + "/"
        Paths.CADOMAINCRYPTOPATH = Paths.CADOMAINPATH + "crypto/"
        # Fabric CA Client Domain Admin
        Paths.CACLIENTDOMAINPATH = Paths.CADOMAINPATH + "admin/"
        Paths.CACLIENTDOMAINMSPPATH = Paths.CACLIENTDOMAINPATH + "msp/"
        ## Fabric CA Domain Cert Files
        Paths.CACERTDOMAINFILE = Paths.CADOMAINCRYPTOPATH + "ca-cert.pem"
        Paths.TLSCERTDOMAINFILE = Paths.CADOMAINCRYPTOPATH + "tls-cert.pem"

        ## Fabric CA Orderer
        Paths.CAORDERERNAME = self.domain.caorderer.name + "." + self.domain.name
        Paths.CAORDERERPATH = Paths.FABRICCAPATH + self.domain.caorderer.name + "/"
        Paths.CAORDERERCRYPTOPATH = Paths.CAORDERERPATH + "crypto/"
        Paths.CAORDERERCACLIENTPATH = Paths.CAORDERERPATH + "admin/"
        Paths.CAORDERERCACLIENTMSPPATH = Paths.CAORDERERCACLIENTPATH + "msp/"
        ## Fabric CA Domain Cert Files
        Paths.CACERTORDERERFILE = Paths.CAORDERERCRYPTOPATH + "ca-cert.pem"
        Paths.TLSCERTORDERERFILE = Paths.CAORDERERCRYPTOPATH + "tls-cert.pem"

        # Orderer Organization Paths
        Paths.ORDERERNAME = self.domain.orderer.name + "." + self.domain.name
        Paths.ORDERERORGPATH = Paths.DOMAINPATH + "ordererOrganizations/"
        Paths.ORDERERORGADMINPATH = Paths.ORDERERORGPATH + "admin/"
        Paths.ORDERERORGMSPPATH = Paths.ORDERERORGADMINPATH + "msp/"
        Paths.ORDERERORGSIGNCERTPATH = Paths.ORDERERORGMSPPATH + "signcerts/"

        ## Orderer Domain Paths
        Paths.ORDDOMAINPATH = Paths.ORDERERORGPATH + self.domain.orderer.name + "/"
        Paths.ORDDOMAINMSPPATH = Paths.ORDDOMAINPATH + "msp/"
        Paths.ORDTLSCAMSPPATH = Paths.ORDDOMAINMSPPATH + "tlscacerts/"
        Paths.ORDDOMAINCACERTPATH = Paths.ORDDOMAINMSPPATH + "cacerts/"
        Paths.ORDSIGNCERTMSPPATH = Paths.ORDDOMAINMSPPATH + "signcerts/"
        Paths.ORDKEYSTOREMSPPATH = Paths.ORDDOMAINMSPPATH + "keystore/"

        Paths.ORDDOMAINTLSPATH = Paths.ORDDOMAINPATH + "tls/"
        Paths.ORDDOMAINADMINCERTPATH = Paths.ORDDOMAINMSPPATH + "admincerts/"
        Paths.ORDTLSCAPATH = Paths.ORDDOMAINTLSPATH + "tlscacerts/"
        Paths.ORDSIGNCERTPATH = Paths.ORDDOMAINTLSPATH + "signcerts/"
        Paths.ORDKEYSTOREPATH = Paths.ORDDOMAINTLSPATH + "keystore/"

        adminpath = Path(Paths.PEERADMINCERTPATH)
        adminpath.mkdir(parents=True, exist_ok=True)

        # Peer Organizations Paths
        Paths.PEERORGPATH = Paths.DOMAINPATH + "peerOrganizations/"

        # Chaincode Crypto Path (under review)
        Paths.CCCRYPTOPATH = Paths.DOMAINPATH + "chaincodecrypto/"
        Paths.CCCRYPTOTLSPATH = Paths.CCCRYPTOPATH + "tls/"
        Paths.CCCRYPTOTLSCAPATH = Paths.CCCRYPTOTLSPATH + "tlscacerts/"

        # Channel Artifacts Path
        Paths.CHANNELARTIFACTSPATH = Paths.DOMAINPATH + "channelartifacts/"
        Paths.BLOCKFILE = (
            Paths.CHANNELARTIFACTSPATH + self.domain.networkname + ".block"
        )

        # Compose Files Path
        Paths.COMPOSEPATH = Paths.DOMAINPATH + "compose/"

        # Firefly Git Path
        Paths.FIREFLYPATH = Paths.DOMAINPATH + "firefly/"

        # Config Path and Files
        Paths.CONFIGPATH = Paths.APPPATH + "config/"
        Paths.CONFIGPEER = Paths.CONFIGPATH + "core.yaml"
        Paths.CONFIGTX = Paths.CONFIGPATH + "configtx.yaml"
        Paths.CONFIGORDERER = Paths.CONFIGPATH + "orderer.yaml"

        # CLI
        Paths.CLIEXTPATH = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/"
        )
        Paths.CLIPATH = "/etc/hyperledger/organizations/"
        Paths.EXTCONFIGTX = Paths.CLIEXTPATH + "config/build/"
        Paths.CLIBLOCKPATH = Paths.CLIPATH + "channelartifacts/"
        Paths.CLIROOTCA = "ordererOrganizations/orderer/tls/ca-root.crt"
        Paths.CLISERVERCRT = "ordererOrganizations/orderer/tls/server.crt"
        Paths.CLISERVERKEY = "ordererOrganizations/orderer/tls/server.key"

    def build_folders(self):
        """_summary_"""
        console.print("[bold white]# Preparing folders[/]")

        os.system("rm -fR " + Paths.FABRICCAPATH)
        os.system("rm -fR " + Paths.PEERORGPATH)
        os.system("rm -fR " + Paths.ORDERERORGPATH)
        os.system("rm -fR " + Paths.CCCRYPTOPATH)
        os.system("rm -fR " + Paths.CHANNELARTIFACTSPATH)
        os.system("rm -fR " + Paths.CACLIENTDOMAINPATH)

        pathcompose = Path(Paths.COMPOSEPATH)
        pathcompose.mkdir(parents=True, exist_ok=True)

        pathfirefly = Path(Paths.FIREFLYPATH)
        pathfirefly.mkdir(parents=True, exist_ok=True)

        pathfabricca = Path(Paths.CADOMAINPATH)
        pathfabricca.mkdir(parents=True, exist_ok=True)

        pathfabriccaord = Path(Paths.CAORDERERPATH)
        pathfabriccaord.mkdir(parents=True, exist_ok=True)

        pathfabriccaclient = Path(Paths.CACLIENTDOMAINPATH)
        pathfabriccaclient.mkdir(parents=True, exist_ok=True)

        pathorderer = Path(Paths.ORDDOMAINADMINCERTPATH)
        pathorderer.mkdir(parents=True, exist_ok=True)

        pathchaincode = Path(Paths.CCCRYPTOPATH)
        pathchaincode.mkdir(parents=True, exist_ok=True)

        msptlscacerts = Path(Paths.ORDTLSCAMSPPATH)
        msptlscacerts.mkdir(parents=True, exist_ok=True)

        caclientdomain = Path(Paths.CACLIENTDOMAINMSPPATH)
        caclientdomain.mkdir(parents=True, exist_ok=True)

        caclientorderer = Path(Paths.CAORDERERCACLIENTMSPPATH)
        caclientorderer.mkdir(parents=True, exist_ok=True)

        configdomain = Path(Paths.DOMAINCONFIGPATH)
        configdomain.mkdir(parents=True, exist_ok=True)

        configbdomain = Path(Paths.DOMAINCONFIGBUILDPATH)
        configbdomain.mkdir(parents=True, exist_ok=True)

        channelartifacts = Path(Paths.CHANNELARTIFACTSPATH)
        channelartifacts.mkdir(parents=True, exist_ok=True)

        for org in self.domain.organizations:
            self.build_folders_org(org)

    def build_folders_org(self, org: Organization):
        """_summary_"""
        pathfabriccaorg = Path(Paths.FABRICCAPATH + org.ca.name)
        pathfabriccaorg.mkdir(parents=True, exist_ok=True)

        pathorgs = Path(Paths.PEERORGPATH + org.name)
        pathorgs.mkdir(parents=True, exist_ok=True)

        for peer in org.peers:
            self.build_folder_peer(org, peer)

    def build_folder_peer(self, org: Organization, peer: Peer):
        """_summary_"""
        Paths.PEERCFGPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/peercfg/"
        pathpeers = Path(Paths.PEERCFGPATH)
        pathpeers.mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Paths.CONFIGPEER,
            Paths.PEERCFGPATH + "core.yaml",
        )

    def set_org_paths(self, org: Organization):
        """_summary_"""
        Paths.ORGPATH = Paths.PEERORGPATH + org.name + "/"
        Paths.ORGCRYPTOPATH = Paths.ORGPATH + "crypto/"
        Paths.ORGCACLIENTPATH = Paths.ORGPATH + "admin/"
        Paths.ORGMSPPATH = Paths.ORGCACLIENTPATH + "msp/"

        Paths.CAORGNAME = org.ca.name + "." + self.domain.name
        Paths.CAORGPATH = Paths.FABRICCAPATH + org.ca.name + "/"
        Paths.CAORGCRYPTOPATH = Paths.CAORGPATH + "crypto/"
        Paths.CAORGCACLIENTPATH = Paths.CAORGPATH + "admin/"
        Paths.CAORGCACLIENTMSPPATH = Paths.CAORGCACLIENTPATH + "msp/"
        Paths.TLSCERTORGFILE = Paths.CAORGCRYPTOPATH + "tls-cert.pem"
        Paths.CACERTORGFILE = Paths.CAORGCRYPTOPATH + "ca-cert.pem"

        Paths.ORGNAME = org.name + "." + self.domain.name
        Paths.ORGUSERSPATH = Paths.ORGPATH + "users/"
        Paths.ORGMSPUSERSPATH = Paths.ORGMSPPATH + "users/"

        Paths.ORGADMINCERTPATH = Paths.ORGMSPPATH + "admincerts/"

        adminpath = Path(Paths.ORGADMINCERTPATH)
        adminpath.mkdir(parents=True, exist_ok=True)

        caorgclient = Path(Paths.CAORGCACLIENTMSPPATH)
        caorgclient.mkdir(parents=True, exist_ok=True)

    def set_peer_paths(self, org: Organization, peer: Peer):
        """_summary_"""
        Paths.PEERPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/"
        Paths.PEERNAME = peer.name + "." + self.domain.name
        Paths.PEERMSPPATH = Paths.PEERPATH + "msp/"
        Paths.PEERTLSCAMSPPATH = Paths.PEERMSPPATH + "tlscacerts/"
        Paths.PEERTLSPATH = Paths.PEERPATH + "tls/"
        Paths.PEERCACERTPATH = Paths.PEERMSPPATH + "cacerts/"
        Paths.PEERTLSCAPATH = Paths.PEERTLSPATH + "tlscacerts/"
        Paths.PEERSIGNCERTPATH = Paths.PEERTLSPATH + "signcerts/"
        Paths.PEERKEYSTOREPATH = Paths.PEERTLSPATH + "keystore/"
        Paths.PEERADMINCERTPATH = Paths.PEERMSPPATH + "admincerts/"
        Paths.PEERCFGPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/peercfg/"

        adminpath = Path(Paths.PEERADMINCERTPATH)
        adminpath.mkdir(parents=True, exist_ok=True)

        msptlscacerts = Path(Paths.PEERTLSCAMSPPATH)
        msptlscacerts.mkdir(parents=True, exist_ok=True)
