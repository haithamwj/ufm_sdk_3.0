#!/bin/bash -x
cd docker/
tagver=$(cat release_info)
echo $tagver
export SERVER_HOST=$SERVER_HOST
expect << EOF
spawn ssh admin@${SERVER_HOST}
expect "Password:*"
send -- "admin\r"
expect "> "
send -- "enable\r"
expect "# "
send -- "config terminal\r"
expect "/(config/) # "
send -- "ufm plugin rest-rdma add tag $tagver\r"
expect "/(config/) # "
send -- "ufm plugin rest-rdma enable\r"
expect "/(config/) # "
send -- "show ufm plugin\r"
expect "/(config/) # "
send "show ufm status\r"
sleep 10
EOF