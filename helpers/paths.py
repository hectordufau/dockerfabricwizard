import os
import shutil
from pathlib import Path

from rich.console import Console

from models.chaincode import Chaincode
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
    CHAINCODEPATH = str()
    CHAINCODEBUILDPATH = str()
    CHAINCODESRC = str()
    CHAINCODEPKG = str()
    PEERSERVERCRT = str()
    PEERSERVERKEY = str()
    PEERCAROOT = str()
    ORDERERORGADMINCERTPATH = str()
    ORDERERORGTLSCAMSPPATH = str()
    ORGTLSPATH = str()
    ORGTLSTLSCAPATH = str()
    ORGSIGNCERTPATH = str()
    ORDERERORGCAMSPPATH = str()
    CLIHOSTNAME = str()

    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

        # Application Path
        # ${PWD}
        Paths.APPPATH = str(Path().absolute()) + "/"

        # Domain Path
        # ${PWD}/domains/[DOMAIN]/
        Paths.DOMAINPATH = Paths.APPPATH + "domains/" + self.domain.name + "/"
        # ${PWD}/domains/[DOMAIN]/config/
        Paths.DOMAINCONFIGPATH = Paths.DOMAINPATH + "config/"
        # ${PWD}/domains/[DOMAIN]/config/configtx.yaml
        Paths.DOMAINCONFIGTXFILE = Paths.DOMAINCONFIGPATH + "configtx.yaml"
        # ${PWD}/domains/[DOMAIN]/config/configtx.json
        Paths.DOMAINCONFIGTXJSONFILE = Paths.DOMAINCONFIGPATH + "configtx.json"
        # ${PWD}/domains/[DOMAIN]/config/build/
        Paths.DOMAINCONFIGBUILDPATH = Paths.DOMAINCONFIGPATH + "build/"

        # Fabric CAs Paths
        # ${PWD}/domains/[DOMAIN]/fabricca/
        Paths.FABRICCAPATH = Paths.DOMAINPATH + "fabricca/"
        ## Fabric CA Domain
        # ca.[DOMAIN]
        Paths.CADOMAINNAME = self.domain.ca.name + "." + self.domain.name
        # ${PWD}/domains/[DOMAIN]/fabricca/ca/
        Paths.CADOMAINPATH = Paths.FABRICCAPATH + self.domain.ca.name + "/"
        # ${PWD}/domains/[DOMAIN]/fabricca/ca/crypto/
        Paths.CADOMAINCRYPTOPATH = Paths.CADOMAINPATH + "crypto/"

        # Fabric CA Client Domain Admin
        # ${PWD}/domains/[DOMAIN]/fabricca/ca/admin/
        Paths.CACLIENTDOMAINPATH = Paths.CADOMAINPATH + "admin/"
        # ${PWD}/domains/[DOMAIN]/fabricca/ca/admin/msp/
        Paths.CACLIENTDOMAINMSPPATH = Paths.CACLIENTDOMAINPATH + "msp/"

        ## Fabric CA Domain Cert Files
        # ${PWD}/domains/[DOMAIN]/fabricca/ca/crypto/ca-cert.pem
        Paths.CACERTDOMAINFILE = Paths.CADOMAINCRYPTOPATH + "ca-cert.pem"
        # ${PWD}/domains/[DOMAIN]/fabricca/ca/crypto/tls-cert.pem
        Paths.TLSCERTDOMAINFILE = Paths.CADOMAINCRYPTOPATH + "tls-cert.pem"

        ## Fabric CA Orderer
        # ca.orderer.[DOMAIN]
        Paths.CAORDERERNAME = self.domain.caorderer.name + "." + self.domain.name
        # ${PWD}/domains/[DOMAIN]/fabricca/ca.orderer/
        Paths.CAORDERERPATH = Paths.FABRICCAPATH + self.domain.caorderer.name + "/"
        # ${PWD}/domains/[DOMAIN]/fabricca/ca.orderer/crypto/
        Paths.CAORDERERCRYPTOPATH = Paths.CAORDERERPATH + "crypto/"
        # ${PWD}/domains/[DOMAIN]/fabricca/ca.orderer/admin/
        Paths.CAORDERERCACLIENTPATH = Paths.CAORDERERPATH + "admin/"
        # ${PWD}/domains/[DOMAIN]/fabricca/ca.orderer/admin/msp/
        Paths.CAORDERERCACLIENTMSPPATH = Paths.CAORDERERCACLIENTPATH + "msp/"
        ## Fabric CA Domain Cert Files
        # ${PWD}/domains/[DOMAIN]/fabricca/ca.orderer/crypto/ca-cert.pem
        Paths.CACERTORDERERFILE = Paths.CAORDERERCRYPTOPATH + "ca-cert.pem"
        # ${PWD}/domains/[DOMAIN]/fabricca/ca.orderer/crypto/tls-cert.pem
        Paths.TLSCERTORDERERFILE = Paths.CAORDERERCRYPTOPATH + "tls-cert.pem"

        # Orderer Organization Paths
        # orderer.[DOMAIN]
        Paths.ORDERERNAME = self.domain.orderer.name + "." + self.domain.name
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/
        Paths.ORDERERORGPATH = Paths.DOMAINPATH + "ordererOrganizations/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/
        Paths.ORDERERORGADMINPATH = Paths.ORDERERORGPATH + "admin/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/msp/
        Paths.ORDERERORGMSPPATH = Paths.ORDERERORGADMINPATH + "msp/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/msp/cacerts/
        Paths.ORDERERORGCAMSPPATH = Paths.ORDERERORGMSPPATH + "cacerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/msp/tlscacerts/
        Paths.ORDERERORGTLSCAMSPPATH = Paths.ORDERERORGMSPPATH + "tlscacerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/msp/admincerts/
        Paths.ORDERERORGADMINCERTPATH = Paths.ORDERERORGMSPPATH + "admincerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/msp/signcerts/
        Paths.ORDERERORGSIGNCERTPATH = Paths.ORDERERORGMSPPATH + "signcerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/tls/
        Paths.ORDERERORGTLSPATH = Paths.ORDERERORGADMINPATH + "tls/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/admin/tls/tlscacerts/
        Paths.ORDERERORGTLSCAPATH = Paths.ORDERERORGTLSPATH + "tlscacerts/"

        ## Orderer Domain Paths
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/
        Paths.ORDDOMAINPATH = Paths.ORDERERORGPATH + self.domain.orderer.name + "/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/msp/
        Paths.ORDDOMAINMSPPATH = Paths.ORDDOMAINPATH + "msp/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/msp/admincerts/
        Paths.ORDDOMAINADMINCERTPATH = Paths.ORDDOMAINMSPPATH + "admincerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/msp/tlscacerts/
        Paths.ORDTLSCAMSPPATH = Paths.ORDDOMAINMSPPATH + "tlscacerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/msp/cacerts/
        Paths.ORDDOMAINCACERTPATH = Paths.ORDDOMAINMSPPATH + "cacerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/msp/signcerts/
        Paths.ORDSIGNCERTMSPPATH = Paths.ORDDOMAINMSPPATH + "signcerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/msp/keystore/
        Paths.ORDKEYSTOREMSPPATH = Paths.ORDDOMAINMSPPATH + "keystore/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/tls/
        Paths.ORDDOMAINTLSPATH = Paths.ORDDOMAINPATH + "tls/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/tls/tlscacerts/
        Paths.ORDTLSCAPATH = Paths.ORDDOMAINTLSPATH + "tlscacerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/tls/signcerts/
        Paths.ORDSIGNCERTPATH = Paths.ORDDOMAINTLSPATH + "signcerts/"
        # ${PWD}/domains/[DOMAIN]/ordererOrganizations/orderer/tls/keystore/
        Paths.ORDKEYSTOREPATH = Paths.ORDDOMAINTLSPATH + "keystore/"

        # Peer Organizations Paths
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/
        Paths.PEERORGPATH = Paths.DOMAINPATH + "peerOrganizations/"

        # Chaincode Crypto Path (under review)
        # ${PWD}/domains/[DOMAIN]/chaincodecrypto/
        Paths.CCCRYPTOPATH = Paths.DOMAINPATH + "chaincodecrypto/"
        # ${PWD}/domains/[DOMAIN]/chaincodecrypto/tls/
        Paths.CCCRYPTOTLSPATH = Paths.CCCRYPTOPATH + "tls/"
        # ${PWD}/domains/[DOMAIN]/chaincodecrypto/tls/tlscacerts/
        Paths.CCCRYPTOTLSCAPATH = Paths.CCCRYPTOTLSPATH + "tlscacerts/"

        # Channel Artifacts Path
        # ${PWD}/domains/[DOMAIN]/channelartifacts/
        Paths.CHANNELARTIFACTSPATH = Paths.DOMAINPATH + "channelartifacts/"
        # ${PWD}/domains/[DOMAIN]/channelartifacts/[NETWORK].block
        Paths.BLOCKFILE = (
            Paths.CHANNELARTIFACTSPATH + self.domain.networkname + ".block"
        )

        # Compose Files Path
        # ${PWD}/domains/[DOMAIN]/compose/
        Paths.COMPOSEPATH = Paths.DOMAINPATH + "compose/"

        # Firefly Git Path
        # ${PWD}/domains/[DOMAIN]/firefly/
        Paths.FIREFLYPATH = Paths.DOMAINPATH + "firefly/"

        # Config Path and Files
        # ${PWD}/config/
        Paths.CONFIGPATH = Paths.APPPATH + "config/"
        # ${PWD}/config/core.yaml
        Paths.CONFIGPEER = Paths.CONFIGPATH + "core.yaml"
        # ${PWD}/config/configtx.yaml
        Paths.CONFIGTX = Paths.CONFIGPATH + "configtx.yaml"
        # ${PWD}/config/orderer.yaml
        Paths.CONFIGORDERER = Paths.CONFIGPATH + "orderer.yaml"

        # CLI
        Paths.CLIHOSTNAME = "cli." + self.domain.name
        Paths.CLIEXTPATH = (
            "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/"
        )
        Paths.CLIPATH = "/etc/hyperledger/organizations/"
        # /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/config/build/
        Paths.EXTCONFIGTX = Paths.CLIEXTPATH + "config/build/"
        # /etc/hyperledger/organizations/channelartifacts/
        Paths.CLIBLOCKPATH = Paths.CLIPATH + "channelartifacts/"
        # Paths.CLIROOTCA = "ordererOrganizations/orderer/tls/ca-root.crt"
        Paths.CLIROOTCA = "ordererOrganizations/orderer/tls/tlscacerts/tls-cert.pem"
        # Paths.CLISERVERCRT = "ordererOrganizations/orderer/tls/server.crt"
        Paths.CLISERVERCRT = "ordererOrganizations/orderer/tls/signcerts/cert.crt"
        # Paths.CLISERVERKEY = "ordererOrganizations/orderer/tls/server.key"
        Paths.CLISERVERKEY = "ordererOrganizations/orderer/tls/keystore/key.pem"

        # CHAINCODE
        # ${PWD}/chaincodes/
        Paths.CHAINCODEPATH = Paths.APPPATH + "chaincodes/"
        # ${PWD}/chaincodes/build/
        Paths.CHAINCODEBUILDPATH = Paths.CHAINCODEPATH + "build/"
        # ${PWD}/chaincodes/build/src/
        Paths.CHAINCODESRC = Paths.CHAINCODEBUILDPATH + "src/"
        # ${PWD}/chaincodes/build/pkg/
        Paths.CHAINCODEPKG = Paths.CHAINCODEBUILDPATH + "pkg/"

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

        pathordererorg = Path(Paths.ORDERERORGADMINCERTPATH)
        pathordererorg.mkdir(parents=True, exist_ok=True)

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

        ordorgtlscapath = Path(Paths.ORDERERORGTLSCAMSPPATH)
        ordorgtlscapath.mkdir(parents=True, exist_ok=True)

        for org in self.domain.organizations:
            self.build_folders_org(org)

    def build_folders_org(self, org: Organization):
        """_summary_"""
        self.set_org_paths(org)

        pathfabriccaorg = Path(Paths.FABRICCAPATH + org.ca.name)
        pathfabriccaorg.mkdir(parents=True, exist_ok=True)

        pathorgs = Path(Paths.PEERORGPATH + org.name)
        pathorgs.mkdir(parents=True, exist_ok=True)

        adminpath = Path(Paths.ORGADMINCERTPATH)
        adminpath.mkdir(parents=True, exist_ok=True)

        caorgclient = Path(Paths.CAORGCACLIENTMSPPATH)
        caorgclient.mkdir(parents=True, exist_ok=True)

        for peer in org.peers:
            self.build_folder_peer(org, peer)

    def build_folder_peer(self, org: Organization, peer: Peer):
        """_summary_"""
        self.set_peer_paths(org, peer)

        Paths.PEERCFGPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/peercfg/"
        pathpeers = Path(Paths.PEERCFGPATH)
        pathpeers.mkdir(parents=True, exist_ok=True)

        adminpath = Path(Paths.PEERADMINCERTPATH)
        adminpath.mkdir(parents=True, exist_ok=True)

        msptlscacerts = Path(Paths.PEERTLSCAMSPPATH)
        msptlscacerts.mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Paths.CONFIGPEER,
            Paths.PEERCFGPATH + "core.yaml",
        )

    def set_org_paths(self, org: Organization):
        """_summary_"""

        # ca.[ORG].[DOMAIN]
        Paths.CAORGNAME = org.ca.name + "." + self.domain.name
        # [ORG].[DOMAIN]
        Paths.ORGNAME = org.name + "." + self.domain.name

        # ${PWD}/domains/[DOMAIN]/fabricca/[ORG]/
        Paths.CAORGPATH = Paths.FABRICCAPATH + org.ca.name + "/"
        # ${PWD}/domains/[DOMAIN]/fabricca/[ORG]/crypto/
        Paths.CAORGCRYPTOPATH = Paths.CAORGPATH + "crypto/"
        # ${PWD}/domains/[DOMAIN]/fabricca/[ORG]/admin/
        Paths.CAORGCACLIENTPATH = Paths.CAORGPATH + "admin/"
        # ${PWD}/domains/[DOMAIN]/fabricca/[ORG]/admin/msp/
        Paths.CAORGCACLIENTMSPPATH = Paths.CAORGCACLIENTPATH + "msp/"
        # ${PWD}/domains/[DOMAIN]/fabricca/[ORG]/crypto/tls-cert.pem
        Paths.TLSCERTORGFILE = Paths.CAORGCRYPTOPATH + "tls-cert.pem"
        # ${PWD}/domains/[DOMAIN]/fabricca/[ORG]/crypto/ca-cert.pem
        Paths.CACERTORGFILE = Paths.CAORGCRYPTOPATH + "ca-cert.pem"

        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/
        Paths.ORGPATH = Paths.PEERORGPATH + org.name + "/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/crypto/
        Paths.ORGCRYPTOPATH = Paths.ORGPATH + "crypto/"

        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/admin/
        Paths.ORGCACLIENTPATH = Paths.ORGPATH + "admin/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/admin/msp/
        Paths.ORGMSPPATH = Paths.ORGCACLIENTPATH + "msp/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/admin/msp/admincerts/
        Paths.ORGADMINCERTPATH = Paths.ORGMSPPATH + "admincerts/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/admin/msp/signcerts/
        Paths.ORGSIGNCERTPATH = Paths.ORGMSPPATH + "signcerts/"

        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/admin/tls/
        Paths.ORGTLSPATH = Paths.ORGCACLIENTPATH + "tls/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/admin/tls/tlscacerts/
        Paths.ORGTLSTLSCAPATH = Paths.ORGTLSPATH + "tlscacerts/"

    def set_peer_paths(self, org: Organization, peer: Peer):
        """_summary_"""

        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/
        Paths.PEERPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/"
        # [PEER].[DOMAIN]
        Paths.PEERNAME = peer.name + "." + self.domain.name
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/peercfg/
        Paths.PEERCFGPATH = Paths.PEERORGPATH + org.name + "/" + peer.name + "/peercfg/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/msp/
        Paths.PEERMSPPATH = Paths.PEERPATH + "msp/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/msp/tlscacerts/
        Paths.PEERTLSCAMSPPATH = Paths.PEERMSPPATH + "tlscacerts/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/msp/cacerts/
        Paths.PEERCACERTPATH = Paths.PEERMSPPATH + "cacerts/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/msp/admincerts/
        Paths.PEERADMINCERTPATH = Paths.PEERMSPPATH + "admincerts/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/tls/
        Paths.PEERTLSPATH = Paths.PEERPATH + "tls/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/tls/tlscacerts/
        Paths.PEERTLSCAPATH = Paths.PEERTLSPATH + "tlscacerts/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/tls/signcerts/
        Paths.PEERSIGNCERTPATH = Paths.PEERTLSPATH + "signcerts/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/tls/keystore/
        Paths.PEERKEYSTOREPATH = Paths.PEERTLSPATH + "keystore/"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/tls/server.crt
        # Paths.PEERSERVERCRT = Paths.PEERTLSPATH + "server.crt"
        Paths.PEERSERVERCRT = Paths.PEERSIGNCERTPATH + "cert.crt"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/tls/server.key
        # Paths.PEERSERVERKEY = Paths.PEERTLSPATH + "server.key"
        Paths.PEERSERVERKEY = Paths.PEERKEYSTOREPATH + "key.pem"
        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/tls/ca-root.crt
        # Paths.PEERCAROOT = Paths.PEERTLSPATH + "ca-root.crt"
        Paths.PEERCAROOT = Paths.PEERTLSCAPATH + "tls-cert.pem"

    def set_chaincode_paths(self, org: Organization, peer: Peer, chaincode: Chaincode):
        """_summary_"""

        # ${PWD}/domains/[DOMAIN]/peerOrganizations/[ORG]/[PEER]/[CHAINCODE]
        Paths.CCPATH = (
            Paths.PEERORGPATH + org.name + "/" + peer.name + "/" + chaincode.name
        )
        # [PEER].[CHAINCODE].ccaas.[DOMAIN]
        Paths.CCNAME = (
            peer.name.replace(".", "")
            + "."
            + chaincode.name
            + ".ccaas."
            + self.domain.name
        )
        
        Paths.CCSMALLNAME = (
            peer.name.replace(".", "")
            + "."
            + chaincode.name
            + ".ccaas"
        )
        
        # [CHAINCODE]_ccaas_image:latest
        Paths.CCIMAGE = chaincode.name + "_ccaas_image:latest"
        
        
