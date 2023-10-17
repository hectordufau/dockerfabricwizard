import os

from helpers.paths import Paths
from models.chaincode import Chaincode
from models.domain import Domain
from models.orderer import Orderer
from models.organization import Organization
from models.peer import Peer


class Commands:
    def __init__(self) -> None:
        pass

    def enroll(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        command = (
            apppath
            + "bin/fabric-ca-client enroll "
            + "-u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            + " --csr.hosts localhost"
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def enroll_msp(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        os.environ["FABRIC_CA_CLIENT_MSPDIR"] = "msp"
        command = (
            apppath
            + "bin/fabric-ca-client enroll "
            + "-u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            + " --csr.hosts localhost"
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def enroll_tls(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        csrhosts: [],
        myhost: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        os.environ["FABRIC_CA_CLIENT_MSPDIR"] = "tls"
        command = (
            apppath
            + "bin/fabric-ca-client enroll "
            + "-u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            + " --enrollment.profile tls --csr.hosts "
            + ",".join(csrhosts)
            + " --myhost "
            + myhost
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def register_orderer(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        command = (
            apppath
            + "bin/fabric-ca-client register "
            + "-u https://localhost:"
            + str(port)
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type orderer "
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def register_orderer_admin(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        command = (
            apppath
            + "bin/fabric-ca-client register "
            + "-u https://localhost:"
            + str(port)
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type admin "
            + " --tls.certfiles "
            + certfile
            + ' --id.attrs "hf.Registrar.Roles=client,hf.Registrar.Attributes=*,hf.Revoker=true,hf.GenCRL=true,admin=true:ecert,abac.init=true:ecert"'
        )
        # print(command)
        os.system(command)

    def register_admin(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        # caname: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        command = (
            apppath
            + "bin/fabric-ca-client register "
            + "-u https://localhost:"
            + str(port)
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type admin "
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def register_peer(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        command = (
            apppath
            + "bin/fabric-ca-client register "
            + "-u https://localhost:"
            + str(port)
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type peer "
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def register_client(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        command = (
            apppath
            + "bin/fabric-ca-client register "
            + "-u https://localhost:"
            + str(port)
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type client "
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def register_user(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        command = (
            apppath
            + "bin/fabric-ca-client register "
            + "-u https://localhost:"
            + str(port)
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type user "
            + " --tls.certfiles "
            + certfile
        )
        # print(command)
        os.system(command)

    def configtxgen_config_path(
        self, apppath: str, configpath: str, block: str, channel: str
    ):
        command = (
            apppath
            + "bin/configtxgen -configPath "
            + configpath
            + " -profile SampleAppChannelEtcdRaft -outputBlock "
            + block
            + " -channelID "
            + channel
        )
        # print(command)
        os.system(command)

    def configtxgen_print_org(self, apppath: str, configtx: str, org: Organization):
        os.environ["FABRIC_CFG_PATH"] = configtx
        command = (
            apppath
            + "bin/configtxgen -printOrg "
            + org.name
            + "MSP > "
            + configtx
            + org.name
            + ".json"
        )
        # print(command)
        os.system(command)

    def osnadmin(
        self,
        apppath: str,
        configpath: str,
        block: str,
        channel: str,
        orderer: Orderer,
        caroot: str,
        tlscert: str,
        tlskey: str,
    ):
        os.environ["FABRIC_CFG_PATH"] = configpath
        os.environ["BLOCKFILE"] = block

        command = (
            apppath
            + "bin/osnadmin channel join --channelID "
            + channel
            + " --config-block "
            + block
            + " -o localhost:"
            + str(orderer.adminlistenport)
            + " --ca-file '"
            + caroot
            + "' --client-cert '"
            + tlscert
            + "' --client-key '"
            + tlskey
            + "'"
        )
        # print(command)
        os.system(command)

    def peer_channel_join(
        self,
        org: Organization,
        peer: Peer,
        apppath: str,
        block: str,
        configpath: str,
        caroot: str,
        peermsp: str,
    ):
        os.environ["BLOCKFILE"] = block
        os.environ["FABRIC_CFG_PATH"] = configpath
        os.environ["CORE_PEER_TLS_ENABLED"] = "true"
        os.environ["CORE_PEER_LOCALMSPID"] = org.name + "MSP"
        os.environ["CORE_PEER_TLS_ROOTCERT_FILE"] = caroot
        os.environ["CORE_PEER_MSPCONFIGPATH"] = peermsp
        os.environ["CORE_PEER_ADDRESS"] = "localhost:" + str(peer.peerlistenport)

        command = apppath + "bin/peer channel join -b " + block
        # print(command)
        os.system(command)

    def peer_channel_signconfigtx(self, configtx: str, org: Organization):
        command = (
            "peer channel signconfigtx -f "
            + configtx
            + org.name
            + "_update_in_envelope.pb"
        )
        # print(command)
        os.system(command)

    def configtxlator_proto_decode(
        self, apppath: str, configpath: str, file: str, update: bool = None
    ):
        commontype = "common.ConfigUpdate " if update else "common.Block "
        command = (
            apppath
            + "bin/configtxlator proto_decode --input "
            + configpath
            + file
            + ".pb --type "
            + commontype
            + "--output "
            + configpath
            + file
            + ".json"
        )
        # print(command)
        os.system(command)

    def configtxlator_proto_encode(
        self, apppath: str, configpath: str, file: str, envelope: bool = None
    ):
        commontype = "common.Envelope" if envelope else "common.Config"
        command = (
            apppath
            + "bin/configtxlator proto_encode --input "
            + configpath
            + file
            + ".json --type "
            + commontype
            + " --output "
            + configpath
            + file
            + ".pb"
        )
        # print(command)
        os.system(command)

    def configtxlator_compute_update(self, apppath: str, channel: str, configpath: str):
        command = (
            apppath
            + "bin/configtxlator compute_update --channel_id "
            + channel
            + " --original "
            + configpath
            + "config.pb --updated "
            + configpath
            + "modified_config.pb --output "
            + configpath
            + "config_update.pb"
        )
        # print(command)
        os.system(command)

    def jq_export_config(self, configpath: str):
        command = (
            "jq .data.data[0].payload.data.config "
            + configpath
            + "config_block.json > "
            + configpath
            + "config.json"
        )
        # print(command)
        os.system(command)

    def jq_export_modified_config(self, org: Organization, configpath: str):
        command = (
            'jq -s \'.[0] * {"channel_group":{"groups":{"Application":{"groups": {"'
            + org.name
            + "MSP\":.[1]}}}}}' "
            + configpath
            + "config.json "
            + configpath
            + org.name
            + ".json > "
            + configpath
            + "modified_config.json"
        )
        # print(command)
        os.system(command)

    def echo_payload(
        self, channel: str, confupdtfile: str, configpath: str, org: Organization
    ):
        command = (
            'echo \'{"payload":{"header":{"channel_header":{"channel_id":"'
            + channel
            + '", "type":2}},"data":{"config_update":'
            + confupdtfile
            + "}}}' | jq . >"
            + configpath
            + org.name
            + "_update_in_envelope.json"
        )
        # print(command)
        os.system(command)

    def peer_lifecycle_chaincode_calculatepackageid(
        self, apppath: str, tarchaincode: str, buildpath: str
    ):
        command = (
            apppath
            + "bin/peer lifecycle chaincode calculatepackageid "
            + tarchaincode
            + " > "
            + buildpath
            + "PACKAGEID.txt"
        )
        # print(command)
        os.system(command)

    def peer_lifecycle_chaincode_install(self, apppath: str, chaincodepkg: str):
        command = apppath + "bin/peer lifecycle chaincode install " + chaincodepkg
        # print(command)
        os.system(command)

    def peer_lifecycle_chaincode_package(
        self, apppath: str, chaincodepkg: str, chaincode: Chaincode
    ):
        command = (
            apppath
            + "bin/peer lifecycle chaincode package "
            + chaincode.name
            + ".tar.gz"
            + " --path "
            + chaincodepkg
            + " --lang golang --label "
            + chaincode.name
            + "_"
            + str(chaincode.version)
        )
        os.system(command)

    def peer_lifecycle_chaincode_queryinstalled(self, apppath: str, packageid: str):
        command = (
            apppath
            + "bin/peer lifecycle chaincode queryinstalled --output json "
            + "| jq -r 'try (.installed_chaincodes[].package_id)'"
            + "| grep ^"
            + packageid
        )
        # print(command)
        os.system(command)

    def peer_lifecycle_chaincode_approveformyorg(
        self,
        apppath: str,
        invoke: bool,
        orderer: Orderer,
        orderername: str,
        cafile: str,
        channel: str,
        chaincodename: str,
        chaincodeversion: int,
        packageid: str,
    ):
        initrequired = ""
        if invoke:
            initrequired = " --init-required"
        command = (
            apppath
            + "bin/peer lifecycle chaincode approveformyorg -o localhost:"
            + str(orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + orderername
            + " --tls --cafile "
            + cafile
            + " --channelID "
            + channel
            + " --name "
            + chaincodename
            + " --version "
            + str(chaincodeversion)
            + " --package-id "
            + packageid
            + " --sequence "
            + str(chaincodeversion)
            + initrequired
        )
        # print(command)
        os.system(command)

    def peer_lifecycle_chaincode_checkcommitreadiness(
        self,
        apppath: str,
        invoke: bool,
        orderer: Orderer,
        orderername: str,
        cafile: str,
        channel: str,
        chaincodename: str,
        chaincodeversion: int,
    ):
        initrequired = ""
        if invoke:
            initrequired = " --init-required"
        command = (
            apppath
            + "bin/peer lifecycle chaincode checkcommitreadiness -o "
            + orderername
            + ":"
            + str(orderer.generallistenport)
            + " --tls --cafile "
            + cafile
            + " --channelID "
            + channel
            + " --name "
            + chaincodename
            + " --version "
            + str(chaincodeversion)
            + " --sequence "
            + str(chaincodeversion)
            + " --output json"
            + initrequired
        )
        # print(command)
        os.system(command)

    def peer_lifecycle_chaincode_commit(
        self,
        apppath: str,
        invoke: bool,
        orderer: Orderer,
        orderername: str,
        cafile: str,
        channel: str,
        chaincodename: str,
        domain: Domain,
        chaincodeversion: int,
    ):
        paths = Paths(domain)
        peeraddress = ""
        for org in domain.organizations:
            paths.set_org_paths(org)
            for peer in org.peers:
                paths.set_peer_paths(org, peer)
                peeraddress += (
                    " --peerAddresses localhost:"
                    + str(peer.peerlistenport)
                    + " --tlsRootCertFiles "
                    + paths.PEERCAROOT
                )

        initrequired = ""
        if invoke:
            initrequired = " --init-required"
        command = (
            apppath
            + "bin/peer lifecycle chaincode commit -o localhost:"
            + str(orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + orderername
            + " --tls --cafile "
            + cafile
            + " --channelID "
            + channel
            + " --name "
            + chaincodename
            + peeraddress
            + " --version "
            + str(chaincodeversion)
            + " --sequence "
            + str(chaincodeversion)
            + initrequired
        )
        # print(command)
        os.system(command)

    def peer_chaincode_invoke(
        self,
        apppath: str,
        invoke: bool,
        orderer: Orderer,
        orderername: str,
        cafile: str,
        channel: str,
        chaincodename: str,
        domain: Domain,
    ):
        paths = Paths(domain)
        peeraddress = ""
        for org in domain.organizations:
            paths.set_org_paths(org)
            for peer in org.peers:
                paths.set_peer_paths(org, peer)
                peeraddress += (
                    " --peerAddresses localhost:"
                    + str(peer.peerlistenport)
                    + " --tlsRootCertFiles "
                    + paths.PEERCAROOT
                )

        fcncall = '{"function":"","Args":[]}'
        initrequired = " -c " + "'" + fcncall + "'"

        if invoke:
            fcncall = '{"function":"InitLedger","Args":[]}'
            initrequired = " --isInit -c " + "'" + fcncall + "'"

        command = (
            apppath
            + "/bin/peer chaincode invoke -o localhost:"
            + str(orderer.generallistenport)
            + " --ordererTLSHostnameOverride "
            + orderername
            + " --tls --cafile "
            + cafile
            + " --channelID "
            + channel
            + " --name "
            + chaincodename
            + peeraddress
            + initrequired
        )
        # print(command)
        os.system(command)
