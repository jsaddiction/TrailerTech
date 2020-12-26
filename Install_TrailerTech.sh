#!/bin/bash

#### USER SETTINGS
# installDirectory: can not be a root directory default: /config/scripts/TrailerTech
# PUID is the id of the user who will be calling this script. Uncomment and set to appropriate values if KodiLibrarian files have wrong uid set
# PGID same as PUID but for group
installDirectory="/config/scripts/TrailerTech"
# ${PUID}=1234
# #{PGID}=1234

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
    error=$(chmod -R ug+rw ${parentDir} 2>&1) || { echo "Failed to set permissions on ${parentDir}. ERROR: ${error}" ; exit 1; }
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

### Set permissions and install dependancies
echo "********** Setting Permissions for TrailerTechnician **********"
error=$(chown -R ${PUID}:${PGID} ${installDirectory} 2>&1) || { echo "Failed to set ownership on ${installDirectory}. ERROR: ${error}" ; }
error=$(chmod -R ug+rwx ${installDirectory} 2>&1) || { echo "Failed to set permissions on ${installDirectory}. ERROR: ${error}" ; exit 1;}

echo "********** Installing TrailerTech Dependencies **********"
error=$(python3 -m pip install -r ${requirementsFile} 2>&1) || { echo "Failed to install dependencies. ERROR: ${error}" ; exit 1; }
