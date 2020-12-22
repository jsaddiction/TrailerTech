#!/bin/bash

#### USER SETTINGS
# installDirectory: can not be a root directory default: /config/scripts/TrailerTech
installDirectory="/scripts/TrailerTech"

### Scripts variables
parentDir="$(dirname ${installDirectory})"
requirementsFile="${installDirectory}/requirements.txt"

apt update

echo "********** INSTALLING GIT **********"
apt install git -y

echo "********** INSTALLING PYTHON3 **********"
apt install python3 -y
apt install python3-pip -y

echo "********** INSTALLING FFMPEG **********"
apt-get install ffmpeg -y

if [ ! -d ${parentDir} ]
then
    echo "*********** Creating script parent directory ************"
    error=$(mkdir -p ${parentDir} 2>&1) || { echo "Failed to create script parent directory ${parentDir}. ERROR: ${error}" ; exit 1; }
fi

### Clone TrailerTech or update if already exists
if [ ! -d ${installDirectory} ]
then
    echo "********** CLONING TrailerTech **********"
    error=$(git clone https://github.com/jsaddiction/TrailerTech.git ${installDirectory} 2>&1) || { echo "Failed to clone repo into ${installDirectory}. ERROR: ${error}" ; exit 1; }
else
    echo "********** UPDATING TrailerTech **********"
    error=$(git -C ${installDirectory} pull 2>&1) || { echo "Failed to update local repo. ERROR: ${error}" ; }
fi

echo "********** Installing TrailerTech Dependencies **********"
error=$(python3 -m pip install -r ${requirementsFile} 2>&1) || { echo "Failed to install dependencies. ERROR: ${error}" ; exit 1; }