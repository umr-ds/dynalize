///////////
// Start Task
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.Task = parent.Task || {};
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
		$("#aTasks").on("click", function(e) {
			showPage("#divTasks");
			setActiveNav($(this).parent())
			ajax.getTask();
		});	
	};
	
	ui.bindContent = function() {
		doc.on("click", "#tblTasks [id|='delete']", function(e) {
			e.preventDefault();
			
			baseDelete(this, function(uri) {
				ajax.deleteTask(uri);
			});
		});	


		doc.on("click", "#tblTasks tr td.clickable", function(e) {
			e.preventDefault();
			
			var parent = $(this).parent();
			var taskid = parent.data().taskid;

			if (taskid == undefined)
				return
				
			$("#taskdetails_" + taskid).toggle();			
		});
		
		doc.on("click", "#btnTaskDeleteAll", function(e) {
			e.preventDefault;
			
			elem = $("#btnTaskDeleteAll");
			
			elem.confirmation({
				placement: 'top',
				btnOkLabel: 'Alle löschen',
				btnCancelLabel: 'Abbrechen',
				title: 'Sicher löschen?',
				onConfirm: function() {
						var ajaxCalls = [];
						
						$("#tblTasks tr").each(function(key, val) { 
							var uri = $(val).data().uri;
							
							if (uri == undefined)
								return
								
							ajaxCalls.push(deleteApi(uri));
						});
						
						// see: http://stackoverflow.com/questions/5627284/pass-in-an-array-of-deferreds-to-when
						$.when.apply($, ajaxCalls).done(function() {
							showAlert("success", "Gelöscht!", "Löschen erfolgreich.");
							ajax.getTask();
						});
					}
			});
	
			elem.confirmation('show');
		});
		
		doc.on("click", "#btnTaskCollapseAll", function(e) {
			$("tr[id^=taskdetails_").hide();
		});
		
		doc.on("click", "#btnTaskExpandAll", function(e) {
			$("tr[id^=taskdetails_").show();
		});		
		
	}
	
	ajax.deleteTask = function(url) {
		deleteApi(url, ajax.getTask);
	}
	
	ajax.getTask = function() {
		getApi(api_prefix + "task", $("#tmplTaskList"), $("#tblTasks tbody"));
	};
	
	// Helper functions

	    
    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.Task.init() });
///////////
// End Task
///////////
