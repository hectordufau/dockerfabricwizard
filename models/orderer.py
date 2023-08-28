from typing import Optional, List

from pydantic import BaseModel


class Orderer(BaseModel):
    name: str = None
    FABRIC_CFG_PATH: str = "/var/hyperledger/fabric/config"
    FABRIC_LOGGING_SPEC: str = "INFO"
    #FABRIC_LOGGING_SPEC: str = "WARN:cauthdsl=debug:policies=debug:msp=debug"
    ORDERER_ADMIN_LISTENADDRESS: str = "0.0.0.0:7053"
    ORDERER_ADMIN_TLS_CERTIFICATE: str = "/var/hyperledger/orderer/tls/server.crt"
    ORDERER_ADMIN_TLS_CLIENTROOTCAS: str = "[/var/hyperledger/orderer/tls/ca.crt]"
    ORDERER_ADMIN_TLS_ENABLED: bool = True
    ORDERER_ADMIN_TLS_PRIVATEKEY: str = "/var/hyperledger/orderer/tls/server.key"
    ORDERER_ADMIN_TLS_ROOTCAS: str = "[/var/hyperledger/orderer/tls/ca.crt]"
    ORDERER_CHANNELPARTICIPATION_ENABLED: bool = True
    ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE: str = (
        "/var/hyperledger/orderer/tls/server.crt"
    )
    ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY: str = (
        "/var/hyperledger/orderer/tls/server.key"
    )
    ORDERER_GENERAL_CLUSTER_ROOTCAS: str = "[/var/hyperledger/orderer/tls/ca.crt]"
    ORDERER_GENERAL_LISTENADDRESS: str = "0.0.0.0"
    ORDERER_GENERAL_LISTENPORT: int = 0
    ORDERER_GENERAL_LOCALMSPDIR: str = "/var/hyperledger/orderer/msp"
    ORDERER_GENERAL_LOCALMSPID: str = "OrdererMSP"
    ORDERER_GENERAL_TLS_CERTIFICATE: str = "/var/hyperledger/orderer/tls/server.crt"
    ORDERER_GENERAL_TLS_ENABLED: bool = True
    ORDERER_GENERAL_TLS_PRIVATEKEY: str = "/var/hyperledger/orderer/tls/server.key"
    ORDERER_GENERAL_TLS_ROOTCAS: str = "[/var/hyperledger/orderer/tls/ca.crt]"
    ORDERER_OPERATIONS_LISTENADDRESS: Optional[str] = None
    adminlistenport: int = 0
    generallistenport: int = 0
    operationslistenport: int = 0
    volumes:  List[Optional[str]] = []
