///////////
// Start Worker
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.Worker = parent.Worker || {};
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
		$("#aWorker").on("click", function(e) {
			showPage("#divWorker");
			setActiveNav($(this).parent())
			ajax.getWorker();
		});	
	};
	
	ui.bindContent = function() {

	}

	ajax.getWorker = function() {
		getApi(api_prefix + "worker", $("#tmplWorkerList"), $("#tblWorker tbody"));
	};
	
	// Helper functions
	    
    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.Worker.init() });
///////////
// End Worker
///////////
