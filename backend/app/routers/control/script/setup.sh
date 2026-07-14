#!/bin/sh

CONTROLLER_IP="$1"

echo "$CONTROLLER_IP"

wget http://"$CONTROLLER_IP":8000/control/script/update.sh
sh update.sh "$CONTROLLER_IP"

touch /etc/config/controller
uci add controller inform
uci set "controller.@inform[0].controller_ip=$CONTROLLER_IP"
uci set "controller.@inform[0].adopted=0"
rm setup.sh