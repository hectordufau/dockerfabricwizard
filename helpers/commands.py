import os


class Commands:
    def __init__(self) -> None:
        pass

    def enroll(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        caname: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home

        os.system(
            apppath
            + "/bin/fabric-ca-client enroll -u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            + " --caname "
            + caname
            + " --tls.certfiles "
            + certfile
        )

    def enroll_msp(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        caname: str,
        msppath: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home

        os.system(
            apppath
            + "/bin/fabric-ca-client enroll -u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            + " --caname "
            + caname
            + " -M "
            + msppath
            + " --tls.certfiles "
            + certfile
        )

    def enroll_tls(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        port: int,
        caname: str,
        tlspath: str,
        csrhosts: [],
        myhost: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home

        os.system(
            apppath
            + "/bin/fabric-ca-client enroll -u https://"
            + user
            + ":"
            + passwd
            + "@localhost:"
            + str(port)
            + " --caname "
            + caname
            + " -M "
            + tlspath
            + " --enrollment.profile tls --csr.hosts "
            + ",".join(csrhosts)
            + " --myhost "
            + myhost
            + " --tls.certfiles "
            + certfile
        )

    def register_orderer(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        caname: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home

        os.system(
            apppath
            + "/bin/fabric-ca-client register "
            + " --caname "
            + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type orderer "
            + " --tls.certfiles "
            + certfile
        )

    def register_admin(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        caname: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home

        os.system(
            apppath
            + "/bin/fabric-ca-client register "
            + " --caname "
            + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type admin "
            + " --tls.certfiles "
            + certfile
        )

    def register_peer(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        caname: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home

        os.system(
            apppath
            + "/bin/fabric-ca-client register "
            + " --caname "
            + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type peer "
            + " --tls.certfiles "
            + certfile
        )

    def register_client(
        self,
        apppath: str,
        home: str,
        user: str,
        passwd: str,
        caname: str,
        certfile: str,
    ):
        os.environ["FABRIC_CA_CLIENT_HOME"] = home

        os.system(
            apppath
            + "/bin/fabric-ca-client register "
            + " --caname "
            + caname
            + " --id.name "
            + user
            + " --id.secret "
            + passwd
            + " --id.type client "
            + " --tls.certfiles "
            + certfile
        )
