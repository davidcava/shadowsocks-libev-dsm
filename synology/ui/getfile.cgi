#!/usr/bin/env php
<?php
require 'authenticate.php';
require 'synoenv.php';

echo "Content-type: text/plain; charset=utf-8\n\n";

$filename = basename($_GET['name']); // basename to make sure we do not try to access other folders
$filepath = $config_dir . '/' . $filename;

if (preg_match('/^(ss-local|ss-server|ss-redir|ss-tunnel|ss-manager|v2ray)(-[[:alnum:]]*)?\.json$/u', $filename, $matches)!==1) {
	echo "Invalid config filename: $filename";
} else {
	if (file_exists($filepath)) {
		readfile($filepath);
	} else {
		readfile("templates/" . $matches[1]  . ".json");
	}
}
