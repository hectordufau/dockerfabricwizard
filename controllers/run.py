import os
import time
from pathlib import Path

from python_on_whales import DockerClient
from rich.console import Console

from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

console = Console()


class Run:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def runAll(self):
        console.print("[bold orange1]RUN[/]")
        console.print("")
        console.print("[bold green]Starting network[/]")
        console.print("[bold white]# Starting CAs[/]")
        self.startCA()
        console.print("")
        console.print("[bold white]# Starting orderer, peers and databases[/]")
        self.startingOPD()
        console.print("")

    def startCA(self):
        pathfabricca = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-ca.yaml",
            ]
        )

        docker = DockerClient(compose_files=[pathfabricca])
        docker.compose.up(detach=True)
        console.print("[bold]# Waiting CAs...[/]")
        time.sleep(5)

    def startCANew(self, orgname: str):
        pathfabricca = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-ca-" + orgname + ".yaml",
            ]
        )

        docker = DockerClient(compose_files=[pathfabricca])
        docker.compose.up(detach=True)
        console.print("[bold]# Waiting new CA...[/]")
        time.sleep(5)

        os.remove(Path(pathfabricca))

    def startingOPD(self):
        pathorderer = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-orderer.yaml",
            ]
        )

        pathnet = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-net.yaml",
            ]
        )

        docker = DockerClient(compose_files=[pathorderer, pathnet])
        docker.compose.up(detach=True)

        console.print("")
        console.print("## Waiting Network...")
        console.print("")
        time.sleep(5)

    def startingPDOrg(self, org: Organization):
        pathnet = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-net-" + org.name + ".yaml",
            ]
        )

        docker = DockerClient(compose_files=[pathnet])
        docker.compose.up(detach=True)

        console.print("")
        console.print("## Waiting Organization...")
        console.print("")
        time.sleep(5)

        os.remove(Path(pathnet))

    def startingPD(self, peer: Peer):
        pathnet = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-net-" + peer.name + ".yaml",
            ]
        )

        docker = DockerClient(compose_files=[pathnet])
        docker.compose.up(detach=True)

        console.print("")
        console.print("## Waiting Peer...")
        console.print("")
        time.sleep(5)

        os.remove(Path(pathnet))
