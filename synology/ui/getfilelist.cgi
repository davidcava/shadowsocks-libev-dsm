#!/usr/bin/env php
<?php
#require 'authenticate.php';
require 'authwithouttoken.php';
require 'synoenv.php';

echo "Content-type: application/json; charset=utf-8\n\n";

$allfiles = array_diff(scandir($config_dir), array( ".", ".." ));
sort($allfiles,SORT_FLAG_CASE|SORT_STRING);
$tree = array();
foreach (array('ss-local','ss-server','ss-redir','ss-tunnel','ss-manager') as $ss) {
	$children = array();
	foreach(preg_grep("/^$ss(-[[:alnum:]]*)?\.json$/u",$allfiles) as $filename) {
		$children[] = [ 'text' => $filename, 'leaf' => true ];
	}
	$tree[] = array( 'text' => $ss, 'children' => $children );
}
echo json_encode($tree);
?>

