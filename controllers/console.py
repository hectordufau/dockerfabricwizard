from rich.console import Console

console = Console()


class ConsoleOutput:
    def __init__(self) -> None:
        pass

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
            "First, you need answer some questions to build your HLF Network. Let's start...."
        )
        console.print("")

    def questions(self):
        console.print("")
        domainname = console.input("[bold red]Domain name:[/] ")
        console.print(domainname)
