from controllers.build import Build
from controllers.console import ConsoleOutput
from controllers.requirements import Requirements
from controllers.run import Run
from models.domain import Domain

network = Domain()
requirements = Requirements()
consoleOutput = ConsoleOutput(network)

consoleOutput.header()
requirements.checkAll()
consoleOutput.questions()

build = Build(network)
build.buildAll()

run = Run(network)
run.runAll()
