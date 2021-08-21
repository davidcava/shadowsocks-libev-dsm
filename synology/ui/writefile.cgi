#!/usr/bin/env php
<?php
#require 'authenticate.php';
require 'authwithouttoken.php';
require 'synoenv.php';

echo "Content-type: text/plain; charset=utf-8\n\n";

parse_str(fread(STDIN,$_SERVER['CONTENT_LENGTH']),$_POST);

$filename = basename($_POST['name']); // basename to make sure we do not try to access other folders
$filepath = $config_dir . '/' . $filename;

if (preg_match('/^(ss-local|ss-server|ss-redir|ss-tunnel|ss-manager|v2ray)(-[[:alnum:]]*)?\.json$/u', $filename, $matches)!==1) {
	echo "Invalid config filename: $filename";
} else {
	if (file_put_contents($filepath,$_POST['action']) !== FALSE) {
		echo "ok\n";
	} else {
		echo "error:Can't open file $filepath to write\n";
	}
}
