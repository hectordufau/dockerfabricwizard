from controllers.build import Build
from controllers.console import ConsoleOutput
from controllers.run import Run
from models.domain import Domain

network = Domain()

consoleOutput = ConsoleOutput(network)
consoleOutput.header()

# consoleOutput.questions()

# build = Build(network)
# build.buildAll()

# run = Run(network)
# run.runAll()
