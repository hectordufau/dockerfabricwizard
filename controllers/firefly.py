import json
import os
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path

import docker
import requests
import ruamel.yaml
from python_on_whales import DockerClient
from rich.console import Console

from controllers.chaincode import ChaincodeDeploy
from controllers.header import Header
from helpers.paths import Paths
from models.chaincode import Chaincode
from models.domain import Domain

whales = DockerClient()
client = docker.from_env()

console = Console()
yaml = ruamel.yaml.YAML()
yaml.indent(sequence=3, offset=1)
yaml.boolean_representation = [f"false", f"true"]
header = Header()


class Firefly:
    def __init__(self, domain: Domain) -> None:
        self.domain: Domain = domain
        self.paths: Paths = Paths(domain)
        self.ffchaincode: Chaincode = None

    def build_all(self):
        os.system("clear")
        header.header()
        console.print("[bold orange1]FIREFLY[/]")
        console.print("")
        if self.check_install():
            self.start_stack()
        else:
            self.build_connection_profiles()
            self.deploy_firefly_chaincode()
            self.create_stack()
            self.start_stack()

    def check_install(self) -> bool:
        console.print("[bold white]# Checking Firefly install[/]")
        return os.path.isdir(self.paths.FIREFLYFABCONNECTPATH)

    def remove(self):
        console.print("[bold white]# Stoping Firefly stack[/]")
        """ os.environ["FIREFLY_HOME"] = self.paths.FIREFLYPATH
        os.system(self.paths.APPPATH + "bin/ff stop " + self.domain.networkname)
        os.system(self.paths.APPPATH + "bin/ff remove -f " + self.domain.networkname) """

    def build_connection_profiles(self):
        console.print("[bold white]# Preparing connection profiles[/]")

        # create firefly/fabconnect folder
        pathfabconnect = Path(self.paths.FIREFLYFABCONNECTPATH)
        pathfabconnect.mkdir(parents=True, exist_ok=True)

        orgclient = self.domain.organizations[0]
        # peerclient = orgclient.peers[0]

        ccp = {
            "version": "1.1.0%",
            "channels": {
                self.domain.networkname: {
                    "orderers": [self.domain.orderer.name + "." + self.domain.name],
                    "peers": {},
                }
            },
            "organizations": {},
            "orderers": {
                self.domain.orderer.name
                + "."
                + self.domain.name: {
                    "url": "grpcs://"
                    + self.domain.orderer.name
                    + "."
                    + self.domain.name
                    + ":"
                    + str(self.domain.orderer.generallistenport),
                    "grpcOptions": {
                        "ssl-target-name-override": self.domain.orderer.name
                        + "."
                        + self.domain.name,
                        "grpc-max-send-message-length": 4194304,
                    },
                    "tlsCACerts": {
                        "path": "/etc/firefly/organizations/"
                        + orgclient.name
                        + "/orderer/tls/tlscacerts/tls-cert.pem"
                    },
                }
            },
            "client": {
                "organization": orgclient.name + "." + self.domain.name,
                "BCCSP": {
                    "security": {
                        "default": {"provider": "SW"},
                        "enabled": True,
                        "hashAlgorithm": "SHA2",
                        "level": 256,
                        "softVerify": True,
                    }
                },
                "credentialStore": {
                    "path": "/etc/firefly/organizations/"
                    + orgclient.name
                    + "/user/admin/msp",
                    "cryptoStore": {
                        "path": "/etc/firefly/organizations/"
                        + orgclient.name
                        + "/user/admin/msp"
                    },
                },
                "logging": {"level": "debug"},
                "tlsCerts": {
                    "client": {
                        "cert": {
                            "path": "/etc/firefly/organizations/"
                            + orgclient.name
                            + "/user/admin/tls/signcerts/cert.pem"
                        },
                        "key": {
                            "path": "/etc/firefly/organizations/"
                            + orgclient.name
                            + "/user/admin/tls/keystore/key.pem"
                        },
                    }
                },
            },
            "peers": {},
            "certificateAuthorities": {},
        }

        for org in self.domain.organizations:
            self.paths.set_org_paths(org)

            ccp["certificateAuthorities"][org.name + "." + self.domain.name] = {
                "url": "https://"
                + org.ca.name
                + "."
                + self.domain.name
                + ":"
                + str(org.ca.serverport),
                "httpOptions": {"verify": False},
                "tlsCACerts": {
                    "path": "/etc/firefly/organizations/"
                    + org.name
                    + "/tlscacerts/tls-cert.pem"
                },
                "registrar": {"enrollId": "admin", "enrollSecret": "adminpw"},
                "caName": org.ca.name + "." + self.domain.name,
            }

            ccp["organizations"][org.name + "." + self.domain.name] = {
                "mspid": org.name + "MSP",
                "peers": [],
                "certificateAuthorities": [org.name + "." + self.domain.name],
                "adminPrivateKey": {
                    "path": "/etc/firefly/organizations/"
                    + org.name
                    + "/user/admin/msp/keystore/key.pem"
                },
                "signedCert": {
                    "path": "/etc/firefly/organizations/"
                    + org.name
                    + "/user/admin/msp/signcerts/cert.pem"
                },
                "cryptoPath": "/etc/firefly/organizations/" + org.name,
            }

            for peer in org.peers:
                self.paths.set_peer_paths(org, peer)

                ccp["channels"][self.domain.networkname]["peers"][
                    peer.name + "." + self.domain.name
                ] = {
                    "chaincodeQuery": True,
                    "endorsingPeer": True,
                    "eventSource": True,
                    "ledgerQuery": True,
                }

                ccp["organizations"][org.name + "." + self.domain.name]["peers"].append(
                    peer.name + "." + self.domain.name
                )

                ccp["peers"][peer.name + "." + self.domain.name] = {
                    "url": "grpcs://"
                    + peer.name
                    + "."
                    + self.domain.name
                    + ":"
                    + str(peer.peerlistenport),
                    "grpcOptions": {
                        "ssl-target-name-override": peer.name + "." + self.domain.name,
                    },
                    "tlsCACerts": {
                        "path": "/etc/firefly/organizations/"
                        + org.name
                        + "/"
                        + peer.name
                        + "/tls/tlscacerts/tls-cert.pem"
                    },
                }

            with open(
                self.paths.FIREFLYFABCONNECTPATH + "ccp.yaml", "w", encoding="utf-8"
            ) as yaml_file:
                yaml.dump(ccp, yaml_file)

    def deploy_firefly_chaincode(self):
        console.print("[bold white]# Deploy Firefly chaincode[/]")
        chaincode = Chaincode()
        chaincode.name = "firefly"
        chaincode.ccport = 9999
        chaincode.invoke = False
        chaincode.usetls = True
        chaincodedeploy = ChaincodeDeploy(self.domain, chaincode)
        self.ffchaincode = chaincodedeploy.build_firefly()

    def create_stack(self):
        console.print("[bold white]# Creating Firefly stack[/]")
        self.build_fabconnect()
        self.build_sharedstorage()
        self.build_dataexchange()
        self.build_database()
        self.build_firefly_core()

    def start_stack(self):
        console.print("[bold white]# Starting Firefly stack[/]")
        console.print("")

        fabconnect = self.paths.COMPOSEPATH + "compose-fabconnect.yaml"
        dataexchange = self.paths.COMPOSEPATH + "compose-dataexchange.yaml"
        sharedstorage = self.paths.COMPOSEPATH + "compose-sharedstorage.yaml"
        database = self.paths.COMPOSEPATH + "compose-database.yaml"
        fireflycore = self.paths.COMPOSEPATH + "compose-fireflycore.yaml"

        whales = DockerClient(
            compose_files=[fabconnect, dataexchange, sharedstorage, database]
        )
        whales.compose.up(detach=True)
        time.sleep(5)

        orgclient = self.domain.organizations[0]

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        # registering Org
        json_data = {
            "name": orgclient.name,
            "type": "client",
            "maxEnrollments": -1,
            "attributes": {},
        }

        response = requests.post(
            "http://localhost:5102/identities",
            headers=headers,
            json=json_data,
            timeout=None,
        )

        registerdata = response.json()

        # enrolling Org
        json_data = {
            "secret": registerdata["secret"],
            "attributes": {},
        }

        requests.post(
            "http://localhost:5102/identities/" + orgclient.name + "/enroll",
            headers=headers,
            json=json_data,
            timeout=None,
        )

        console.print("# Waiting Database load data....")
        console.print("")
        command = "sh -c 'for file in /migrations/*;do psql -U firefly -d firefly -f $file;done;'"
        clidocker = client.containers.get("database." + self.domain.name)
        clidocker.exec_run(command)
        time.sleep(5)

        console.print("# Enabling Database SSL....")
        command = "chmod 600 /var/lib/postgresql/server.key"
        clidocker.exec_run(command)
        command = "chown postgres:postgres /var/lib/postgresql/server.key"
        clidocker.exec_run(command)
        command = "psql -U firefly -d firefly -f /var/lib/postgresql/sslenable.sql"
        clidocker.exec_run(command)
        time.sleep(1)

        console.print("# Waiting Firefly start...")
        console.print("")
        whales = DockerClient(compose_files=[fireflycore])
        whales.compose.up(detach=True)
        time.sleep(5)

        params = {
            "confirm": "true",
        }

        json_data = {
            "additionalProp1": "string",
            "additionalProp2": "string",
            "additionalProp3": "string",
        }

        # registering org
        requests.post(
            "http://127.0.0.1:5000/api/v1/namespaces/default/network/organizations/self",
            params=params,
            headers=headers,
            json=json_data,
            timeout=None,
        )

        # registering node
        requests.post(
            "http://127.0.0.1:5000/api/v1/namespaces/default/network/nodes/self",
            params=params,
            headers=headers,
            json=json_data,
            timeout=None,
        )

        webbrowser.open("http://127.0.0.1:5000/ui", 1)
        webbrowser.open("http://127.0.0.1:5000/api", 1)

    def build_fabconnect(self):
        console.print("[bold]## Bulding Fabconnect[/]")

        orgmsp = Path(self.paths.FIREFLYFABCONNECTPATH + "msp/")
        orgmsp.mkdir(parents=True, exist_ok=True)

        # copy org msps to msp
        for org in self.domain.organizations:
            self.paths.set_org_paths(org)

            shutil.copytree(
                self.paths.MSPORGPATH,
                self.paths.FIREFLYFABCONNECTPATH + "msp/" + org.name,
            )
        # save fabconnect.yaml
        fabconnectcfg = {
            "maxInFlight": 10,
            "maxTXWaitTime": 60,
            "sendConcurrency": 25,
            "receipts": {
                "maxDocs": 1000,
                "queryLimit": 100,
                "retryInitialDelay": 5,
                "retryTimeout": 30,
                "leveldb": {"path": "/fabconnect/receipts"},
            },
            "events": {
                "webhooksAllowPrivateIPs": True,
                "leveldb": {"path": "/fabconnect/events"},
            },
            "http": {"port": 3000},
            "rpc": {"useGatewayClient": True, "configPath": "/fabconnect/ccp.yaml"},
        }

        with open(
            self.paths.FIREFLYFABCONNECTPATH + "fabconnect.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(fabconnectcfg, yaml_file)

        # save compose-fabconnect.yaml
        fabconnectservice = {
            "version": "3.7",
            "networks": {
                self.domain.networkname: {
                    "name": self.domain.networkname,
                    "external": True,
                }
            },
            "services": {
                "fabconnect."
                + self.domain.name: {
                    "container_name": "fabconnect." + self.domain.name,
                    "image": "ghcr.io/hyperledger/firefly-fabconnect",
                    # "user": str(os.geteuid()) + ":" + str(os.getgid()),
                    "command": "-f /fabconnect/fabconnect.yaml",
                    "volumes": [
                        "fabconnect_receipts:/fabconnect/receipts",
                        "fabconnect_events:/fabconnect/events",
                        self.paths.FIREFLYFABCONNECTPATH
                        + "fabconnect.yaml:/fabconnect/fabconnect.yaml",
                        self.paths.FIREFLYFABCONNECTPATH
                        + "msp/"
                        + ":/etc/firefly/organizations",
                        self.paths.FIREFLYFABCONNECTPATH
                        + "ccp.yaml:/fabconnect/ccp.yaml",
                    ],
                    "ports": ["5102:3000"],
                    "healthcheck": {
                        "test": [
                            "CMD",
                            "wget",
                            "-O",
                            "-",
                            "http://localhost:3000/status",
                        ]
                    },
                    "logging": {
                        "driver": "json-file",
                        "options": {"max-file": "1", "max-size": "10m"},
                    },
                    "networks": [self.domain.networkname],
                }
            },
            "volumes": {"fabconnect_events": {}, "fabconnect_receipts": {}},
        }

        with open(
            self.paths.COMPOSEPATH + "compose-fabconnect.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(fabconnectservice, yaml_file)

    def build_sharedstorage(self):
        console.print("[bold]## Bulding Sharedstorage[/]")

        sharedstorage = {
            "version": "3.7",
            "networks": {
                self.domain.networkname: {
                    "name": self.domain.networkname,
                    "external": True,
                }
            },
            "services": {
                "sharedstorage."
                + self.domain.name: {
                    "container_name": "sharedstorage." + self.domain.name,
                    "image": "ipfs/go-ipfs:v0.10.0",
                    "environment": {
                        "IPFS_SWARM_KEY": "/key/swarm/psk/1.0.0/\n/base16/\n5a378bd04ac0bece92ed9b7f02abbfaa78f7b2c1cfcc86ff8a25f72626ee7aba",
                        "LIBP2P_FORCE_PNET": "1",
                    },
                    "volumes": ["ipfs_staging:/export", "ipfs_data:/data/ipfs"],
                    "ports": ["10206:5001", "10207:8080"],
                    "healthcheck": {
                        "test": [
                            "CMD-SHELL",
                            "wget --post-data= http://127.0.0.1:5001/api/v0/id -O - -q",
                        ],
                        "interval": "5s",
                        "timeout": "3s",
                        "retries": 12,
                    },
                    "logging": {
                        "driver": "json-file",
                        "options": {"max-file": "1", "max-size": "10m"},
                    },
                    "networks": [self.domain.networkname],
                },
            },
            "volumes": {
                "ipfs_data": {},
                "ipfs_staging": {},
            },
        }

        with open(
            self.paths.COMPOSEPATH + "compose-sharedstorage.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(sharedstorage, yaml_file)

    def build_dataexchange(self):
        console.print("[bold]## Bulding Dataexchange[/]")

        dataexch = Path(self.paths.FIREFLYDATAEXCHPATH + "peer-certs")
        dataexch.mkdir(parents=True, exist_ok=True)

        decfg = {
            "api": {"hostname": "0.0.0.0", "port": 3000},
            "p2p": {
                "hostname": "0.0.0.0",
                "endpoint": "https://dataexchange." + self.domain.name + ":3001",
                "port": 3001,
            },
            "peers": [{"id": "org", "endpoint": "https://localhost:4001"}],
        }

        json_object = json.dumps(decfg, indent=4)
        with open(
            self.paths.FIREFLYDATAEXCHPATH + "config.json", "w", encoding="utf-8"
        ) as outfile:
            outfile.write(json_object)

        dataexchange = {
            "version": "3.7",
            "networks": {
                self.domain.networkname: {
                    "name": self.domain.networkname,
                    "external": True,
                }
            },
            "services": {
                "dataexchange."
                + self.domain.name: {
                    "container_name": "dataexchange." + self.domain.name,
                    "image": "ghcr.io/hyperledger/firefly-dataexchange-https",
                    "volumes": [self.paths.FIREFLYDATAEXCHPATH + ":/data"],
                    "ports": ["10205:3000"],
                    "logging": {
                        "driver": "json-file",
                        "options": {"max-file": "1", "max-size": "10m"},
                    },
                    "networks": [self.domain.networkname],
                },
            },
            "volumes": {
                "dataexchange": {},
            },
        }

        with open(
            self.paths.COMPOSEPATH + "compose-dataexchange.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(dataexchange, yaml_file)

        old_dir = os.getcwd()
        os.chdir(self.paths.FIREFLYDATAEXCHPATH)
        os.system(
            "openssl req -new -x509 -nodes -days 365 -subj '/CN=localhost/O=org' -keyout key.pem -out cert.pem"
        )
        shutil.copy("cert.pem", "peer-certs/org.pem")
        os.chdir(old_dir)

    def build_database(self):
        console.print("[bold]## Bulding Database[/]")

        shutil.copytree(
            self.paths.FIREFLYDBMIGRATION,
            self.paths.FIREFLYDATABASEPATH + "migrations",
        )

        old_dir = os.getcwd()
        os.chdir(self.paths.FIREFLYDATABASEPATH)
        os.system(
            "openssl req -new -x509 -nodes -days 365 -subj '/CN=database/O=teste.com' -keyout key.pem -out cert.pem"
        )
        os.chdir(old_dir)

        with open(self.paths.FIREFLYDATABASEPATH + "sslenable.sql", "w") as file1:
            # Writing data to a file
            file1.write(
                "ALTER SYSTEM SET ssl_cert_file TO '/var/lib/postgresql/server.crt';\n"
            )
            file1.write(
                "ALTER SYSTEM SET ssl_key_file TO '/var/lib/postgresql/server.key';\n"
            )
            file1.write("ALTER SYSTEM SET ssl TO 'ON';\n")
            file1.write("select pg_reload_conf();")

        database = {
            "version": "3.7",
            "networks": {
                self.domain.networkname: {
                    "name": self.domain.networkname,
                    "external": True,
                }
            },
            "services": {
                "database."
                + self.domain.name: {
                    "container_name": "database." + self.domain.name,
                    "image": "postgres",
                    "volumes": [
                        "database:/var/lib/postgresql/data",
                        self.paths.FIREFLYDATABASEPATH + "migrations:/migrations",
                        self.paths.FIREFLYDATABASEPATH
                        + "cert.pem:/var/lib/postgresql/server.crt",
                        self.paths.FIREFLYDATABASEPATH
                        + "key.pem:/var/lib/postgresql/server.key",
                        self.paths.FIREFLYDATABASEPATH
                        + "sslenable.sql:/var/lib/postgresql/sslenable.sql",
                    ],
                    "ports": ["5432:5432"],
                    "logging": {
                        "driver": "json-file",
                        "options": {"max-file": "1", "max-size": "10m"},
                    },
                    "environment": [
                        "POSTGRES_PASSWORD=firefly_password",
                        "POSTGRES_USER=firefly",
                        "POSTGRES_DB=firefly",
                    ],
                    "networks": [self.domain.networkname],
                },
            },
            "volumes": {
                "database": {},
            },
        }

        with open(
            self.paths.COMPOSEPATH + "compose-database.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(database, yaml_file)

    def build_firefly_core(self):
        console.print("[bold]## Bulding FireFly Core[/]")

        corefld = Path(self.paths.FIREFLYCOREPATH)
        corefld.mkdir(parents=True, exist_ok=True)

        orgclient = self.domain.organizations[0]

        corecfg = {
            "log": {"level": "debug"},
            "debug": {"port": 6060},
            "http": {
                "port": 5000,
                "address": "0.0.0.0",
                "publicURL": "http://127.0.0.1:5000",
            },
            "admin": {
                "port": 5101,
                "address": "0.0.0.0",
                "publicURL": "http://127.0.0.1:5101",
                "enabled": True,
            },
            "spi": {
                "port": 5101,
                "address": "0.0.0.0",
                "publicURL": "http://127.0.0.1:5101",
                "enabled": True,
            },
            "metrics": {},
            "ui": {"path": "./frontend"},
            "event": {"dbevents": {"bufferSize": 10000}},
            "plugins": {
                "database": [
                    {
                        "name": "database0",
                        "type": "postgres",
                        "postgres": {
                            "url": "postgresql://firefly:firefly_password@database."
                            + self.domain.name
                            + ":5432/firefly",
                            "migrations": {"auto": False},
                        },
                    }
                ],
                "blockchain": [
                    {
                        "name": "blockchain0",
                        "type": "fabric",
                        "fabric": {
                            "fabconnect": {
                                "url": "http://fabconnect."
                                + self.domain.name
                                + ":3000",
                                "channel": self.domain.networkname,
                                "chaincode": self.ffchaincode.name,
                                "topic": "0",
                                "signer": "admin",
                            }
                        },
                    }
                ],
                "sharedstorage": [
                    {
                        "name": "sharedstorage0",
                        "type": "ipfs",
                        "ipfs": {
                            "api": {
                                "url": "http://sharedstorage."
                                + self.domain.name
                                + ":5001"
                            },
                            "gateway": {
                                "url": "http://sharedstorage."
                                + self.domain.name
                                + ":8080"
                            },
                        },
                    }
                ],
                "dataexchange": [
                    {
                        "name": "dataexchange0",
                        "type": "ffdx",
                        "ffdx": {
                            "url": "http://dataexchange." + self.domain.name + ":3000"
                        },
                    }
                ],
            },
            "namespaces": {
                "default": "default",
                "predefined": [
                    {
                        "defaultKey": orgclient.name,
                        "description": "Default predefined namespace",
                        "multiparty": {
                            "contract": [
                                {
                                    "firstEvent": "",
                                    "location": {
                                        "channel": self.domain.networkname,
                                        "chaincode": self.ffchaincode.name,
                                    },
                                }
                            ],
                            "enabled": True,
                            "node": {
                                "name": "firefly." + self.domain.name,
                            },
                            "org": {
                                "key": orgclient.name,
                                "name": orgclient.name,
                            },
                        },
                        "name": "default",
                        "plugins": [
                            "database0",
                            "blockchain0",
                            "dataexchange0",
                            "sharedstorage0",
                        ],
                    }
                ],
            },
        }

        with open(
            self.paths.FIREFLYCOREPATH + "firefly.core.yaml",
            "w",
            encoding="utf-8",
        ) as yaml_file:
            yaml.dump(corecfg, yaml_file)

        fireflycore = {
            "version": "3.7",
            "networks": {
                self.domain.networkname: {
                    "name": self.domain.networkname,
                    "external": True,
                }
            },
            "services": {
                "firefly."
                + self.domain.name: {
                    "container_name": "firefly." + self.domain.name,
                    "image": "ghcr.io/hyperledger/firefly",
                    "volumes": [
                        self.paths.FIREFLYCOREPATH
                        + "firefly.core.yaml:/etc/firefly/firefly.core",
                        "firefly_core_db:/etc/firefly/db",
                    ],
                    "ports": ["5000:5000", "5101:5101"],
                    "logging": {
                        "driver": "json-file",
                        "options": {"max-file": "1", "max-size": "10m"},
                    },
                    "networks": [self.domain.networkname],
                    # "entrypoint": ["/bin/sh", "-c", "exit", "0"],
                }
            },
            "volumes": {
                "firefly_core_db": {},
            },
        }

        with open(
            self.paths.COMPOSEPATH + "compose-fireflycore.yaml", "w", encoding="utf-8"
        ) as yaml_file:
            yaml.dump(fireflycore, yaml_file)
