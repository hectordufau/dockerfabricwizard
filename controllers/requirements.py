import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import docker
from git import Repo
from python_on_whales import DockerClient
from rich.console import Console

whales = DockerClient()

console = Console()


class Requirements:
    def __init__(self) -> None:
        pass

    def check_all(self):
        console.print("[bold green]Checking Requirements[/]")
        self.check_curl()
        self.check_jq()
        self.check_docker()
        self.check_hlf_binaries()
        self.check_firefly_cli()
        self.check_firefly()
        self.check_domain_folder()

    def check_curl(self):
        console.print("[bold white]# Checking cURL[/]")
        rc = subprocess.call(
            ["which", "curl"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if rc != 0:
            console.print("[bold red]> cURL isn't installed. Please install it.[/]")
            exit(0)

    def check_jq(self):
        console.print("[bold white]# Checking jq[/]")
        rc = subprocess.call(
            ["which", "jq"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if rc != 0:
            console.print("[bold red]> jq isn't installed. Please install it.[/]")
            exit(0)

    def check_docker(self):
        console.print("[bold white]# Checking Docker[/]")
        try:
            client = docker.DockerClient(base_url="unix://var/run/docker.sock")
            client.ping()
        except:
            console.print(
                "[bold red]> Docker isn't installed or running. Please install and run it.[/]"
            )
            exit(0)

    def check_hlf_binaries(self):
        console.print("[bold white]# Checking HLF binaries[/]")

        pathbin = "bin"
        isFolderBinExist = os.path.exists(pathbin)

        pathbuilder = "builders"
        isFolderBuilderExist = os.path.exists(pathbuilder)

        pathconfig = "config"
        isFolderConfigExist = os.path.exists(pathconfig)

        if (
            (isFolderBinExist == False)
            or (isFolderBuilderExist == False)
            or (isFolderConfigExist == False)
        ):
            console.print(
                "[bold yellow]> Please wait for HLF binaries downloading and installing.[/]"
            )

            os.system(
                "curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh"
            )
            os.system("./install-fabric.sh binary")

    def check_firefly(self):
        console.print("[bold white]# Checking FireFly chaincode source[/]")
        fireflysource = str(Path().absolute()) + "/fireflysources/firefly/"
        fireflyccgo = str(Path().absolute()) + "/chaincodes/firefly-go"
        fireflychaincode = str(Path().absolute()) + "/chaincodes/firefly/"
        isFireflyExist = os.path.exists(Path(fireflysource))
        if not isFireflyExist:
            console.print(
                "[bold yellow]> Please wait for FireFly chaincode source downloading and installing.[/]"
            )

            Repo.clone_from("https://github.com/hyperledger/firefly", fireflysource)
            shutil.copytree(
                fireflysource + "smart_contracts/fabric/firefly-go",
                fireflyccgo,
            )
            os.rename(
                fireflyccgo,
                fireflychaincode,
            )
        else:
            repo = Repo(path=fireflysource)
            pull = repo.remotes.origin.pull("main")
            if pull[0].flags != 0:
                console.print(
                    "[bold yellow]> Please wait for FireFly chaincode source updating.[/]"
                )
                shutil.copytree(
                    fireflysource + "smart_contracts/fabric/firefly-go",
                    fireflyccgo,
                )
                shutil.rmtree(str(Path().absolute()) + "/chaincodes/firefly")
                os.rename(
                    fireflyccgo,
                    fireflychaincode,
                )

    def check_firefly_cli(self):
        console.print("[bold white]# Checking FireFly CLI source[/]")
        fireflysource = str(Path().absolute()) + "/fireflysources/firefly-cli/"
        fireflybin = str(Path().absolute()) + "/bin/"
        isFireflyExist = os.path.exists(Path(fireflysource))
        if not isFireflyExist:
            console.print(
                "[bold yellow]> Please wait for FireFly CLI source downloading and installing.[/]"
            )

            Repo.clone_from("https://github.com/hyperledger/firefly-cli", fireflysource)
            whales.run(
                image="golang:1.18",
                volumes=[(fireflysource, "/usr/src/myapp")],
                workdir="/usr/src/myapp",
                command=["make"],
                remove=True,
            )
            shutil.copy(fireflysource + "ff/ff", fireflybin)

        else:
            repo = Repo(path=fireflysource)
            pull = repo.remotes.origin.pull("main")
            if pull[0].flags != 0:
                console.print(
                    "[bold yellow]> Please wait for FireFly CLI source updating.[/]"
                )
                whales.run(
                    image="golang:1.18",
                    volumes=[(fireflysource, "/usr/src/myapp")],
                    workdir="/usr/src/myapp",
                    command="make",
                    remove=True,
                )
                os.remove(fireflybin + "/ff")
                shutil.copy(fireflysource + "ff/ff", fireflybin)

    def check_domain_folder(self):
        pathdomains = "domains"
        isFolderDomainsExist = os.path.exists(pathdomains)

        if not isFolderDomainsExist:
            os.mkdir(pathdomains)

        console.print("[bold green]All requirements gathered.[/]")
        console.print("")
