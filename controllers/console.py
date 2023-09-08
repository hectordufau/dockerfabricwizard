import json
import os
from pathlib import Path
from typing import List

import validators
from python_on_whales import DockerClient
from rich.console import Console

from controllers.blockchain import Blockchain
from controllers.build import Build
from controllers.chaincode import ChaincodeDeploy
from controllers.firefly import Firefly
from controllers.header import Header
from controllers.requirements import Requirements
from controllers.run import Run
from models.ca import Ca
from models.chaincode import Chaincode
from models.database import Database
from models.domain import Domain
from models.orderer import Orderer
from models.organization import Organization
from models.peer import Peer

console = Console()
header = Header()


class ConsoleOutput:
    def __init__(self) -> None:
        self.domain = Domain()

    def start(self):
        console.print("")
        requirements = Requirements()
        requirements.checkAll()
        self.mainMenu()

    def questions(self):
        os.system("clear")
        header.header()
        portlist: List[int] = []

        console.print("[bold orange1]NEW NETWORK[/]")
        console.print("")
        console.print("[bold red]Press 'Q' to quit anytime[/]")
        console.print("")
        self.domain = Domain()

        domainname = console.input("[bold]Domain name:[/] ")
        if domainname.lower() == "q":
            self.mainMenu()
        while not validators.domain(domainname):
            domainname = console.input(
                "[bold red]Domain name not valid. Please retype again:[/] "
            )
            if domainname.lower() == "q":
                self.mainMenu()
        self.domain.name = domainname
        self.domain.networkname = domainname.split(".")[0]

        ordererdomain = Orderer()
        ordererdomain.name = "orderer"
        ordererdomain.generallistenport = 7050
        portlist.append(ordererdomain.generallistenport)
        ordererdomain.operationslistenport = 9443
        portlist.append(ordererdomain.operationslistenport)
        ordererdomain.adminlistenport = 7053
        portlist.append(ordererdomain.adminlistenport)
        ordererdomain.ORDERER_GENERAL_LISTENPORT = ordererdomain.generallistenport
        ordererdomain.ORDERER_OPERATIONS_LISTENADDRESS = (
            ordererdomain.name
            + "."
            + domainname
            + ":"
            + str(ordererdomain.operationslistenport)
        )
        ordererdomain.ORDERER_ADMIN_LISTENADDRESS = "0.0.0.0:" + str(
            ordererdomain.adminlistenport
        )
        ordererdomain.volumes = [
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + ordererdomain.name
            + "/msp:/var/hyperledger/orderer/msp",
            str(Path().absolute())
            + "/domains/"
            + self.domain.name
            + "/ordererOrganizations/"
            + ordererdomain.name
            + "/tls/:/var/hyperledger/orderer/tls",
            ordererdomain.name
            + "."
            + domainname
            + ":/var/hyperledger/production/orderer",
        ]
        self.domain.orderer = ordererdomain

        cadomain = Ca()
        cadomain.name = "ca.orderer"
        cadomain.FABRIC_CA_SERVER_CA_NAME = cadomain.name
        cadomain.volumes = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/fabric-ca/",
                cadomain.name,
                ":/etc/hyperledger/fabric-ca-server",
            ]
        )
        self.domain.ca = cadomain
        portlist.append(self.domain.ca.serverport)
        portlist.append(self.domain.ca.operationslistenport)

        qtyorgs = console.input("[bold]Number of Organizations:[/] ")
        if qtyorgs.lower() == "q":
            self.mainMenu()
        value = 0
        while not qtyorgs.isdigit():
            qtyorgs = console.input(
                "[bold red]Number of Organizations value not valid. Please retype again:[/] "
            )
            if qtyorgs.lower() == "q":
                self.mainMenu()
        value = int(qtyorgs)

        while not validators.between(value, min=1):
            qtyorgs = console.input(
                "[bold red]Number of Organizations value not valid, min 1. Please retype again:[/] "
            )
            if qtyorgs.lower() == "q":
                self.mainMenu()
            while not qtyorgs.isdigit():
                value = 0
            value = int(qtyorgs)

        self.domain.qtyorgs = value

        console.print("")
        iorgs = 1
        portpeer = 7051
        portcouchdb = 5984
        peeroperationlisten = 9444
        peerchaincodelistenport = 7052
        caorgserverport = self.domain.ca.serverport + 100
        caorgoplstport = self.domain.ca.operationslistenport + 100

        while iorgs <= self.domain.qtyorgs:
            org = Organization()
            orgname = console.input("[bold]Organization #" + str(iorgs) + " name:[/] ")
            if orgname.lower() == "q":
                self.mainMenu()
            while not orgname.isalpha():
                orgname = console.input(
                    "[bold red]Organization #"
                    + str(iorgs)
                    + " name not valid. Please retype again:[/] "
                )
                if orgname.lower() == "q":
                    self.mainMenu()
            org.name = orgname

            caorg = Ca()
            caorg.name = "ca." + org.name
            caorg.FABRIC_CA_SERVER_CA_NAME = caorg.name
            caorg.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS = "0.0.0.0:" + str(
                caorgoplstport
            )
            caorg.FABRIC_CA_SERVER_PORT = caorgserverport
            caorg.volumes = "".join(
                [
                    str(Path().absolute()),
                    "/domains/",
                    self.domain.name,
                    "/fabric-ca/",
                    caorg.name,
                    ":/etc/hyperledger/fabric-ca-server",
                ]
            )
            caorg.serverport = caorgserverport
            caorg.operationslistenport = caorgoplstport
            portlist.append(caorgserverport)
            portlist.append(caorgoplstport)
            org.ca = caorg

            qtypeers = console.input("[bold]Number of Peers:[/] ")
            if qtypeers.lower() == "q":
                self.mainMenu()
            valuepeers = 0
            while not qtypeers.isdigit():
                qtypeers = console.input(
                    "[bold red]Number of Peers value not valid. Please retype again:[/] "
                )
                if qtypeers.lower() == "q":
                    self.mainMenu()
            valuepeers = int(qtypeers)

            while not validators.between(valuepeers, min=1):
                qtypeers = console.input(
                    "[bold red]Number of Peers value not valid, min 1. Please retype again:[/] "
                )
                if qtypeers.lower() == "q":
                    self.mainMenu()
                while not qtypeers.isdigit():
                    valuepeers = 0
                valuepeers = int(qtypeers)

            org.qtypeers = valuepeers

            ipeers = 1

            while ipeers <= org.qtypeers:
                peer = Peer()
                peer.name = "peer" + str(ipeers) + "." + org.name
                peerport = console.input(
                    "[bold]Peer "
                    + peer.name
                    + " Port Number (ex. "
                    + str(portpeer)
                    + "):[/] "
                )
                if peerport.lower() == "q":
                    self.mainMenu()
                valueport = 0
                while not peerport.isdigit():
                    peerport = console.input(
                        "[bold red]Peer "
                        + peer.name
                        + " Port Number value not valid. Please retype again:[/] "
                    )
                    if peerport.lower() == "q":
                        self.mainMenu()
                valueport = int(peerport)

                validport = True
                while validport:
                    if valueport in portlist:
                        validport = True
                        peerport = console.input(
                            "[bold red]Peer "
                            + peer.name
                            + " Port Number value in use. Please retype again:[/] "
                        )
                        if peerport.lower() == "q":
                            self.mainMenu()
                        valueport = int(peerport)
                    else:
                        validport = False

                while not validators.between(valueport, min=portpeer, max=65535):
                    peerport = console.input(
                        "[bold red]Peer "
                        + peer.name
                        + " Port Number value not valid, min "
                        + str(portpeer)
                        + ". Please retype again:[/] "
                    )
                    if peerport.lower() == "q":
                        self.mainMenu()
                    while not peerport.isdigit():
                        valueport = 0
                    valueport = int(peerport)

                peer.volumes = [
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/"
                    + peer.name
                    + ":/etc/hyperledger/fabric",
                    peer.name + "." + self.domain.name + ":/var/hyperledger/production",
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + "/peerOrganizations/"
                    + org.name
                    + "/"
                    + peer.name
                    + "/peercfg"
                    + ":/etc/hyperledger/peercfg",
                    str(Path().absolute())
                    + "/domains/"
                    + self.domain.name
                    + ":/etc/hyperledger/organizations",
                    "/var/run/docker.sock:/host/var/run/docker.sock",
                ]

                database = Database()
                database.port = portcouchdb
                database.name = "db.peer" + str(ipeers)+"." + org.name
                database.COUCHDB_USER = "admin"
                database.COUCHDB_PASSWORD = "adminpw"

                peer.CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME = database.COUCHDB_USER
                peer.CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD = (
                    database.COUCHDB_PASSWORD
                )
                peer.CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS = (
                    database.name + "." + self.domain.name + ":5984"
                )
                peer.CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE = self.domain.networkname
                peer.CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG = (
                    '{"peername":"' + "peer" + str(ipeers) + org.name + '"}'
                )
                peer.CORE_PEER_LISTENADDRESS = "0.0.0.0:" + str(valueport)
                peer.CORE_OPERATIONS_LISTENADDRESS = (
                    peer.name + "." + self.domain.name + ":" + str(peeroperationlisten)
                )
                peer.peerlistenport = valueport
                peer.operationslistenport = peeroperationlisten
                portlist.append(peeroperationlisten)
                peer.CORE_PEER_ADDRESS = (
                    peer.name + "." + self.domain.name + ":" + str(valueport)
                )
                peer.CORE_PEER_CHAINCODEADDRESS = (
                    peer.name
                    + "."
                    + self.domain.name
                    + ":"
                    + str(peerchaincodelistenport)
                )
                peer.chaincodelistenport = peerchaincodelistenport
                peer.CORE_PEER_CHAINCODELISTENADDRESS = "0.0.0.0:" + str(
                    peerchaincodelistenport
                )
                portlist.append(peerchaincodelistenport)
                peer.CORE_PEER_GOSSIP_EXTERNALENDPOINT = peer.CORE_PEER_ADDRESS
                peer.CORE_PEER_GOSSIP_BOOTSTRAP = peer.CORE_PEER_ADDRESS
                peer.CORE_PEER_LOCALMSPID = org.name + "MSP"
                peer.CORE_PEER_ID = peer.name + "." + self.domain.name

                peer.database = database

                org.peers.append(peer)

                portlist.append(valueport)

                ipeers += 1
                portpeer += 1000
                portcouchdb += 1000
                peeroperationlisten += 1000
                peerchaincodelistenport += 1000

            self.domain.organizations.append(org)

            iorgs += 1
            portpeer += 1000
            caorgserverport += 100
            caorgoplstport += 100
            console.print("")

        build = Build(self.domain)
        build.buildAll()
        blockchain = Blockchain(self.domain)
        blockchain.buildAll()
        self.networkSelected(self.domain.name)

    def createOrganization(self, domain: Domain):
        os.system("clear")
        header.header()
        portlist: List[int] = []

        console.print("[bold orange1]NEW ORGANIZATION[/]")
        console.print("")
        console.print("[bold red]Press 'Q' to quit anytime[/]")
        console.print("")

        iorgs = domain.qtyorgs + 1
        portpeer = 0
        peeroperationlisten = 0
        peerchaincodelistenport = 0
        portcouchdb = 0
        caorgserverport = 0
        caorgoplstport = 0

        portlist.append(domain.ca.serverport)
        portlist.append(domain.ca.operationslistenport)
        portlist.append(domain.orderer.adminlistenport)
        portlist.append(domain.orderer.generallistenport)
        portlist.append(domain.orderer.operationslistenport)
        for org in domain.organizations:
            portlist.append(org.ca.serverport)
            portlist.append(org.ca.operationslistenport)
            for peer in org.peers:
                portlist.append(peer.operationslistenport)
                peeroperationlisten = peer.operationslistenport + 1000
                portlist.append(peer.chaincodelistenport)
                peerchaincodelistenport = peer.chaincodelistenport + 1000
                portlist.append(peer.peerlistenport)
                portpeer = peer.peerlistenport + 1000
                portlist.append(peer.database.port)
                portcouchdb = peer.database.port + 1000

            caorgserverport = org.ca.serverport + 100
            caorgoplstport = org.ca.operationslistenport + 100

        org = Organization()
        orgname = console.input("[bold]Organization #" + str(iorgs) + " name:[/] ")
        if orgname.lower() == "q":
            self.networkSelected(domain.name)
        while not orgname.isalpha():
            orgname = console.input(
                "[bold red]Organization #"
                + str(iorgs)
                + " name not valid. Please retype again:[/] "
            )
            if orgname.lower() == "q":
                self.networkSelected(domain.name)
        org.name = orgname

        caorg = Ca()
        caorg.name = "ca." + org.name
        caorg.FABRIC_CA_SERVER_CA_NAME = caorg.name
        caorg.FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS = "0.0.0.0:" + str(
            caorgoplstport
        )
        caorg.FABRIC_CA_SERVER_PORT = caorgserverport
        caorg.volumes = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                domain.name,
                "/fabric-ca/",
                caorg.name,
                ":/etc/hyperledger/fabric-ca-server",
            ]
        )
        caorg.serverport = caorgserverport
        caorg.operationslistenport = caorgoplstport
        portlist.append(caorgserverport)
        portlist.append(caorgoplstport)
        org.ca = caorg

        qtypeers = console.input("[bold]Number of Peers:[/] ")
        if qtypeers.lower() == "q":
            self.networkSelected(domain.name)
        valuepeers = 0
        while not qtypeers.isdigit():
            qtypeers = console.input(
                "[bold red]Number of Peers value not valid. Please retype again:[/] "
            )
            if qtypeers.lower() == "q":
                self.networkSelected(domain.name)
        valuepeers = int(qtypeers)

        while not validators.between(valuepeers, min=1):
            qtypeers = console.input(
                "[bold red]Number of Peers value not valid, min 1. Please retype again:[/] "
            )
            if qtypeers.lower() == "q":
                self.networkSelected(domain.name)
            while not qtypeers.isdigit():
                valuepeers = 0
            valuepeers = int(qtypeers)

        org.qtypeers = valuepeers

        ipeers = 1

        while ipeers <= org.qtypeers:
            peer = Peer()
            peer.name = "peer" + str(ipeers) + "." + org.name
            peerport = console.input(
                "[bold]Peer "
                + peer.name
                + " Port Number (ex. "
                + str(portpeer)
                + "):[/] "
            )
            if peerport.lower() == "q":
                self.networkSelected(domain.name)
            valueport = 0
            while not peerport.isdigit():
                peerport = console.input(
                    "[bold red]Peer "
                    + peer.name
                    + " Port Number value not valid. Please retype again:[/] "
                )
                if peerport.lower() == "q":
                    self.networkSelected(domain.name)
            valueport = int(peerport)

            validport = True
            while validport:
                if valueport in portlist:
                    validport = True
                    peerport = console.input(
                        "[bold red]Peer "
                        + peer.name
                        + " Port Number value in use. Please retype again:[/] "
                    )
                    if peerport.lower() == "q":
                        self.networkSelected(domain.name)
                    valueport = int(peerport)
                else:
                    validport = False

            while not validators.between(valueport, min=portpeer, max=65535):
                peerport = console.input(
                    "[bold red]Peer "
                    + peer.name
                    + " Port Number value not valid, min "
                    + str(portpeer)
                    + ". Please retype again:[/] "
                )
                if peerport.lower() == "q":
                    self.networkSelected(domain.name)
                while not peerport.isdigit():
                    valueport = 0
                valueport = int(peerport)

            peer.volumes = [
                str(Path().absolute())
                + "/domains/"
                + domain.name
                + "/peerOrganizations/"
                + org.name
                + "/"
                + peer.name
                + ":/etc/hyperledger/fabric",
                peer.name + "." + domain.name + ":/var/hyperledger/production",
                str(Path().absolute())
                + "/domains/"
                + domain.name
                + "/peerOrganizations/"
                + org.name
                + "/"
                + peer.name
                + "/peercfg"
                + ":/etc/hyperledger/peercfg",
                str(Path().absolute())
                + "/domains/"
                + domain.name
                + ":/etc/hyperledger/organizations",
                "/var/run/docker.sock:/host/var/run/docker.sock",
            ]

            database = Database()
            database.port = portcouchdb
            database.name = "db.peer" + str(ipeers)+"." + org.name
            database.COUCHDB_USER = "admin"
            database.COUCHDB_PASSWORD = "adminpw"

            peer.CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME = database.COUCHDB_USER
            peer.CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD = database.COUCHDB_PASSWORD
            peer.CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS = (
                database.name + "." + self.domain.name + ":5984"
            )
            peer.CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE = domain.networkname
            peer.CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG = (
                '{"peername":"' + "peer" + str(ipeers) + org.name + '"}'
            )
            peer.CORE_PEER_LISTENADDRESS = "0.0.0.0:" + str(valueport)
            peer.CORE_OPERATIONS_LISTENADDRESS = (
                peer.name + "." + domain.name + ":" + str(peeroperationlisten)
            )
            peer.peerlistenport = valueport
            peer.operationslistenport = peeroperationlisten
            portlist.append(peeroperationlisten)
            peer.CORE_PEER_ADDRESS = (
                peer.name + "." + domain.name + ":" + str(valueport)
            )
            peer.CORE_PEER_CHAINCODEADDRESS = (
                peer.name + "." + domain.name + ":" + str(peerchaincodelistenport)
            )
            peer.chaincodelistenport = peerchaincodelistenport
            peer.CORE_PEER_CHAINCODELISTENADDRESS = "0.0.0.0:" + str(
                peerchaincodelistenport
            )
            portlist.append(peerchaincodelistenport)
            peer.CORE_PEER_GOSSIP_EXTERNALENDPOINT = peer.CORE_PEER_ADDRESS
            peer.CORE_PEER_GOSSIP_BOOTSTRAP = peer.CORE_PEER_ADDRESS
            peer.CORE_PEER_LOCALMSPID = org.name + "MSP"
            peer.CORE_PEER_ID = peer.name + "." + domain.name

            peer.database = database

            org.peers.append(peer)

            portlist.append(valueport)

            ipeers += 1
            portpeer += 1000
            portcouchdb += 1000
            peeroperationlisten += 1000
            peerchaincodelistenport += 1000

        domain.organizations.append(org)
        domain.qtyorgs += 1
        console.print("")

        build = Build(domain)
        build.buildNewOrganization(org)
        blockchain = Blockchain(domain)
        blockchain.buildNewOrganization(org)
        self.networkSelected(domain.name)

    def createPeer(self, domain: Domain, org: Organization):
        portlist: List[int] = []

        portpeer = 0
        peeroperationlisten = 0
        peerchaincodelistenport = 0
        portcouchdb = 0

        portlist.append(domain.ca.serverport)
        portlist.append(domain.ca.operationslistenport)
        portlist.append(domain.orderer.adminlistenport)
        portlist.append(domain.orderer.generallistenport)
        portlist.append(domain.orderer.operationslistenport)
        for org in domain.organizations:
            portlist.append(org.ca.serverport)
            portlist.append(org.ca.operationslistenport)
            for peer in org.peers:
                portlist.append(peer.operationslistenport)
                peeroperationlisten = peer.operationslistenport + 1000
                portlist.append(peer.chaincodelistenport)
                peerchaincodelistenport = peer.chaincodelistenport + 1000
                portlist.append(peer.peerlistenport)
                portpeer = peer.peerlistenport + 1000
                portlist.append(peer.database.port)
                portcouchdb = peer.database.port + 1000

        ipeers = org.qtypeers + 1
        peer = Peer()
        peer.name = "peer" + str(ipeers) + "." + org.name
        peerport = console.input(
            "[bold]Peer " + peer.name + " Port Number (ex. " + str(portpeer) + "):[/] "
        )
        if peerport.lower() == "q":
            self.networkSelected(domain.name)
        valueport = 0
        while not peerport.isdigit():
            peerport = console.input(
                "[bold red]Peer "
                + peer.name
                + " Port Number value not valid. Please retype again:[/] "
            )
            if peerport.lower() == "q":
                self.networkSelected(domain.name)
        valueport = int(peerport)

        validport = True
        while validport:
            if valueport in portlist:
                validport = True
                peerport = console.input(
                    "[bold red]Peer "
                    + peer.name
                    + " Port Number value in use. Please retype again:[/] "
                )
                if peerport.lower() == "q":
                    self.networkSelected(domain.name)
                valueport = int(peerport)
            else:
                validport = False

        while not validators.between(valueport, min=portpeer, max=65535):
            peerport = console.input(
                "[bold red]Peer "
                + peer.name
                + " Port Number value not valid, min "
                + str(portpeer)
                + ". Please retype again:[/] "
            )
            if peerport.lower() == "q":
                self.networkSelected(domain.name)
            while not peerport.isdigit():
                valueport = 0
            valueport = int(peerport)

        peer.volumes = [
            str(Path().absolute())
            + "/domains/"
            + domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + ":/etc/hyperledger/fabric",
            peer.name + "." + domain.name + ":/var/hyperledger/production",
            str(Path().absolute())
            + "/domains/"
            + domain.name
            + "/peerOrganizations/"
            + org.name
            + "/"
            + peer.name
            + "/peercfg"
            + ":/etc/hyperledger/peercfg",
            str(Path().absolute())
            + "/domains/"
            + domain.name
            + ":/etc/hyperledger/organizations",
            "/var/run/docker.sock:/host/var/run/docker.sock",
        ]

        database = Database()
        database.port = portcouchdb
        database.name = "db.peer" + str(ipeers)+"." + org.name
        database.COUCHDB_USER = "admin"
        database.COUCHDB_PASSWORD = "adminpw"

        peer.CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME = database.COUCHDB_USER
        peer.CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD = database.COUCHDB_PASSWORD
        peer.CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS = (
            database.name + "." + self.domain.name + ":5984"
        )
        peer.CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE = domain.networkname
        peer.CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG = (
            '{"peername":"' + "peer" + str(ipeers) + org.name + '"}'
        )
        peer.CORE_PEER_LISTENADDRESS = "0.0.0.0:" + str(valueport)
        peer.CORE_OPERATIONS_LISTENADDRESS = (
            peer.name + "." + domain.name + ":" + str(peeroperationlisten)
        )
        peer.peerlistenport = valueport
        peer.operationslistenport = peeroperationlisten
        portlist.append(peeroperationlisten)
        peer.CORE_PEER_ADDRESS = peer.name + "." + domain.name + ":" + str(valueport)
        peer.CORE_PEER_CHAINCODEADDRESS = (
            peer.name + "." + domain.name + ":" + str(peerchaincodelistenport)
        )
        peer.chaincodelistenport = peerchaincodelistenport
        peer.CORE_PEER_CHAINCODELISTENADDRESS = "0.0.0.0:" + str(
            peerchaincodelistenport
        )
        portlist.append(peerchaincodelistenport)
        peer.CORE_PEER_GOSSIP_EXTERNALENDPOINT = peer.CORE_PEER_ADDRESS
        peer.CORE_PEER_GOSSIP_BOOTSTRAP = peer.CORE_PEER_ADDRESS
        peer.CORE_PEER_LOCALMSPID = org.name + "MSP"
        peer.CORE_PEER_ID = peer.name + "." + domain.name

        peer.database = database

        org.peers.append(peer)

        org.qtypeers += 1

        build = Build(domain)
        build.buildNewPeer(org, peer)
        blockchain = Blockchain(domain)
        blockchain.joinChannelPeer(org, peer)
        self.networkSelected(domain.name)

    def mainMenu(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]MENU[/]")
        console.print("")
        console.print("[bold white]N - New network[/]")
        console.print("[bold white]S - Select an existing network[/]")
        console.print("[bold white]D - Docker status[/]")
        console.print("[bold white]C - Clean all Docker resources[/]")
        console.print("[bold white]Q - Quit[/]")
        console.print("")
        option = console.input("[bold]Select an option (N,S,D,C or Q):[/] ")
        console.print("")

        selectoption = True
        while selectoption:
            match option.lower():
                case "n":
                    selectoption = False
                    self.questions()
                case "s":
                    selectoption = False
                    self.selectNetwork()
                case "d":
                    selectoption = False
                    self.checkDockerStatus()
                case "c":
                    selectoption = False
                    self.cleanDockerAll()
                case "q":
                    selectoption = False
                    exit(0)
                case _:
                    option = console.input("[bold]Select an option (N,S,D,C or Q):[/] ")
                    console.print("")

    def checkDockerStatus(self, domain: Domain = None):
        os.system("clear")
        header.header()
        console.print("[bold orange1]DOCKER STATUS[/]")
        console.print("")
        console.print("[bold]Containers[/]")
        console.print("")
        if domain is None:
            os.system("docker ps")
        else:
            os.system('docker ps -f "network=' + domain.networkname + '"')
        console.print("")
        console.print("[bold]Volumes[/]")
        console.print("")
        os.system("docker volume ls")
        console.print("")
        console.print("[bold]Networks[/]")
        console.print("")
        if domain is None:
            os.system("docker network ls")
        else:
            os.system('docker network ls -f "name=' + domain.networkname + '"')
        console.print("")
        console.print("[bold white]M - Return to menu[/]")
        console.print("[bold white]Q - Quit[/]")
        console.print("")
        option = console.input("[bold]Select an option (M or Q):[/] ")
        console.print("")

        selectoption = True
        while selectoption:
            match option.lower():
                case "m":
                    selectoption = False
                    if domain is None:
                        self.mainMenu()
                    else:
                        self.networkSelected(domain.name)
                case "q":
                    selectoption = False
                    exit(0)
                case _:
                    option = console.input("[bold]Select an option (M or Q):[/] ")
                    console.print("")

    def cleanDockerAll(self, domain: Domain = None):
        os.system("clear")
        header.header()
        console.print("[bold orange1]DOCKER CLEANING[/]")
        console.print("")
        console.print("[bold green]Removing all Docker resources[/]")
        console.print("[bold]# Stopping containers[/]")
        if domain is None:
            os.system("docker stop $(docker ps -a -q)")
        else:
            os.system(
                'docker stop $(docker ps -a -q -f "network=' + domain.networkname + '")'
            )
        console.print("[bold]# Removing containers and volumes[/]")
        if domain is None:
            os.system("docker rm -v $(docker ps -a -q) -f")
        else:
            os.system(
                'docker rm -v $(docker ps -a -q -f "network='
                + domain.networkname
                + '")'
            )
        if domain is not None:
            console.print("[bold]# Removing network[/]")
            os.system("docker network rm " + domain.networkname + " -f")

        if domain is None:
            console.print("[bold]# Removing images[/]")
            os.system("docker rmi $(docker images -a -q)")
            console.print("[bold]# Removing other resources[/]")
            os.system("docker system prune -a -f")
            os.system("docker volume prune -a -f")
            console.print("")
            self.mainMenu()
        else:
            self.networkSelected(domain.name)

    def selectNetwork(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]SELECT A NETWORK[/]")
        console.print("")
        dirdomains = "".join(
            [
                str(Path().absolute()),
                "/domains",
            ]
        )
        listnetworks = [
            name
            for name in os.listdir(dirdomains)
            if os.path.isdir(os.path.join(dirdomains, name))
        ]
        for i, folder in enumerate(listnetworks):
            console.print("[bold]" + str(i) + " : " + folder)
        console.print("[bold]P - Return to previous menu[/]")
        console.print("[bold]Q - Quit[/]")
        console.print("")

        option = console.input("[bold]Select a network:[/] ")
        selected = True
        while selected:
            if option.lower() == "p":
                selected = False
                console.print("")
                self.mainMenu()
            elif option.lower() == "q":
                selected = False
                console.print("")
                exit(0)
            elif option.isdigit() and (int(option) <= (len(listnetworks) - 1)):
                selected = False
                console.print("")
                self.networkSelected(listnetworks[int(option)])
            else:
                option = console.input(
                    "[bold red]Wrong option.[/] [bold white]Select a network:[/] "
                )
                console.print("")

    def selectOrganization(self, domain: Domain):
        os.system("clear")
        header.header()
        console.print("[bold orange1]ADDING A PEER[/]")
        console.print("")

        for i, org in enumerate(domain.organizations):
            console.print("[bold]" + str(i) + " : " + org.name)
        console.print("[bold]P - Return to previous menu[/]")
        console.print("[bold]Q - Quit[/]")
        console.print("")

        option = console.input("[bold]Select an Organization:[/] ")
        selected = True
        while selected:
            if option.lower() == "p":
                selected = False
                console.print("")
                self.mainMenu()
            elif option.lower() == "q":
                selected = False
                console.print("")
                exit(0)
            elif option.isdigit() and (int(option) <= (len(domain.organizations) - 1)):
                selected = False
                console.print("")
                self.createPeer(domain, domain.organizations[int(option)])
            else:
                option = console.input(
                    "[bold red]Wrong option.[/] [bold white]Select an Organization:[/] "
                )
                console.print("")

    def networkSelected(self, network: str):
        os.system("clear")
        header.header()
        console.print("[bold orange1]NETWORK " + network + "[/]")
        console.print("")
        console.print("[bold white]N - Network status[/]")
        console.print("[bold white]O - Add organization[/]")
        console.print("[bold white]P - Add peer[/]")
        console.print("[bold white]A - Add chaincode[/]")
        console.print("[bold white]F - Run Firefly[/]")
        console.print("[bold white]Y - Remove Firefly[/]")
        console.print("[bold white]G - Start network[/]")
        console.print("[bold white]S - Stop network[/]")
        console.print("[bold white]C - Clean docker[/]")
        console.print("[bold white]D - Delete network and configs[/]")
        console.print("[bold white]R - Return to previous menu[/]")
        console.print("[bold white]M - Return to main menu[/]")
        console.print("[bold white]Q - Quit[/]")
        console.print("")
        option = console.input(
            "[bold]Select an option (N,O,P,A,F,Y,G,S,C,D,R,M or Q):[/] "
        )
        console.print("")

        configfile = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                network,
                "/setup.json",
            ]
        )
        domain: Domain() = None
        with open(configfile) as config_file:
            j = json.loads(config_file.read())
            domain = Domain(**j)

        netpath = str(Path().absolute()) + "/domains/" + domain.name
        dockpath = netpath + "/compose/"
        docker = DockerClient(
            compose_files=[
                dockpath + "compose-ca.yaml",
                dockpath + "compose-net.yaml",
                dockpath + "compose-orderer.yaml",
            ]
        )

        selectoption = True
        while selectoption:
            match option.lower():
                case "n":
                    selectoption = False
                    self.checkDockerStatus(domain)
                case "o":
                    selectoption = False
                    self.createOrganization(domain)
                    self.networkSelected(domain.name)
                case "p":
                    selectoption = False
                    self.selectOrganization(domain)
                    self.networkSelected(domain.name)
                case "a":
                    selectoption = False
                    self.selectChaincode(domain)
                    self.networkSelected(domain.name)
                case "f":
                    selectoption = False
                    self.runFirefly(domain)
                    self.networkSelected(domain.name)
                case "y":
                    selectoption = False
                    self.removeFirefly(domain)
                    self.networkSelected(domain.name)
                case "g":
                    selectoption = False
                    run = Run(domain)
                    exists = run.checkContainer()
                    run.runAll()
                    if not exists:
                        blockchain = Blockchain(domain)
                        blockchain.rebuild()
                    self.checkDockerStatus(domain)
                case "s":
                    selectoption = False
                    console.print("[bold white]# Stopping network...[/]")
                    docker.compose.stop()
                    self.checkDockerStatus(domain)
                case "c":
                    selectoption = False
                    console.print("[bold white]# Cleaning...[/]")
                    docker.compose.down(
                        remove_orphans=True, remove_images="all", volumes=True
                    )
                    docker.system.prune(True, True)
                    self.networkSelected(domain.name)
                case "d":
                    selectoption = False
                    console.print("[bold white]# Deleting...[/]")
                    ffpath = (
                        os.environ["HOME"] + "/.firefly/stacks/" + domain.networkname
                    )
                    ffdir = os.path.isdir(ffpath)
                    if ffdir:
                        os.system(
                            str(Path().absolute())
                            + "/bin/ff stop "
                            + domain.networkname
                        )
                        os.system(
                            str(Path().absolute())
                            + "/bin/ff remove -f "
                            + domain.networkname
                        )
                    docker.compose.down(
                        remove_orphans=True, remove_images="all", volumes=True
                    )
                    clist = docker.container.list(True)
                    if len(clist) > 0:
                        docker.container.stop(clist)
                    docker.system.prune(True, True)
                    os.system("rm -fR " + netpath)
                    self.selectNetwork()
                case "r":
                    selectoption = False
                    self.selectNetwork()
                case "m":
                    selectoption = False
                    self.mainMenu()
                case "q":
                    selectoption = False
                    exit(0)
                case _:
                    option = console.input(
                        "[bold]Select an option (N,O,P,A,F,Y,G,S,C,D,R,M or Q):[/] "
                    )
                    console.print("")

    def selectChaincode(self, domain: Domain):
        os.system("clear")
        header.header()
        console.print("[bold orange1]SELECT A CHAINCODE[/]")
        console.print("")
        dirchaincodes = "".join(
            [
                str(Path().absolute()),
                "/chaincodes/",
            ]
        )

        chaincode = Chaincode()

        portlist: List[int] = []
        ccport = 1999
        portlist.append(domain.ca.serverport)
        portlist.append(domain.ca.operationslistenport)
        portlist.append(domain.orderer.adminlistenport)
        portlist.append(domain.orderer.generallistenport)
        portlist.append(domain.orderer.operationslistenport)
        portlist.append(9999)  # Exclusive for Firefly chaincode
        for org in domain.organizations:
            portlist.append(org.ca.serverport)
            portlist.append(org.ca.operationslistenport)
            for peer in org.peers:
                portlist.append(peer.operationslistenport)
                portlist.append(peer.chaincodelistenport)
                portlist.append(peer.peerlistenport)
                portlist.append(peer.database.port)
        for cc in domain.chaincodes:
            portlist.append(cc.ccport)
            ccport = cc.ccport + 1000

        listccsrc = [
            name
            for name in os.listdir(dirchaincodes)
            if os.path.isdir(os.path.join(dirchaincodes, name))
        ]
        for i, folder in enumerate(listccsrc):
            console.print("[bold]" + str(i) + " : " + folder)
        console.print("[bold]P - Return to previous menu[/]")
        console.print("[bold]Q - Quit[/]")
        console.print("")

        option = console.input("[bold]Select a chaincode:[/] ")
        selected = True
        while selected:
            if option.lower() == "p":
                selected = False
                console.print("")
                self.networkSelected(domain.name)
            elif option.lower() == "q":
                selected = False
                console.print("")
                exit(0)
            elif option.isdigit() and (int(option) <= (len(listccsrc) - 1)):
                selected = False
                console.print("")
                chaincode.name = listccsrc[int(option)]
            else:
                option = console.input(
                    "[bold red]Wrong option.[/] [bold white]Select a chaincode:[/] "
                )
                console.print("")

        builded = False
        for cc in domain.chaincodes:
            if chaincode.name == cc.name:
                builded = True
                chaincode = cc

        previous = False
        if builded:
            useprevious = console.input(
                "[bold white]This chaincode was installed previously. Do you want to use same config? (y/n):[/] "
            )

            selected = True
            while selected:
                if useprevious.lower() == "y":
                    selected = False
                    previous = True
                    console.print("")
                elif useprevious.lower() == "n":
                    selected = False
                    previous = False
                    console.print("")
                elif useprevious.lower() == "p":
                    selected = False
                    console.print("")
                    self.networkSelected(domain.name)
                elif useprevious.lower() == "q":
                    selected = False
                    console.print("")
                    exit(0)
                else:
                    useprevious = console.input(
                        "[bold red]Wrong option.[/] [bold white]Do you want to use same config? (y/n):[/] "
                    )
                    console.print("")

        if previous:
            self.chaincodeSelected(domain, chaincode)
        else:
            hasinit = console.input(
                "[bold white]Invoke init function required (y/n):[/] "
            )
            invoke = False
            selected = True
            while selected:
                if hasinit.lower() == "y":
                    selected = False
                    invoke = True
                    console.print("")
                elif hasinit.lower() == "n":
                    selected = False
                    console.print("")
                elif hasinit.lower() == "p":
                    selected = False
                    console.print("")
                    self.networkSelected(domain.name)
                elif hasinit.lower() == "q":
                    selected = False
                    console.print("")
                    exit(0)
                else:
                    hasinit = console.input(
                        "[bold red]Wrong option.[/] [bold white]Invoke init function required (y/n):[/] "
                    )
                    console.print("")

            chaincode.invoke = invoke

            if invoke:
                ccfunction = console.input("[bold]Invoke function name:[/] ")
                if ccfunction.lower() == "q":
                    self.networkSelected(domain.name)
                while not ccfunction.isalpha():
                    ccfunction = console.input(
                        "[bold red]Invoke function name not valid. Please retype again:[/] "
                    )
                    if ccfunction.lower() == "q":
                        self.networkSelected(domain.name)
                        break
                chaincode.function = ccfunction
                console.print("")

            if not builded:
                ccportn = console.input(
                    "[bold]Chaincode Port Number (ex. " + str(ccport) + "):[/] "
                )
                if ccportn.lower() == "q":
                    self.networkSelected(domain.name)
                valueport = 0
                while not ccportn.isdigit():
                    ccportn = console.input(
                        "[bold red]Chaincode Port Number value not valid. Please retype again:[/] "
                    )
                    if ccportn.lower() == "q":
                        self.networkSelected(domain.name)
                        break
                valueport = int(ccportn)

                validport = True
                while validport:
                    if valueport in portlist:
                        validport = True
                        ccportn = console.input(
                            "[bold red]Chaincode Port Number value in use. Please retype again:[/] "
                        )
                        if ccportn.lower() == "q":
                            self.networkSelected(domain.name)
                            break
                        valueport = int(ccportn)
                    else:
                        validport = False

                while not validators.between(valueport, min=ccport, max=65535):
                    ccportn = console.input(
                        "[bold red]Chaincode Port Number value not valid, min "
                        + str(ccport)
                        + ". Please retype again:[/] "
                    )
                    if ccportn.lower() == "q":
                        self.networkSelected(domain.name)
                        break
                    while not ccportn.isdigit():
                        valueport = 0
                    valueport = int(ccportn)

                chaincode.ccport = valueport
                console.print("")

            hastls = console.input("[bold white]Use TLS Connection (y/n):[/] ")
            tls = False
            selected = True
            while selected:
                if hastls.lower() == "y":
                    selected = False
                    tls = True
                    console.print("")
                elif hastls.lower() == "n":
                    selected = False
                    console.print("")
                elif hastls.lower() == "p":
                    selected = False
                    console.print("")
                    self.networkSelected(domain.name)
                elif hastls.lower() == "q":
                    selected = False
                    console.print("")
                    exit(0)
                else:
                    hastls = console.input(
                        "[bold red]Wrong option.[/] [bold white]Use TLS Connection (y/n):[/] "
                    )
                    console.print("")

            chaincode.usetls = tls
            #chaincode.usetls = False

            self.chaincodeSelected(domain, chaincode)

    def chaincodeSelected(self, domain: Domain, chaincode: Chaincode):
        chaincode = ChaincodeDeploy(domain, chaincode)
        chaincode.buildAll()

    def runFirefly(self, domain: Domain):
        firefly = Firefly(domain)
        firefly.buildAll()

    def removeFirefly(self, domain: Domain):
        firefly = Firefly(domain)
        firefly.remove()
