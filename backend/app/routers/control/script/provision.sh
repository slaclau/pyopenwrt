sysupgrade -b /tmp/old.tar.gz
logger -t CONTROLLER "backed up old config to old.tar.gz"

CONTROLLER_IP=$(uci get controller.@inform[0].controller_ip)
DEVICE_ID=$(uci get controller.@inform[0].device_id)

wget http://"$CONTROLLER_IP":8000/configuration/raw/"$DEVICE_ID" -O /tmp/new.tar.gz
logger -t CONTROLLER "downloaded new config to new.tar.gz"

sysupgrade -r /tmp/new.tar.gz
logger -t CONTROLLER "loaded new config from new.tar.gz"

service system restart
service network restart
wifi
service dnsmasq restart

sleep 90

if /usr/libexec/controller/inform.sh; then
  rm /tmp/old.tar.gz
  rm /tmp/new.tar.gz
  logger -t CONTROLLER "keeping new config"
else
  sysupgrade -r /tmp/old.tar.gz
  rm /tmp/old.tar.gz
  rm /tmp/new.tar.gz
  service system restart
  service network restart
  logger -t CONTROLLER "reverting"
fi;