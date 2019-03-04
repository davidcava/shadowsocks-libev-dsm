#!/usr/bin/env php
<?php
require 'authenticate.php';
require 'synoenv.php';

echo "Content-type: text/plain; charset=utf-8\n\n";

$filename = basename($_GET['name']); // basename to make sure we do not try to access other folders
$action = $_GET['action'];

if (preg_match('/^(ss-local|ss-server|ss-redir|ss-tunnel|ss-manager|v2ray)(-[[:alnum:]]*)?\.json$/u', $filename, $matches)!==1) {
	echo "Invalid config filename: $filename";
} elseif ($action != 'start' && $action != 'stop') {
	echo "Invalid action: $action";
} else {
	system($script_dir . "/start-stop-status $action $matches[1] 2>/dev/null", $return_var);
	echo "result=$return_var\n";
}
