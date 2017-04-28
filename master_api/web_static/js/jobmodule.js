///////////
// Start Job
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.Job = parent.Job || {};
    var ajax = api.Ajax = api.Ajax || {};
    var ui = api.UI = api.UI || {};
		
	var doc = $(document);

    // Initialisierungsfunktion für jedes Modul
    api.init = function () {
        this.bindUIActions();
    };

    api.bindUIActions = function () {
        ui.bindNav();
		ui.bindContent();
    };
	

    ui.bindNav = function () {
		$("#aJobs").on("click", function(e) {
			showPage("#divJobs");
			setActiveNav($(this).parent())
			ajax.getJob();
			ajax.getDataProviders();
			ajax.getClouds();
			ajax.getLayers();
			ajax.getScripts();
		});	
	};
	
	ui.bindContent = function() {
		doc.on("click", "#tblJobs [id|='start']", function(e) {
			e.preventDefault();
			
			var elem = $(this);
			var uri = elem.data().uri;
			
			if (uri == undefined)
				return;			
			
			$.ajax({
				type: 'POST',
				url: uri + "/execute",
				success: function() {
					showAlert("success", "Started!", "Job wird ausgeführt!");
				}
			});
		});
		
		doc.on("click", "#tblJobs [id|='delete']", function(e) {
			e.preventDefault();
			
			baseDelete(this, function(uri) {
				ajax.deleteJob(uri);
			});
		});
		
		doc.on("click", "#tblJobs [id|='copy']", function(e) {
			e.preventDefault();
			
			baseCopy(this, unselectRows, function(msg) {
				var data = msg.data;
				
				$("#txtJobName").val("Copy of " + data.name);
				$("#cboJobCloud").val(data.clouddef_id || 0);
				$("#cboJobRunLayer").val(data.run_layer_id || 0);
				$("#cboJobScript").val(data.script_id || 0);
				$("#cboJobSourceDataProvider").val(data.source_datadef_id || 0);
				$("#cboJobDestinationDataProvider").val(data.destination_datadef_id || 0)
				$("#txtJobTaskTimeout").val(data.task_timeout);		
			});
		});		

		doc.on("click", "#tblJobs tr td.clickable", function(e) {
			e.preventDefault();
			
			baseEdit(this, unselectRows, function(msg) {
				var data = msg.data;
				
				$("#txtJobName").val(data.name);
				$("#cboJobCloud").val(data.clouddef_id || 0);
				$("#cboJobRunLayer").val(data.run_layer_id || 0);
				$("#cboJobScript").val(data.script_id || 0);
				$("#cboJobSourceDataProvider").val(data.source_datadef_id || 0);
				$("#cboJobDestinationDataProvider").val(data.destination_datadef_id || 0)
				$("#txtJobTaskTimeout").val(data.task_timeout);				
			});
		});
						
		$("#btnJobSave").on("click", function(e) {
			e.preventDefault();
			
			var data = {
				name : $("#txtJobName").val(),
				clouddef_id : $("#cboJobCloud").val() || 0,
				run_layer_id : $('#cboJobRunLayer').val() || 0,
				script_id : $("#cboJobScript").val() || 0,
				source_datadef_id : $("#cboJobSourceDataProvider").val() || 0,
				destination_datadef_id : $("#cboJobDestinationDataProvider").val() || 0,
				task_timeout : $("#txtJobTaskTimeout").val()
			}
						
			if (data.name == "") {
				showAlert("danger", "Achtung!", "Das Namensfeld ist zwingend benötigt.");
				return;
			}
			
			var uri = $("#divJobs tr.info").first().data("uri");
			
			if (uri == undefined) {
				addApi(api_prefix + "job", data, ajax.getJob);
			} else {
				updateApi(uri, data, ajax.getJob)
			}
			
			resetJobForm();
		});

		$("#btnJobCancel").on("click", function(e) {
			e.preventDefault();
			resetJobForm();
			unselectRows();
		});							
	}
	
	ajax.deleteJob = function(url) {
		deleteApi(url, ajax.getJob);
	}
	
	ajax.getJob = function() {
		getApi(api_prefix + "job", $("#tmplJobList"), $("#tblJobs tbody"));
	};
		
	ajax.getDataProviders = function() {
		getApi(api_prefix + "datadef", $("#tmplDataProviders"), $("#cboJobSourceDataProvider"));
		getApi(api_prefix + "datadef", $("#tmplDataProviders"), $("#cboJobDestinationDataProvider"));
	}
	
	ajax.getClouds = function() {
		getApi(api_prefix + "clouddef", $("#tmplCloudtype"), $("#cboJobCloud"));
	}

	ajax.getLayers = function() {
		getApi(api_prefix + "layer", $("#tmplLayers"), $("#cboJobRunLayer"));
	}	
	
	ajax.getScripts = function() {
		getApi(api_prefix + "script", $("#tmplScripts"), $("#cboJobScript"));
	}	
	
	// Helper functions
	function resetJobForm() {
		$("#txtJobName").val("");
		$("#cboJobCloud")[0].selectedIndex = 0;
		$("#cboJobRunLayer")[0].selectedIndex = 0;
		$("#cboJobScript")[0].selectedIndex = 0;
		$("#cboJobSourceDataProvider")[0].selectedIndex = 0;
		$("#cboJobDestinationDataProvider")[0].selectedIndex = 0;
		$("#txtJobTaskTimeout").val("600");
	}
	
	function unselectRows() {
		$("#divJobs tr.info").removeClass("info");
	}
	    
    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.Job.init() });
///////////
// End Job
///////////
