#!/bin/bash
# bash notify.sh "Alert title" "Message body"
TOKEN="[PUT YOUR ACCESS TOKEN HERE]"
TITLE="$1"
BODY="$2"

curl --header 'Access-Token: $TOKEN' \
     --data-urlencode type="note" \
     --data-urlencode title="$TITLE" \
     --data-urlencode body="$BODY" \
     --request POST https://api.pushbullet.com/v2/pushes