import time
from pathlib import Path

from python_on_whales import DockerClient
from rich.console import Console

from models.domain import Domain

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
        # docker.compose.up()
        console.print("[bold]# Waiting CAs...[/]")
        time.sleep(5)

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
        # docker.compose.up()
