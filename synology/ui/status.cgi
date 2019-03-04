#!/usr/bin/env php
<?php
require 'authenticate.php';
require 'synoenv.php';

echo "Content-type: text/plain; charset=utf-8\n\n";

$filename = basename($_GET['name']); // basename to make sure we do not try to access other folders

if (preg_match('/^(ss-local|ss-server|ss-redir|ss-tunnel|ss-manager|v2ray)(-[[:alnum:]]*)?\.json$/u', $filename, $matches)!==1) {
	echo "Invalid config filename: $filename";
} else {
	$filepath = '../var/' . $matches[1] . $matches[2] . ".pid";
	if (file_exists($filepath)) {
		if (posix_kill(file_get_contents($filepath), 0)) {
			echo "0\n";
		} else {
			echo "2\n";
		}
	} else {
		echo "1\n";
	}
}
