#!/bin/bash
sudo apt-get update
sudo apt-get install -yq rabbitmq-server

# Install Python
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

cat <<EOF > /etc/rabbitmq/rabbitmq.config
[
  {rabbit, [
     {tcp_listeners, [6555]}
     ]}
].
EOF

service rabbitmq-server restart

sudo rabbitmqctl add_user dynalize dyn123
sudo rabbitmqctl add_vhost dynalize_vhost
sudo rabbitmqctl set_permissions -p dynalize_vhost dynalize  ".*" ".*" ".*"


