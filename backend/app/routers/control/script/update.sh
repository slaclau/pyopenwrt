#!/bin/sh

CONTROLLER_IP="$1"

echo "$CONTROLLER_IP"

wget http://"$CONTROLLER_IP":8000/control/script/inform.uc
wget http://"$CONTROLLER_IP":8000/control/script/inform.sh
wget http://"$CONTROLLER_IP":8000/control/script/inform_wrapper.sh
wget http://"$CONTROLLER_IP":8000/control/script/inform

wget http://"$CONTROLLER_IP":8000/control/script/provision.sh

chmod +x inform.sh
chmod +x inform_wrapper.sh
chmod +x inform
chmod +x provision.sh

mkdir -p /usr/libexec/controller

mv inform.uc /usr/libexec/controller/
mv inform.sh /usr/libexec/controller/
mv inform_wrapper.sh /usr/libexec/controller/
mv provision.sh /usr/libexec/controller/

mv inform /etc/init.d/

service inform enable
service inform start

rm update.sh