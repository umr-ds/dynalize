///////////
// Start Script
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.Script = parent.Script || {};
    var ajax = api.Ajax = api.Ajax || {};
    var ui = api.UI = api.UI || {};
	
	var editor;
	var editorSession;
	
	var doc = $(document);

    // Initialisierungsfunktion für jedes Modul
    api.init = function () {
        this.bindUIActions();
		this.initEditor();
    };

    api.bindUIActions = function () {
        ui.bindNav();
		ui.bindContent();
    };
	
	api.initEditor = function() {
		editor = ace.edit("txtScriptContent");
		editorSession = editor.getSession();
		
		editorSession.setMode("ace/mode/python");
		editor.setTheme("ace/theme/clouds");
		editor.setOptions({
			minLines: 30,
			maxLines: 60
		});
		
		editor.setShowPrintMargin(false);
	}

    ui.bindNav = function () {
		$("#aScripts").on("click", function(e) {
			showPage("#divScripts");
			setActiveNav($(this).parent())
			ajax.getScripts();
		});
	};
	
	ui.bindContent = function() {
		doc.on("click", "#tblScripts [id|='delete']", function(e) {
			e.preventDefault();
			
			baseDelete(this, function(uri) {
				ajax.deleteScript(uri);
			});
			
			resetScriptForm();
		});

		doc.on("click", "#tblScripts [id|='copy']", function(e) {
			e.preventDefault();
			
			baseCopy(this, unselectRows, function(msg) {
				editorSession.setValue(msg.data.content);
				$("#txtScriptName").val("Copy of " + msg.data.name)			
			});
		});
				
		doc.on("click", "#tblScripts tr td.clickable", function(e) {
			e.preventDefault();
			
			baseEdit(this, unselectRows, function(msg) {
				editorSession.setValue(msg.data.content);
				$("#txtScriptName").val(msg.data.name)			
			});
		});
		
							
		$("#btnScriptSave").on("click", function(e) {
			e.preventDefault();
			var name = $("#txtScriptName").val();
			var code = editorSession.getValue();
			
			if (name == "") {
				showAlert("danger", "Achtung!", "Das Namensfeld ist zwingend benötigt.");
				return;
			}
			
			var uri = $("#divScripts tr.info").first().data("uri");
			
			if (uri == undefined) {
				ajax.addScript(name, code);
			} else {
				ajax.updateScript(uri, name, code);
			}
			
			resetScriptForm();
		});

		$("#btnScriptCancel").on("click", function(e) {
			e.preventDefault();
			resetScriptForm();
			unselectRows();
		});
	}
	
	ajax.deleteScript = function(url) {
		deleteApi(url, ajax.getScripts);
	}

	ajax.addScript = function(name, content) {
		var data = {
			name : name,
			content : content
		};
		
		addApi(api_prefix + "script", data, ajax.getScripts);
	}

	ajax.updateScript = function(url, name, content) {
		var data = {
			name : name,
			content : content
		};
		
		updateApi(url, data, ajax.getScripts);
	}

	ajax.getScripts = function() {
		getApi(api_prefix + "script", $("#tmplScriptList"), $("#tblScripts tbody"))
	}
	
	
	// Helper functions
	function unselectRows() {
		$("#divScripts tr.info").removeClass("info");
	}
	
	function resetScriptForm() {
		$("#txtScriptName").val("");
		editorSession.setValue("#!/usr/bin/env python");
	}
    
    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.Script.init() });
///////////
// End Script
///////////
