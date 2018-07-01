#!/bin/sh
# checked with shellcheck -x

#--------------------------------------------------------------------------------------
# This script is called at shadowsocks-libev startup on Synology when ss-redir is used.
# It sets up TCP redirections.
# It is only called once, for the instance launched with ss-redir.json, but it also creates redirection rules for the other ss-redir-xxx.json if any.
# The additional ss-redir-xxx.json need to have iptables filtering rules into ss-redir-xxx.ipt-rules-include and/or
# ss-redir-xxx.ipt-rules-exclude so that some ip traffic goes to ss-redir-xxx while default traffic goes to main ss-redir.
# All server ports found in any ss-xxx.json are excluded from redirection rules.
# IPs (or domains) from file ss-redir-ignore-ips are also excluded from redirection.
# Limitations:
# - does not handle redirects of local packets (OUTPUT chain)
#--------------------------------------------------------------------------------------

# Source package specific variable and functions
SVC_SETUP="$(dirname "$0")/service-setup"
if [ -r "${SVC_SETUP}" ]; then
	#shellcheck source=service-setup
	. "${SVC_SETUP}"
fi

TABLE=nat
TCPUDP=tcp

MAINCHAIN="SS_REDIR"

# List of other IPs to bypass
IGNORE_LIST="$CONFIG_DIR/ss-redir-ignore-ips"

# List of target IPs to be excluded from redirection
get_wan_ip() {
	cat <<-EOF | grep -E "^([0-9]{1,3}\.){3}[0-9]{1,3}(/[0-9.]*)?" | sort -u
	$(jq -r '.server' "$CONFIG_DIR"/ss-*.json)
	$(cat "${IGNORE_LIST:=/dev/null}" 2>/dev/null)
	EOF
}
gen_iplist() {
    cat <<-EOF
	0.0.0.0/8
	10.0.0.0/8
	100.64.0.0/10
	127.0.0.0/8
	169.254.0.0/16
	172.16.0.0/12
	192.0.0.0/24
	192.0.2.0/24
	192.88.99.0/24
	192.168.0.0/16
	198.18.0.0/15
	198.51.100.0/24
	203.0.113.0/24
	224.0.0.0/4
	240.0.0.0/4
	255.255.255.255
	$(get_wan_ip)
	EOF
}
insert_modules() {
	/usr/syno/bin/synomoduletool --insmod Shadowsocks x_tables.ko ip_tables.ko iptable_filter.ko nf_conntrack.ko nf_defrag_ipv4.ko nf_conntrack_ipv4.ko nf_nat.ko iptable_nat.ko ipt_REDIRECT.ko xt_multiport.ko xt_tcpudp.ko xt_state.ko ipt_MASQUERADE.ko
}

# Activate routing, but not ICMP redirects
/sbin/sysctl -w -q net.ipv4.ip_forward=1
/sbin/sysctl -w -q net.ipv4.conf.all.send_redirects=0
/sbin/sysctl -w -q net.ipv4.conf.default.send_redirects=0
/sbin/sysctl -w -q net.ipv4.conf.eth0.send_redirects=0

# Insert needed iptables kernel modules
insert_modules

# If it already exists, flush and remove the main SS_XXX chain from PREROUTING/OUTPUT else create it
if $IPT -t "$TABLE" -L "$MAINCHAIN" -n >>/dev/null 2>&1; then
	$IPT -t "$TABLE" -F "$MAINCHAIN"
	$IPT -t "$TABLE" -D PREROUTING -p $TCPUDP -j "$MAINCHAIN" 2>>/dev/null
	$IPT -t "$TABLE" -D OUTPUT -p $TCPUDP -j "$MAINCHAIN" 2>>/dev/null
else
	$IPT -t "$TABLE" -N "$MAINCHAIN"
fi

# Ignore local IPs, SS servers IPs
for ip in $(gen_iplist)
do
	$IPT -t "$TABLE" -A "$MAINCHAIN" -d "$ip" -j RETURN
done

# Create SS_XXX_[xxx] chains for each ss-redir instance.
# If there are files ss-redir-xxx: add rules to decide what should be (or should not be) redirected there
# Files ss-redir-xxx.ipt-rules-include and/or ss-redir-xxx.ipt-rules-exclude must have the iptables parameters for this
for CONF_FILE in "$CONFIG_DIR"/ss-redir*.json
do
	CONF_NAME=$(echo "$CONF_FILE" | sed -E 's,'"$CONFFILES_REGEX"',\4,')

	# Allow to have specific parameters in ss-<server>-xxx.params
	# not really needed because most parameters can be specified in the json file, so commented out
	#PARAMS="$(grep '^-' $CONFIG_DIR/$SS_SERVER${CONF_NAME:+-$CONF_NAME}.params 2>/dev/null)"

	CMD="$INSTALL_DIR/bin/$SS_SERVER $PARAMS -c $CONF_FILE -f $PID_FILE"

	# tcp is inactive if option udp_only or -U (default is active)
	if grep -E -q 'udp_only' "$CONF_FILE" || [ -z "${CMD##* -U*}" ]; then
		continue
	fi

	CHAIN="${MAINCHAIN}_$CONF_NAME"

	# Flush chain if it already exists, create it if not
	if $IPT -t "$TABLE" -L "$CHAIN" -n >>/dev/null 2>&1; then
		$IPT -t "$TABLE" -F "$CHAIN"
	else
		$IPT -t "$TABLE" -N "$CHAIN"
	fi

	EXCLUDE_FILE="$CONFIG_DIR/ss-redir${CONF_NAME:+-$CONF_NAME}.ipt-rules-exclude"
	grep "^-" "$EXCLUDE_FILE" 2>>/dev/null | while read -r rule
	do
		#shellcheck disable=SC2086
		$IPT -t "$TABLE" -A "$CHAIN" -p $TCPUDP $rule -j RETURN
	done

	# Local port to redirect to, from ss-redir-xxx.json
	local_port=$(jq -r '.local_port' "$CONF_FILE")

	INCLUDE_FILE="$CONFIG_DIR/ss-redir${CONF_NAME:+-$CONF_NAME}.ipt-rules-include"
	( grep "^-" "$INCLUDE_FILE" 2>>/dev/null || echo ) | while read -r rule
	do
		#shellcheck disable=SC2086
		$IPT -t "$TABLE" -A "$CHAIN" -p $TCPUDP $rule -j REDIRECT --to-ports "$local_port"
	done

	$IPT -t "$TABLE" -A "$MAINCHAIN" -p $TCPUDP -j "$CHAIN"
done

# Install main SS_XXX chain in PREROUTING chain
$IPT -t "$TABLE" -A PREROUTING -p $TCPUDP -j "$MAINCHAIN"

# Optionally install main SS_XXX chain in OUTPUT chain
# TODO
