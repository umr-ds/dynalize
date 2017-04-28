///////////
// Start Layer
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.Layer = parent.Layer || {};
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
		editor = ace.edit("txtLayerContent");
		editorSession = editor.getSession();
		
		editorSession.setMode("ace/mode/dockerfile");
		editor.setTheme("ace/theme/clouds");
		editor.setOptions({
			minLines: 30,
			maxLines: 60
		});
		
		editor.setShowPrintMargin(false);
	}

    ui.bindNav = function () {
		$("#aLayers").on("click", function(e) {
			showPage("#divLayers");
			setActiveNav($(this).parent())
			ajax.getLayer();
		});
	};
	
	ui.bindContent = function() {
		doc.on("click", "#tblLayers [id|='delete']", function(e) {
			e.preventDefault();
			
			baseDelete(this, function(uri) {
				ajax.deleteLayer(uri);
			});
			
			resetLayerForm();
		});

		doc.on("click", "#tblLayers [id|='copy']", function(e) {
			e.preventDefault();
			
			baseCopy(this, unselectRows, function(msg) {
				// TODO: Merge with edit handler!
				editorSession.setValue(msg.data.content);
				$("#txtLayerName").val("Copy of " + msg.data.name)
				$("#txtLayerTag").val(msg.data.tag)
				$('#cboLayerParent').val(msg.data.parent_id || 0);
				$("#cboLayerParent").change();			
			});
		});		

		doc.on("click", "#tblLayers tr td.clickable", function(e) {
			e.preventDefault();
			
			baseEdit(this, unselectRows, function(msg) {
				editorSession.setValue(msg.data.content);
				$("#txtLayerName").val(msg.data.name)
				$("#txtLayerTag").val(msg.data.tag)
				$('#cboLayerParent').val(msg.data.parent_id || 0);
				$("#cboLayerParent").change();			
			});
		});
						
		$("#btnLayerSave").on("click", function(e) {
			e.preventDefault();
			var name = $("#txtLayerName").val();
			var tag = $("#txtLayerTag").val();
			var code = editorSession.getValue();
			var parent = $('#cboLayerParent').val() || 0;
			
			if (name == "") {
				showAlert("danger", "Achtung!", "Das Namensfeld ist zwingend benötigt.");
				return;
			}
			
			var uri = $("#divLayers tr.info").first().data("uri");
			
			if (uri == undefined) {
				ajax.addLayer(name, tag, code, parent);
			} else {
				ajax.updateLayer(uri, name, tag, code, parent);
			}
			
			resetLayerForm();
		});

		$("#btnLayerCancel").on("click", function(e) {
			e.preventDefault();
			resetLayerForm();
			unselectRows();
		});
			
		$("#cboLayerParent").on("change", function(e) {
			e.preventDefault();
			
			var uri = $("#cboLayerParent :selected").data("uri");

			if (uri == undefined) {
				$("#ulLayerTree").html("<li>(Aktueller Layer)</li>");
				return;
			}
			
			$("#ulLayerTree").html(getSpinner());
			
			$.ajax({
				url: uri + "/tree",
				success: function (msg) {
					var output = Mustache.render($("#tmplLayerTree").html(), msg);
					output = output + "<li>(Aktueller Layer)</li>";
					$("#ulLayerTree").html(output);
				}
			});
		});
	}
	
	ajax.deleteLayer = function(url) {
		deleteApi(url, ajax.getLayer);
	}

	ajax.addLayer = function(name, tag, content, parent_id) {
		var data = {
			name : name,
			tag : tag,
			content : content,
			parent_id : parent_id
		};
		
		addApi(api_prefix + "layer", data, ajax.getLayer);
	}

	ajax.updateLayer = function(url, name, tag, content, parent_id) {
		var data = {
			name : name,
			tag : tag,
			content : content,
			parent_id : parent_id
		};
		
		updateApi(url, data, ajax.getLayer);
	}

	ajax.getLayer = function() {
		getApi(api_prefix + "layer", $("#tmplLayerList"), $("#tblLayers tbody"), function(msg) {
			var output = Mustache.render($("#tmplLayers").html(), msg);
			output = "<option value=\"0\">(Kein)</option>" + output;
			$("#cboLayerParent").html(output);
		});
	}

	// Helper functions
	function resetLayerForm() {
		$("#txtLayerName").val("");
		$("#txtLayerTag").val("");
		$("#cboLayerParent").val(0);
		editorSession.setValue("");
	}
	
	function unselectRows() {
		$("#divLayers tr.info").removeClass("info");
	}

    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.Layer.init() });
///////////
// End Layer
///////////
