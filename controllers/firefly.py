from rich.console import Console

from models.domain import Domain

console = Console()


class Firefly:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain

    def buildAll(self):
        console.print("[bold orange1]FIREFLY[/]")
        console.print("")
        if self.checkInstall():
            self.startStack()
        else:
            self.buildConnectionProfiles()
            self.deployFFChaincode()
            self.createStack()
            self.startStack()

    def checkInstall(self) -> bool:
        console.print("[bold white]# Checking Firefly install[/]")
        return True

    def buildConnectionProfiles(self):
        console.print("[bold white]# Preparing connection profiles[/]")

    def deployFFChaincode(self):
        console.print("[bold white]# Deploy Firefly chaincode[/]")

    def createStack(self):
        console.print("[bold white]# Creating Firefly stack[/]")

    def startStack(self):
        console.print("[bold white]# Starting Firefly stack[/]")
