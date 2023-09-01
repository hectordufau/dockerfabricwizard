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

    def checkAll(self):
        console.print("[bold green]Checking Requirements[/]")
        self.checkCurl()
        self.checkJq()
        self.checkDocker()
        self.checkHLFBinaries()
        self.checkFireflyBinary()
        self.checkFireflyChaincode()
        self.checkDomainFolder()

    def checkCurl(self):
        console.print("[bold white]# Checking cURL[/]")
        rc = subprocess.call(
            ["which", "curl"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if rc != 0:
            console.print("[bold red]> cURL isn't installed. Please install it.[/]")
            exit(0)

    def checkJq(self):
        console.print("[bold white]# Checking jq[/]")
        rc = subprocess.call(
            ["which", "jq"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if rc != 0:
            console.print("[bold red]> jq isn't installed. Please install it.[/]")
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

    def checkFireflyBinary(self):
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

    def checkFireflyChaincode(self):
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
        shutil.rmtree(fireflysource+".git")

    def checkDomainFolder(self):
        pathdomains = "domains"
        isFolderDomainsExist = os.path.exists(pathdomains)

        if not isFolderDomainsExist:
            os.mkdir(pathdomains)

        console.print("[bold green]All requirements gathered.[/]")
        console.print("")
