<?php
parse_str($_SERVER['QUERY_STRING'], $_GET);

// Replicate the current environment but change method to GET to avoid called cgi to expect a stdin content
$env = $_SERVER;
$env['CONTENT_LENGTH'] = '';
$env['HTTP_CONTENT_LENGTH'] = '';
unset($env['CONTENT_TYPE']);
unset($env['HTTP_CONTENT_TYPE']);
$env['REQUEST_METHOD'] = 'GET';

$descriptorspec = array(0 => array("pipe", "r"), 1 => array("pipe", "w"));

// if SynoToken is not provided then retrieve it manually
if ($_GET['SynoToken'] == '' and $_SERVER['X-SYNO-TOKEN'] == '') {
	// Cannot use shell_exec because it interferes with STDIN breaking POST data
	$process = proc_open('/usr/syno/synoman/webman/login.cgi 2>/dev/null', $descriptorspec, $pipes, NULL, $env);
	fclose($pipes[0]);
	$response = stream_get_contents($pipes[1]);
	fclose($pipes[1]);
	proc_close($process);

	if (preg_match('/SynoToken" *: *"([^"]+)"/',$response,$matches)===1) {
		$env['QUERY_STRING'] = "SynoToken=$matches[1]";
	}
}

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
/* removed because a user might have admin rights without being admin. TODO: find a way...
if ($username !== 'admin') {
	echo $_SERVER['SERVER_PROTOCOL'] . " 400 Bad Request\n";
	echo "Content-type: text/html; charset=utf-8\n\n";
	echo '<HTML><HEAD><TITLE>Login Required</TITLE></HEAD><BODY>Please login first as admin</BODY></HTML>';
	exit;
}
*/

