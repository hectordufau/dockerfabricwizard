import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import docker
from git import Repo
from rich.console import Console

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
        self.check_firefly_binary()
        self.check_firefly_chaincode()
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

    def check_firefly_binary(self):
        console.print("[bold white]# Checking Firefly binary[/]")
        fireflyfile = str(Path().absolute()) + "/bin/ff"
        isFireflyExist = os.path.exists(Path(fireflyfile))
        if not isFireflyExist:
            console.print(
                "[bold yellow]> Please wait for Firefly downloading and installing.[/]"
            )
            old_dir = os.getcwd()
            os.chdir(Path(str(Path().absolute()) + "/bin"))
            os.system(
                'curl -s https://api.github.com/repos/hyperledger/firefly-cli/releases/latest | grep -wo "https.*$(uname)_x86_64.*gz" | wget -qi -'
            )
            for file in os.listdir(Path().absolute()):
                if file.endswith(".tar.gz"):
                    with tarfile.open(
                        str(Path().absolute()) + "/" + file, "r:gz"
                    ) as tar:
                        tar.extract("ff")
                    os.remove(str(Path().absolute()) + "/" + file)
            os.chdir(old_dir)

    def check_firefly_chaincode(self):
        console.print("[bold white]# Checking Firefly chaincode source[/]")
        fireflysource = str(Path().absolute()) + "/firefly/"
        isFireflyExist = os.path.exists(Path(fireflysource))
        if not isFireflyExist:
            console.print(
                "[bold yellow]> Please wait for Firefly chaincode source downloading and installing.[/]"
            )

            Repo.clone_from("https://github.com/hyperledger/firefly", fireflysource)
            shutil.move(
                fireflysource + "smart_contracts/fabric/firefly-go",
                str(Path().absolute()) + "/chaincodes/",
            )
            os.rename(
                str(Path().absolute()) + "/chaincodes/firefly-go",
                str(Path().absolute()) + "/chaincodes/firefly",
            )
            shutil.rmtree(fireflysource + ".git")
            shutil.rmtree(fireflysource + ".githooks")
            shutil.rmtree(fireflysource + ".github")
            shutil.rmtree(fireflysource + ".vscode")

    def check_domain_folder(self):
        pathdomains = "domains"
        isFolderDomainsExist = os.path.exists(pathdomains)

        if not isFolderDomainsExist:
            os.mkdir(pathdomains)

        console.print("[bold green]All requirements gathered.[/]")
        console.print("")
