from pydantic import BaseModel


class Peer(BaseModel):
    name: str = None
    CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG: str = '{"peername":"peername"}'
    CORE_CHAINCODE_EXECUTETIMEOUT: str = "300s"
    CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS: str = None
    CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD: str = "adminpw"
    CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME: str = "admin"
    CORE_LEDGER_STATE_STATEDATABASE: str = "CouchDB"
    CORE_OPERATIONS_LISTENADDRESS: str = None
    CORE_PEER_ADDRESS: str = None
    CORE_PEER_CHAINCODEADDRESS: str = None
    CORE_PEER_CHAINCODELISTENADDRESS: str = None
    CORE_PEER_GOSSIP_BOOTSTRAP: str = None
    CORE_PEER_GOSSIP_EXTERNALENDPOINT: str = None
    CORE_PEER_ID: str = None
    CORE_PEER_LISTENADDRESS: str = "0.0.0.0:7051"
    CORE_PEER_LOCALMSPID: str = None
    CORE_PEER_MSPCONFIGPATH: str = "/etc/hyperledger/fabric/msp"
    CORE_PEER_PROFILE_ENABLED: bool = False
    CORE_PEER_TLS_CERT_FILE: str = "/etc/hyperledger/fabric/tls/server.crt"
    CORE_PEER_TLS_ENABLED: bool = True
    CORE_PEER_TLS_KEY_FILE: str = "/etc/hyperledger/fabric/tls/server.key"
    CORE_PEER_TLS_ROOTCERT_FILE: str = "/etc/hyperledger/fabric/tls/ca.crt"
    CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE: str = None
    CORE_VM_ENDPOINT: str = "unix:///host/var/run/docker.sock"
    FABRIC_CFG_PATH: str = "/etc/hyperledger/peercfg"
    FABRIC_LOGGING_SPEC: str = "INFO"
    operationslistenport: int = 0
    chaincodelistenport: int = 0
    peerlistenport: int = 0
