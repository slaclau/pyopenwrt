#!/bin/sh

. /usr/share/libubox/jshn.sh

CONTROLLER_IP=$(uci get controller.@inform[0].controller_ip)
MSG_JSON="$(ucode /usr/libexec/controller/inform.uc)"

RTN=$(wget -O - --post-data="$MSG_JSON" \
  --header='Content-Type: application/json' \
  http://"$CONTROLLER_IP":8000/control/inform \
  2> /dev/null)

echo $RTN
logger -t CONTROLLER "sent inform packet"
if [ -z "$RTN" ]; then
  logger -t CONTROLLER "got no response"
  exit 1
else
  logger -t CONTROLLER "got rtn $RTN"
fi

json_load "$RTN"
if uci get controller.@inform[0] && uci get controller.@inform[0].device_id; then
  logger -t CONTROLLER "device id configured already"
else
  json_get_var DEVICE_ID "device_id"
  if uci get controller.@inform[0]; then
    pass
  else
    uci add controller inform
  fi;
  uci set controller.@inform[0].device_id="$DEVICE_ID"
  logger -t CONTROLLER "device id set to $DEVICE_ID"
  uci commit
fi;

json_get_var COMMAND "command"
logger -t CONTROLLER "received command $COMMAND"
case "$COMMAND" in
  reboot)
    reboot now
    ;;
  adopt)
    uci set controller.@inform[0].adopted=1
    uci commit
    /usr/libexec/controller/provision.sh &
    ;;
  provision)
    /usr/libexec/controller/provision.sh &
    ;;
  update-inform)
    wget http://"$CONTROLLER_IP":8000/control/script/update.sh
    sh update.sh "$CONTROLLER_IP"
    ;;
  locate)
    . /lib/functions/leds.sh
    status_led=$(get_dt_led running)
    status_led_blink_fast
    ;;
  stop-locate)
    . /lib/functions/leds.sh
    status_led=$(get_dt_led running)
    status_led_on
esac

