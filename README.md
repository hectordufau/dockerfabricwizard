`
# Docker Fabric Wizard

Welcome to Docker Fabric Wizard, a tool designed to simplify the automated installation of [Hyperledger Fabric](https://www.hyperledger.org/projects/fabric) using [Docker](https://hub.docker.com/u/hyperledger/) containers. This tool is aimed at professionals and students interested in blockchain technology.

> __Warning__
This project is under development, however you can use it to build your Hyperledger Fabric network from scratch. It is also not an official [Hyperledger Fabric](https://www.hyperledger.org/projects/fabric) tool.


## Table of Contents

- [Overview](#overview)
- [Versions](#versions)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Chaincode Deploy](#how-to-deploy-a-chaincode-chaincode-as-a-service---ccaas)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [Development Status](#development-status)
- [License](#license)

## Overview

Docker Fabric Wizard streamlines the process of setting up a [Hyperledger Fabric](https://www.hyperledger.org/projects/fabric) network by utilizing [Docker](https://hub.docker.com/u/hyperledger/) containers. It offers an automated installation process based on user-provided network structure details. The tool generates and configures the necessary [Docker](https://hub.docker.com/u/hyperledger/) containers, allowing you to quickly deploy a [Hyperledger Fabric](https://www.hyperledger.org/projects/fabric) network for development, testing, or educational purposes.

## Versions

Docker Fabric Wizard uses Hyperledger Fabric v2.5 LTS (FABRIC_VERSION 2.5.14, fabric-ca 1.5.15).

## Prerequisites

Before you begin, make sure you have the following prerequisites:

- Linux OS (don't use Windows/WSL2 - if your OS is Micro$oft Window$, install and use any VM manager, like VirtualBox or Vagrant)
- Docker
- Python (version 3.10 minimal).
- Git (sure!)
- Basic understanding of [Docker](https://docs.docker.com/) and [Hyperledger Fabric](https://hyperledger-fabric.readthedocs.io/en/latest/getting_started.html) concepts.

## Installation

1. Clone this repository to your local machine:

   ```
   git clone https://github.com/hectordufau/dockerfabricwizard.git
   cd dockerfabricwizard
   ```

2. Install the required dependencies using pip:

   ```
   pip install -r requirements.txt
   ```

## Usage

1. Navigate to the project directory.

2. Run the script by executing the following command:

   ```
   python main.py
   ```

3. Follow the prompts to provide the necessary network structure details.

4. The Docker Fabric Wizard will generate and configure Docker containers based on your inputs.

5. Once the installation is complete, you will have a Hyperledger Fabric network up and running within Docker containers.

6. If you only want build config files (docker composer and HLF config files), just copy all files and folders inside `domain/<domainname>` folder and use them for your own

## How to deploy a chaincode (Chaincode as a Service - CCAAS)

1. Put your whole chaincode code folder inside **chaincodes** folder (dockerfilewizard/chaincodes). You can use Asset Transfer Basic [Typescript](https://github.com/hyperledger/fabric-samples/tree/main/asset-transfer-basic/chaincode-typescript) or