from controllers.console import ConsoleOutput
from controllers.requirements import Requirements

requirements = Requirements()
consoleOutput = ConsoleOutput()

consoleOutput.header()
requirements.checkAll()
# consoleOutput.questions()
