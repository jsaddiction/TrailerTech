#!/bin/bash

#### USER SETTINGS
# installDirectory: can not be a root directory default: /config/scripts/TrailerTech
# PUID is the id of the user who will be calling this script. Uncomment and set to appropriate values if KodiLibrarian files have wrong uid set
# PGID same as PUID but for group
installDirectory="/config/scripts/TrailerTech"
# ${PUID}=1234
# ${PGID}=1234

### Scripts variables
parentDir="$(dirname ${installDirectory})"
requirementsFile="${installDirectory}/requirements.txt"
## ubuntu/ Debian based part
if [[ -n "$(command -v apt-get)" ]]; then
   apt update -yq
   install="git python3 python3 ffmpeg"
   for i in ${install}; do
       echo "********** INSTALLING $i **********"
       apt install $i -yq
   done   
fi
## alpine install 
if [[ -n "$(command -v apk)" ]]; then
   apk -qU --no-cache update
   apk -qU --no-cache upgrade
   install="git python3 python3 ffmpeg"
   for i in ${install}; do
       echo "********** INSTALLING $i **********"
       apk -qU --no-cache --no-progres add $i
   done
fi

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
