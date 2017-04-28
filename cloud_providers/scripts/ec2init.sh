#!/bin/bash

export DEPLOY_SHUTDOWN={{DEPLOY_SHUTDOWN}}
export DEPLOY_DIRECTORY=/dynalize

# Install Python
sudo apt-get update
sudo apt-get install -yq python3 python3-pip unzip

# Install Git
sudo apt-get install -yq git

# Update to Python 3.4.2
sudo apt-get build-dep -yq python3.4
wget https://www.python.org/ftp/python/3.4.2/Python-3.4.2.tgz
tar -xzf Python-3.4.2.tgz
cd Python-3.4.2
./configure
make
sudo make install

# Install Docker
curl -o /install-docker.sh http://get.docker.io/
chmod +x /install-docker.sh
/install-docker.sh

# Setup Dynalize
mkdir $DEPLOY_DIRECTORY
cd $DEPLOY_DIRECTORY

curl -o $DEPLOY_DIRECTORY/deploy.zip "{{DEPLOY_URL_APP}}" && unzip $DEPLOY_DIRECTORY/deploy.zip
sudo pip3 install -r requirements.txt

if [ -f $DEPLOY_DIRECTORY/deploy.json ]
then
	sudo python3 main.py
fi


# Add upstart script

cat <<EOF > /etc/init/dynalize.conf
# Dynalize
# See https://help.ubuntu.com/community/UbuntuBootupHowto for details

description "Dynalize Master/Worker"
author "PUM"

# Stanzas
#
# Stanzas control when and how a process is started and stopped
# See a list of stanzas here: http://upstart.ubuntu.com/wiki/Stanzas#respawn

# When to start the service
start on runlevel [2345]

# When to stop the service
stop on runlevel [016]

# Automatically restart process if crashed
respawn

# Change working dir
chdir $DEPLOY_DIRECTORY

# Start the process
exec python3 $DEPLOY_DIRECTORY/main.py
EOF



# Check if dynalize should be started after deployment, otherwise shutdown
if [ "$DEPLOY_SHUTDOWN" == "1" ]
then
	sudo halt
else
	python3 $DEPLOY_DIRECTORY/main.py {{DEPLOY_PARAMETER}}
fi
