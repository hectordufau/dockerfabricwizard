import json
import os
from pathlib import Path
from typing import List

import validators
from rich.console import Console

from controllers.build import Build
from controllers.requirements import Requirements
from controllers.run import Run
from models.ca import Ca
from models.domain import Domain
from models.orderer import Orderer
from models.organization import Organization
from models.peer import Peer

console = Console()


class ConsoleOutput:
    def __init__(self) -> None:
        self.domain = Domain()

    def start(self):
        console.print("")
        requirements = Requirements()
        requirements.checkAll()
        self.mainMenu()

    def header(self):
        console.print(
            """[blue]
        ██████████                     █████                        
        ░███░░░░███                   ░░███                         
        ░███   ░░███  ██████   ██████  ░███ █████  ██████  ████████ 
        ░███    ░███ ███░░███ ███░░███ ░███░░███  ███░░███░░███░░███
        ░███    ░███░███ ░███░███ ░░░  ░██████░  ░███████  ░███ ░░░ 
        ░███    ███ ░███ ░███░███  ███ ░███░░███ ░███░░░   ░███     
        ██████████  ░░██████ ░░██████  ████ █████░░██████  █████    
        ░░░░░░░░░░    ░░░░░░   ░░░░░░  ░░░░ ░░░░░  ░░░░░░  ░░░░░[/]
        [red]
        ███████████           █████                ███              
        ░███░░░░░░█           ░███                ░░░               
        ░███   █ ░   ██████   ░███████  ████████  ████   ██████     
        ░███████    ░░░░░███  ░███░░███░░███░░███░░███  ███░░███    
        ░███░░░█     ███████  ░███ ░███ ░███ ░░░  ░███ ░███ ░░░     
        ░███  ░     ███░░███  ░███ ░███ ░███      ░███ ░███  ███    
        █████      ░░████████ ████████  █████     █████░░██████     
        ░░░░░        ░░░░░░░░ ░░░░░░░░  ░░░░░     ░░░░░  ░░░░░░[/]
        """
        )
        console.print("")
        console.print("[bold]Welcome to the DockerFabric Wizard![/]")
        console.print("")
        console.print(
            "You will guided during all Hyperledger Fabric deployment. Let's start..."
        )
        console.print("")

    def questions(self):
        os.system("clear")
        self.header()
        portlist: List[int] = []

        console.print("[bold orange1]NEW NETWORK[/]")
        console.print("")
        console.print("[bold red]Press 'Q' to quit anytime[/]")
        console.print("")

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
        cadomain.name = "ca_orderer"
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

                peer.CORE_PEER_LISTENADDRESS = "0.0.0.0:" + str(valueport)
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
                ]

                org.peers.append(peer)

                portlist.append(valueport)

                ipeers += 1
                portpeer += 1000

            self.domain.organizations.append(org)

            iorgs += 1
            portpeer += 1000
            caorgserverport += 100
            caorgoplstport += 100
            console.print("")

        build = Build(self.domain)
        build.buildAll()
        # self.selectNetwork()

    def mainMenu(self):
        os.system("clear")
        self.header()
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

    def checkDockerStatus(self):
        os.system("clear")
        self.header()
        console.print("[bold orange1]DOCKER STATUS[/]")
        console.print("")
        console.print("[bold]Containers[/]")
        console.print("")
        os.system("docker ps")
        console.print("")
        console.print("[bold]Volumes[/]")
        console.print("")
        os.system("docker volume ls")
        console.print("")
        console.print("[bold]Networks[/]")
        console.print("")
        os.system("docker network ls")
        console.print("")
        console.print("[bold white]M - Return to main menu[/]")
        console.print("[bold white]Q - Quit[/]")
        console.print("")
        option = console.input("[bold]Select an option (M or Q):[/] ")
        console.print("")

        selectoption = True
        while selectoption:
            match option.lower():
                case "m":
                    selectoption = False
                    self.mainMenu()
                case "q":
                    selectoption = False
                    exit(0)
                case _:
                    option = console.input("[bold]Select an option (M or Q):[/] ")
                    console.print("")

    def cleanDockerAll(self):
        os.system("clear")
        self.header()
        console.print("[bold orange1]DOCKER CLEANING[/]")
        console.print("")
        console.print("[bold green]Removing all Docker resources[/]")
        console.print("[bold]# Stopping containers[/]")
        os.system("docker stop $(docker ps -a -q)")
        console.print("[bold]# Removing containers and volumes[/]")
        os.system("docker rm -v $(docker ps -a -q)")
        console.print("[bold]# Removing inmages[/]")
        os.system("docker rmi $(docker images -a -q)")
        console.print("[bold]# Removing other resources[/]")
        os.system("docker system prune -a -f")
        console.print("")
        self.mainMenu()

    def selectNetwork(self):
        os.system("clear")
        self.header()
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

    def networkSelected(self, network: str):
        os.system("clear")
        self.header()
        console.print("[bold orange1]NETWORK " + network + "[/]")
        console.print("")
        console.print("[bold white]N - Network status[/]")
        console.print("[bold white]O - Add organization[/]")
        console.print("[bold white]P - Add peer[/]")
        console.print("[bold white]C - Add chaincode[/]")
        console.print("[bold white]G - Start network[/]")
        console.print("[bold white]S - Stop network[/]")
        console.print("[bold white]D - Clean docker[/]")
        console.print("[bold white]R - Return to previous menu[/]")
        console.print("[bold white]M - Return to main menu[/]")
        console.print("[bold white]Q - Quit[/]")
        console.print("")
        option = console.input("[bold]Select an option (N,O,P,C,G,S,D,R,M or Q):[/] ")
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

        selectoption = True
        while selectoption:
            match option.lower():
                case "n":
                    selectoption = False
                case "o":
                    selectoption = False
                case "p":
                    selectoption = False
                case "c":
                    selectoption = False
                case "g":
                    selectoption = False
                    run = Run(domain)
                    run.runAll()
                    self.checkDockerStatus()
                case "s":
                    selectoption = False
                    # self.selectNetwork()
                case "d":
                    selectoption = False
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
                        "[bold]Select an option (N,O,P,C,G,S,D,R,M or Q):[/] "
                    )
                    console.print("")
