import os

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
        # caname: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client enroll -d -u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --csr.hosts localhost"
            + " --tls.certfiles "
            + certfile
        )
        print(command)
        os.system(command)

    def enroll_msp(
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
        os.environ["FABRIC_CA_CLIENT_MSPDIR"] = "msp"
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client enroll -d -u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --csr.hosts localhost"
            + " --tls.certfiles "
            + certfile
        )
        print(command)
        os.system(command)

    def enroll_tls(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        # caname: str,
        csrhosts: [],
        myhost: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home
        os.environ["FABRIC_CA_CLIENT_MSPDIR"] = "tls"
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client enroll -d -u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --enrollment.profile tls --csr.hosts "
            + ",".join(csrhosts)
            + " --myhost "
            + myhost
            + " --tls.certfiles "
            + certfile
        )
        print(command)
        os.system(command)

    def register_orderer(
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
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client register -d -u https://localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type orderer "
            + " --tls.certfiles "
            + certfile
        )
        print(command)
        os.system(command)

    def register_orderer_admin(
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
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client register -d -u https://localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type admin "
            + " --tls.certfiles "
            + certfile
            + ' --id.attrs "hf.Registrar.Roles=client,hf.Registrar.Attributes=*,hf.Revoker=true,hf.GenCRL=true,admin=true:ecert,abac.init=true:ecert"'
        )
        print(command)
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
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client register -d -u https://localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type admin "
            + " --tls.certfiles "
            + certfile
        )
        print(command)
        os.system(command)

    def register_peer(
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
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client register -d -u https://localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type peer "
            + " --tls.certfiles "
            + certfile
        )
        print(command)
        os.system(command)

    def register_client(
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
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client register -d -u https://localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type client "
            + " --tls.certfiles "
            + certfile
        )
        print(command)
        os.system(command)

    def register_user(
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
        print("FABRIC_CA_CLIENT_HOME=" + home)
        command = (
            apppath
            + "bin/fabric-ca-client register -d -u https://localhost:"
            + str(port)
            # + " --caname "
            # + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type user "
            + " --tls.certfiles "
            + certfile
        )
        print(command)
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
        print(command)
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
        print(command)
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
        print(command)
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
        print(command)
        os.system(command)

    def peer_channel_signconfigtx(self, configtx: str, org: Organization):
        command = (
            "peer channel signconfigtx -f "
            + configtx
            + org.name
            + "_update_in_envelope.pb"
        )
        print(command)
        os.system(command)

    def configtxlator_proto_decode(self, apppath: str, configpath: str, file: str):
        command = (
            apppath
            + "bin/configtxlator proto_decode --input "
            + configpath
            + file
            + ".pb --type common.Block --output "
            + configpath
            + file
            + ".json"
        )
        print(command)
        os.system(command)

    def configtxlator_proto_encode(self, apppath: str, configpath: str, file: str):
        command = (
            apppath
            + "bin/configtxlator proto_encode --input "
            + configpath
            + file
            + ".json --type common.Config --output "
            + configpath
            + file
            + ".pb"
        )
        print(command)
        os.system(command)

    def configtxlator_compute_update(self, apppath: str, channel: str, configpath: str):
        command = (
            apppath
            + "/bin/configtxlator compute_update --channel_id "
            + channel
            + " --original "
            + configpath
            + "config.pb --updated "
            + configpath
            + "modified_config.pb --output "
            + configpath
            + "config_update.pb"
        )
        print(command)
        os.system(command)

    def jq_export_config(self, configpath: str):
        command = (
            "jq .data.data[0].payload.data.config "
            + configpath
            + "config_block.json > "
            + configpath
            + "config.json"
        )
        print(command)
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
        print(command)
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
        print(command)
        os.system(command)
