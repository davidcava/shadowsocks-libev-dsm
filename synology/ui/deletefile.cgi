#!/usr/bin/env php
<?php
#require 'authenticate.php';
require 'authwithouttoken.php';
require 'synoenv.php';

echo "Content-type: text/plain; charset=utf-8\n\n";

$filename = basename($_GET['name']); // basename to make sure we do not try to access other folders
$filepath = $config_dir . '/' . $filename;

if (preg_match('/^(ss-local|ss-server|ss-redir|ss-tunnel|ss-manager|v2ray)(-[[:alnum:]]*)?\.json$/u', $filename, $matches)!==1) {
	echo "Invalid config filename: $filename\n";
} else {
	if (! file_exists($filepath)) {
		echo "file not found\n";
	} else {
		if (unlink($filepath)) {
			echo "ok\n";
		} else {
			echo "Deleting failed for $filepath\n";
		}
	}
}
