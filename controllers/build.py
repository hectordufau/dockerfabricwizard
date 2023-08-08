import json
import os

from models.domain import Domain


class Build:
    def __init__(self, domain: Domain) -> None:
        self.domain = domain

    def buildNetwork(self):
        pathdomains = "domains/" + self.domain.name
        isFolderDomainsExist = os.path.exists(pathdomains)

        if not isFolderDomainsExist:
            os.mkdir(pathdomains)

        json_object = json.dumps(self.domain, default=lambda x: x.__dict__, indent=4)
        with open(pathdomains + "/setup.json", "w") as outfile:
            outfile.write(json_object)
