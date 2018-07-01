#!/bin/bash
# checked with: shellcheck -x gensc.sh

# Source package specific variable and functions
SVC_SETUP="$(dirname "$0")/service-setup"
if [ -r "${SVC_SETUP}" ]; then
    #shellcheck source=service-setup
    . "${SVC_SETUP}"
fi

PORT_SC_FILE="$INSTALL_DIR/port_conf/shadowsocks-libev.sc"
PORT_SC_FILE_TMP="$INSTALL_DIR/port_conf/shadowsocks-libev.tmp"

gensc ()
{
    local CONF_FILE

    echo "# File generated automatically by gensc, changes will be overwritten"
    echo

    #Look for any ss-<ssserver>-<name>.json config files in configuration etc folder
    while read -r CONF_FILE
    do
        local SS_SERVER CONF_NAME CMD
        SS_SERVER=$(echo "$CONF_FILE" | sed -E 's,'"$CONFFILES_REGEX"',\2,')
        CONF_NAME=$(echo "$CONF_FILE" | sed -E 's,'"$CONFFILES_REGEX"',\4,')
        CMD="$INSTALL_DIR/bin/$SS_SERVER"

        local tcpmode
        grep -E -q 'udp_only' -- "$CONF_FILE"
        if grep -E -q 'udp_only' -- "$CONF_FILE" || [[ -z "${CMD##* -U*}" ]]; then
            tcpmode=0
        else
            tcpmode=1
        fi

        local udpmode
        if grep -E -q 'tcp_and_udp|udp_only' -- "$CONF_FILE" || [[ -z "${CMD##* -u*}" || -z "${CMD##* -U*}" ]]; then
            udpmode=1
        else
            udpmode=0
        fi

        local title=""
        local ip=""
        local port=""
        case "$SS_SERVER" in
            ss-local)
                ip=$(jq -r '.local_ip' "$CONF_FILE")
                port=$(jq -r '.local_port' "$CONF_FILE")
                title="Proxy SOCKS"
                ;;
            ss-redir)
                ip=$(jq -r '.local_ip' "$CONF_FILE")
                port=$(jq -r '.local_port' "$CONF_FILE")
                title="Redir port"
                ;;
            ss-tunnel)
                ip=$(jq -r '.local_ip' "$CONF_FILE")
                port=$(jq -r '.local_port' "$CONF_FILE")
                local tunnel_address
                tunnel_address=$(jq -r '.tunnel_address' "$CONF_FILE")
                title="Tunnel to $tunnel_address"
                ;;
            ss-server)
                ip=$(jq -r '.server_ip' "$CONF_FILE")
                port=$(jq -r '.server_port' "$CONF_FILE")
                title="SS server"
                ;;
        esac

        local tcpudp=""
        if [[ "$tcpmode" = 1 && "$udpmode" = 1 ]]; then
            tcpudp="tcp,udp"
        elif [[ "$tcpmode" = 1 ]]; then
            tcpudp="tcp"
        elif [[ "$udpmode" = 1 ]]; then
            tcpudp="udp"
        fi

        # test for loopback addr is not reliable but at least most common way of writing the loopback are excluded from forward
        local port_forward
        if [[ ( "$SS_SERVER" = "ss-local" || "$SS_SERVER" = "ss-server" || "$SS_SERVER" = "ss-tunnel" ) && "$ip" != "127.0.0.1" && "$ip" != "::1" ]]; then
            port_forward="yes"
        else
            port_forward="no"
        fi

        cat <<-EOF
		[shadowsocks-libev_$SS_SERVER${CONF_NAME:+-$CONF_NAME}]
		title="$title"
		desc="shadowsocks-libev${CONF_NAME:+ $CONF_NAME}"
		port_forward="$port_forward"
		dst.ports="$port/$tcpudp"

	EOF

    done < <( find -L "$CONFIG_DIR" -maxdepth 1 -regextype posix-extended -regex "$CONFFILES_REGEX" -type f )

}

gensc > "$PORT_SC_FILE_TMP"

if diff -q -b -B "$PORT_SC_FILE" "$PORT_SC_FILE_TMP" >>/dev/null; then
    echo No change!
    rm "$PORT_SC_FILE_TMP"
else
    echo -n Port changes
    mv "$PORT_SC_FILE_TMP" "$PORT_SC_FILE"
    /usr/syno/sbin/synopkghelper update shadowsocks-libev port-config && echo " updated successfully" || echo " but ERROR during update"
fi
