from controllers.console import ConsoleOutput
from controllers.requirements import Requirements

consoleOutput = ConsoleOutput()

consoleOutput.header()

requirements = Requirements()
requirements.checkCurl()
requirements.checkDocker()
requirements.checkHLFBinaries()

#consoleOutput.questions()
