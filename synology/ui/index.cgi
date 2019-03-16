#!/bin/env php
<?php
require 'authwithouttoken.php';

echo "Content-type: text/html; charset=utf-8\n\n";
?>
<html>
<head>
    <title>Shadowsocks-libev</title>
    <link rel="stylesheet" type="text/css" href="/scripts/ext-3/resources/css/ext-all.css"/>
        <!-- yup, I'm mixing themes from both versions, gives a bit more native look -->
    <link rel="stylesheet" type="text/css" href="/scripts/ext-3/resources/css/xtheme-gray.css"/>
    <script type="text/javascript" src="/scripts/ext-3/adapter/ext/ext-base.js"></script>
    <script type="text/javascript" src="/scripts/ext-3/ext-all.js"></script>
    <script src="/webman/dsmtoken.cgi"></script>
</head>
<body>
<script type="text/javascript">


Ext.onReady(function() {

	var texta = new Ext.form.TextArea ({
		region: 'center',
		name: 'msg',
		style: 'font-family:monospace',
		grow: false,
		preventScrollbars: false,
		disabled: true,
		msgTarget: "title",
		enableKeyEvents:true,
		listeners: {
			// BUG: pasting/moving text with mouse does not trigger dirty state
			keyup: function(f, e) {
				if (saveBtn.disabled && texta.isDirty()) saveBtn.enable();
				else if (!saveBtn.disabled && texta.getValue()==texta.originalValue) saveBtn.disable();
			}
		},
		validator: function(val) {
			try {
				Ext.util.JSON.decode(val);
				return true;
			} catch(e) {
				return e.message;
			}
		}
	});
		
	var saveBtn = new Ext.Button({
		name: 'save',
		text: 'Save',
		handler: function(){
			var e=texta.getActiveError();
			var node=nav.getSelectionModel().getSelectedNode();
			var filename = node.text;
			saveBtn.disable();
			if (e!='') {
				Ext.Msg.show({title:'Config file is not valid',msg:e,buttons: Ext.Msg.OK,icon: Ext.Msg.ERROR});
				return;
			}
			texta.disable(); // no changes during saving
			conn.request({
				url: 'writefile.cgi',
				method: 'POST',
				params: Ext.urlEncode({name: filename, action: texta.getValue()}),
				callback: function(options,success,responseObject) {
					if (success && responseObject.responseText=="ok\n") {
						Ext.Msg.show({title: 'Status',msg: 'File&nbsp;' + filename + '&nbsp;saved.',buttons: Ext.Msg.OK, icon: Ext.Msg.INFO});
						if (node==nav.getSelectionModel().getSelectedNode()) {
							texta.originalValue=texta.getValue(); // set not dirty
						}
					} else {
						Ext.Msg.show({title: 'Error',msg: 'Error&nbsp;saving&nbsp;file&nbsp;' + filename + ':<PRE>' + responseObject.responseText + '</PRE>',buttons: Ext.Msg.OK, icon: Ext.Msg.ERROR});
					}
					if (node==nav.getSelectionModel().getSelectedNode()) {
						texta.enable();
					}
				}
			});
		},
		icon: 'images/save.png',
		cls: 'x-btn-text-icon',
		disabled: true
	});

	var startstopBtn = new Ext.Button({
		name: 'startstop',
		text: 'Start/Stop',
		handler: function(){
			var node=nav.getSelectionModel().getSelectedNode();
			var filename = node.text;
			var action = startstopBtn.getText();
			if (texta.isDirty() && action == 'Start') {
				Ext.Msg.show({title:'Config file not saved',msg: 'Save the config file before starting the service',buttons: Ext.Msg.OK,icon: Ext.Msg.WARNING});
				return;
			}
			startstopBtn.disable();
			conn.request({
				url: 'startstop.cgi',
				method: 'GET',
				params: Ext.urlEncode({name: filename, action: action.toLowerCase()}),
				callback: function(options,success,responseObject) {
					var resp = responseObject.responseText;
					if (success && resp.endsWith('result=0\n')) {
						Ext.Msg.show({title: action + ' result',msg: action + ' log:<PRE>' + resp.substr(0,resp.lastIndexOf('result=')-1) + '</PRE>',buttons: Ext.Msg.OK, icon: Ext.Msg.INFO});
					} else {
						Ext.Msg.show({title: action + ' failed',msg: action + ' log:<PRE>' + resp + '</PRE>',buttons: Ext.Msg.OK,icon: Ext.Msg.ERROR});
					}
					checkStatus(node);
				}
			});
		},
		icon: 'images/start.png',
		cls: 'x-btn-text-icon',
		disabled: true
	});

	var toolb =	new Ext.Toolbar({
		height: 24,
            region: 'north',
				items: [
					saveBtn,
					startstopBtn
				]
			});

	var nav = new Ext.tree.TreePanel({
		title: 'Configuration files',
		region: 'west',
		split: true,
		width: 200,
		collapsible: false,
		dataUrl: 'getfilelist.cgi',
		requestMethod: 'GET',
		rootVisible: false,
		root: new Ext.tree.AsyncTreeNode({
			expanded: true,
			preloadChildren: true,
		}),
		listeners: {
			 append: function (tree, pnode, node, idx) {
				if (node.isLeaf()) checkStatus(node);
			}
		},
		selModel: new Ext.tree.DefaultSelectionModel({
			listeners: {
				beforeselect: function(th, newNode, oldNode) {
					if (texta.isDirty()) {
						Ext.Msg.show({title:'Unsaved changed',msg:'Your changes on file ' + oldNode.text + ' have been cancelled',buttons: Ext.Msg.OK, icon: Ext.Msg.INFO});
					}
				},
				selectionchange: function(th,node) {
					saveBtn.disable();
					startstopBtn.disable();
					texta.disable();
					texta.setValue('');
					texta.clearInvalid();
					if (node && node.isLeaf()) {
						checkStatus(node);
						conn.request({
							url: 'getfile.cgi?'+Ext.urlEncode({name: node.text}),
							method: 'GET',
							success: function(responseObject) {
								if (node==nav.getSelectionModel().getSelectedNode()){
									texta.originalValue=responseObject.responseText; //for dirty state
									texta.setValue(texta.originalValue);
									texta.enable();
								}
							}
						});
					}
				}
			}
		}),
		tools: [ 
		{
			id: "plus",
			handler: function() {
				var node = nav.getSelectionModel().getSelectedNode();
				function createNode(newnodename) {
					if (node.findChild("text", newnodename) != null)
						Ext.Msg.show({title:'Create config file',msg:"Config file " + newnodename + " already exists.",buttons: Ext.Msg.OK,icon: Ext.Msg.WARNING});
					else
						node.appendChild(new Ext.tree.TreeNode({text: newnodename, leaf: true})).select();
				}
				if (node == null) {
					Ext.Msg.show({title:"Create config file",msg:"Select first in the tree the ss-xxx server for which you want to create the new config file.",buttons: Ext.Msg.OK,icon: Ext.Msg.WARNING});
					return;
				}
				if (node.isLeaf()) node = node.parentNode;
				Ext.Msg.prompt("Config file to create (leave empty for default config file)",node.text + "-",function(btn,cfgname){
					if (btn == 'ok') createNode(node.text + (cfgname!=''?'-':'') + cfgname + ".json");
				});
			}
		},{
			id: "minus",
			handler: function() {
				var node = nav.getSelectionModel().getSelectedNode();
				if (node == null || !node.isLeaf()) {
					Ext.Msg.show({title:"Delete config file",msg:"Select first in the tree the file to delete.",buttons: Ext.Msg.OK,icon: Ext.Msg.INFO});
					return;
				} else if (startstopBtn.getText() == "Stop") {
					Ext.Msg.show({title:"Delete config file",msg:"Stop the service first.",buttons: Ext.Msg.OK,icon: Ext.Msg.INFO});
					return;
				} else {
					var filename = node.text;
					Ext.Msg.confirm("Delete file", "Confirm to permanently delete config file: " + filename,function(btn){
						if (btn != 'yes') return;
						conn.request({
							url: 'deletefile.cgi?'+Ext.urlEncode({name: filename}),
							method: 'GET',
							callback: function(options,success,responseObject) {
								if (responseObject.responseText=="ok\n") {
									//Ext.Msg.show({title: 'Status',msg: 'Config file is now deleted:' + filename,buttons: Ext.Msg.OK, icon: Ext.Msg.INFO});
									node.remove(true);
								} else if (responseObject.responseText=="file not found\n") {
									node.remove(true); // delete a node just created
								} else {
									Ext.Msg.show({title: 'Error',msg: 'Error&nbsp;deleting&nbsp;file&nbsp;' + filename + ':<PRE>' + responseObject.responseText + '</PRE>',buttons: Ext.Msg.OK, icon: Ext.Msg.ERROR});
								}
							}
						});
					});
				}
			}
		}]
	});

	function checkStatus(node) {
		conn.request({
				url: 'status.cgi?'+Ext.urlEncode({name: node.text}),
				method: 'GET',
				callback: function(options,success,responseObject) {
					if (success && responseObject.responseText=="0\n") {
						node.setIcon("images/started.png");
						if (node==nav.getSelectionModel().getSelectedNode()){
							startstopBtn.enable();
							startstopBtn.setText("Stop");
						}
					} else {
						node.setIcon("images/stopped.png");
						if (node==nav.getSelectionModel().getSelectedNode()){
							startstopBtn.enable();
							startstopBtn.setText("Start");
						}
					}
				}
		});
	}

	var conn = new Ext.data.Connection();

    var form = new Ext.Panel({
        baseCls: 'x-plain',
        layout: 'border',
        region: 'center',
        items: [ toolb, texta ]
    });

	new Ext.Viewport({
		layout: 'border',
		items: [ nav, form ]
	});

	//Ext.QuickTips.init();
	nav.getRootNode().expand(true);
 
});
</script>
</body>
</html>

