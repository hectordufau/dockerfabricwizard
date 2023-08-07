import os
import subprocess

import docker
from rich.console import Console

console = Console()


class Requirements:
    def __init__(self) -> None:
        console.print("[bold green]Checking Requirements[/]")

    def checkCurl(self):
        console.print("[bold white]# Checking cURL[/]")
        rc = subprocess.call(
            ["which", "curl"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if rc != 0:
            console.print("[bold red]> cURL isn't installed. Please install it.[/]")
            exit(0)

    def checkDocker(self):
        console.print("[bold white]# Checking Docker[/]")
        try:
            client = docker.DockerClient(base_url="unix://var/run/docker.sock")
            client.ping()
        except:
            console.print(
                "[bold red]> Docker isn't installed or running. Please install and run it.[/]"
            )
            exit(0)

    def checkHLFBinaries(self):
        console.print("[bold white]# Checking if HLF binaries are installed[/]")

        pathbin = "bin"
        isFolderBinExist = os.path.exists(pathbin)

        pathbuilder = "builder"
        isFolderBuilderExist = os.path.exists(pathbuilder)

        if (not isFolderBinExist) and (not isFolderBuilderExist):
            console.print(
                "[bold yellow]> Please wait for HLF binaries downloading and installing.[/]"
            )

            os.system(
                "curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh"
            )
            os.system("./install-fabric.sh binary")

        console.print("[bold green]All requirements gathered...starting questions.[/]")
        console.print("")
