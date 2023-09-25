import os
import time
from pathlib import Path

from python_on_whales import DockerClient
from rich.console import Console

from controllers.header import Header
from models.domain import Domain
from models.organization import Organization
from models.peer import Peer

console = Console()
header = Header()


class Run:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def run_all(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]RUN[/]")
        console.print("")
        console.print("[bold green]Starting network[/]")
        console.print("[bold white]# Starting CAs[/]")
        self.start_ca()
        console.print("")
        console.print("[bold white]# Starting orderer, peers and databases[/]")
        self.starting_opd()
        console.print("")

    def start_ca(self):
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
        time.sleep(2)

    def start_ca_new(self, orgname: str):
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
        time.sleep(2)

        os.remove(Path(pathfabricca))

    def starting_opd(self):
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
        time.sleep(2)

    def starting_pd_org(self, org: Organization):
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
        time.sleep(2)

        os.remove(Path(pathnet))

    def starting_pd(self, peer: Peer):
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
        time.sleep(1)

        os.remove(Path(pathnet))

    def check_container(self) -> bool:
        pathorderer = "".join(
            [
                str(Path().absolute()),
                "/domains/",
                self.domain.name,
                "/compose/",
                "compose-orderer.yaml",
            ]
        )

        docker = DockerClient(compose_files=[pathorderer])
        return docker.container.exists(self.domain.orderer.name)
