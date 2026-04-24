#!/bin/bash

if [[ -z "$BACKEND" ]]; then
  export BACKEND=0.0.0.0:8000
fi
if [[ -z "$SOCKETIO" ]]; then
  export SOCKETIO=0.0.0.0:9000
fi
if [[ -z "$FRAPPE_SITE_NAME_HEADER" ]]; then
  export FRAPPE_SITE_NAME_HEADER='$host'
fi
if [[ -z "$PROXY_READ_TIMEOUT" ]]; then
  export PROXY_READ_TIMEOUT=120
fi
if [[ -z "$CLIENT_MAX_BODY_SIZE" ]]; then
  export CLIENT_MAX_BODY_SIZE=50m
fi

envsubst '${BACKEND}
  ${SOCKETIO}
  ${FRAPPE_SITE_NAME_HEADER}
  ${PROXY_READ_TIMEOUT}
  ${CLIENT_MAX_BODY_SIZE}' \
  </templates/nginx/frappe.conf.template >/etc/nginx/conf.d/frappe.conf

nginx -g 'daemon off;'
