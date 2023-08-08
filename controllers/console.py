import validators
from rich.console import Console

from models.ca import Ca
from models.domain import Domain
from models.orderer import Orderer
from models.organization import Organization
from models.peer import Peer

console = Console()


class ConsoleOutput:
    def __init__(self, domain: Domain) -> None:
        self.domain = domain

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
            "You will guided during all Hyperledger Fabric deployment starting now."
        )
        console.print(
            "First, you need answer some questions to build your HLF Network. Let's start..."
        )
        console.print("")

    def questions(self):
        console.print("[bold orange1]QUESTIONS[/]")
        console.print("")

        domainname = console.input("[bold]Domain name:[/] ")
        while not validators.domain(domainname):
            domainname = console.input(
                "[bold red]Domain name not valid. Please retype again:[/] "
            )
        self.domain.name = domainname
        self.domain.networkname = domainname.split(".")[0]

        ordererdomain = Orderer()
        ordererdomain.name = "orderer"
        self.domain.orderer = ordererdomain

        cadomain = Ca()
        cadomain.name = "ca_orderer"
        cadomain.FABRIC_CA_SERVER_CA_NAME = cadomain.name
        self.domain.ca = cadomain

        qtyorgs = console.input("[bold]Number of Organizations:[/] ")
        value = 0
        while not qtyorgs.isdigit():
            qtyorgs = console.input(
                "[bold red]Number of Organizations value not valid. Please retype again:[/] "
            )
        value = int(qtyorgs)

        while not validators.between(value, min=1):
            qtyorgs = console.input(
                "[bold red]Number of Organizations value not valid, min 1. Please retype again:[/] "
            )
            while not qtyorgs.isdigit():
                value = 0
            value = int(qtyorgs)

        self.domain.qtyorgs = value

        console.print("")
        iorgs = 1
        while iorgs <= self.domain.qtyorgs:
            org = Organization()
            orgname = console.input("[bold]Organization #" + str(iorgs) + " name:[/] ")
            while not orgname.isalpha():
                orgname = console.input(
                    "[bold red]Organization #"
                    + str(iorgs)
                    + " name not valid. Please retype again:[/] "
                )
            org.name = orgname

            caorg = Ca()
            caorg.name = "ca." + org.name
            caorg.FABRIC_CA_SERVER_CA_NAME = caorg.name

            org.ca = caorg

            qtypeers = console.input("[bold]Number of Peers:[/] ")
            valuepeers = 0
            while not qtypeers.isdigit():
                qtypeers = console.input(
                    "[bold red]Number of Peers value not valid. Please retype again:[/] "
                )
            valuepeers = int(qtypeers)

            while not validators.between(valuepeers, min=1):
                qtypeers = console.input(
                    "[bold red]Number of Peers value not valid, min 1. Please retype again:[/] "
                )
                while not qtypeers.isdigit():
                    valuepeers = 0
                valuepeers = int(qtypeers)

            org.qtypeers = valuepeers

            ipeers = 1
            portpeer = 7051
            while ipeers <= org.qtypeers:
                peer = Peer()
                peer.name = "peer" + str(ipeers) + "." + org.name
                peerport = console.input(
                    "[bold]Peer "
                    + peer.name
                    + " Port Number [ex. "
                    + str(portpeer)
                    + "]:[/] "
                )
                valueport = 0
                while not peerport.isdigit():
                    qtyorgs = console.input(
                        "[bold red]Peer "
                        + peer.name
                        + " Port Number value not valid. Please retype again:[/] "
                    )
                valueport = int(peerport)

                while not validators.between(valueport, min=portpeer, max=65535):
                    peerport = console.input(
                        "[bold red]Peer "
                        + peer.name
                        + " Port Number value not valid, min "
                        + str(portpeer)
                        + ". Please retype again:[/] "
                    )
                    while not peerport.isdigit():
                        valueport = 0
                    valueport = int(peerport)

                peer.CORE_PEER_LISTENADDRESS = "0.0.0.0:" + str(valueport)

                org.peers.append(peer)

                ipeers += 1
                portpeer += 1000

            self.domain.organizations.append(org)

            iorgs += 1
