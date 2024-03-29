<?php
error_reporting(E_ERROR);

parse_str($_SERVER['QUERY_STRING'], $_GET);

// Replicate the current environment but change method to GET to avoid called cgi to expect a stdin content
$env = $_SERVER;
$env['CONTENT_LENGTH'] = '';
$env['HTTP_CONTENT_LENGTH'] = '';
unset($env['CONTENT_TYPE']);
unset($env['HTTP_CONTENT_TYPE']);
$env['REQUEST_METHOD'] = 'GET';

$descriptorspec = array(0 => array("pipe", "r"), 1 => array("pipe", "w"));

// Check authentication
$pipes=NULL;
$process = proc_open('/usr/syno/synoman/webman/modules/authenticate.cgi', $descriptorspec, $pipes, NULL, $env);
fclose($pipes[0]);
$username = trim(stream_get_contents($pipes[1]));
fclose($pipes[1]);
proc_close($process);

// Not logged in
if ($username == '') {
	echo $_SERVER['SERVER_PROTOCOL'] . " 403 Forbidden\n";
	echo "Content-type: text/html; charset=utf-8\n\n";
	echo '<HTML><HEAD><TITLE>Login Required</TITLE></HEAD><BODY>Please login first</BODY></HTML>';
	exit;
}

// Not admin
exec('/bin/id -G -n ' . escapeshellarg($username) . ' | grep -qE "( |^)administrators( |$)"', $dummy, $retval);
if ( $retval != 0 ) {
    echo $_SERVER['SERVER_PROTOCOL'] . " 400 Bad Request\n";
    echo "Content-type: text/html; charset=utf-8\n\n";
    echo "<HTML><HEAD><TITLE>Login Required</TITLE></HEAD><BODY>Please use an account with admin rights ($username has not)</BODY></HTML>";
    exit;
}

