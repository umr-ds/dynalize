///////////
// Start DataProvider
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.DataProvider = parent.DataProvider || {};
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
		$("#aDataProvider").on("click", function(e) {
			showPage("#divDataProvider");
			setActiveNav($(this).parent())
			ajax.getDataProvider();
			ajax.getDataProvidertype();
		});	
	};
	
	ui.bindContent = function() {
		doc.on("click", "#tblDataProvider [id|='delete']", function(e) {
			e.preventDefault();
			
			baseDelete(this, function(uri) {
				ajax.deleteDataProvider(uri);
			});
		});
		
		doc.on("click", "#tblDataProvider [id|='copy']", function(e) {
			e.preventDefault();
			
			baseCopy(this, unselectRows, function(msg) {
				var data = msg.data;
				
				$("#txtDataProviderName").val("Copy of " + data.name);
				$("#cboDataProviderType").val(data.dataprovider_id);
				$('#txtDataProviderSource').val(data.source);
				$("#txtDataProviderSourcePathFilter").val(data.source_path_filter);
				$("#txtDataProviderSourceFilenameFilter").val(data.source_filename_filter);
				$("#txtDataProviderDestination").val(data.destination);
				
				// S3 specific
				$("#txtDataProviderS3BucketName").val(data.bucket_name);
				$("#txtDataProviderS3AccessKey").val(data.access_key);
				$("#txtDataProviderS3SecretKey").val(data.secret_key);	
			});
		});		

		doc.on("click", "#tblDataProvider tr td.clickable", function(e) {
			e.preventDefault();
			
			baseEdit(this, unselectRows, function(msg) {
				var data = msg.data;
				
				$("#txtDataProviderName").val(data.name);
				$("#cboDataProviderType").val(data.dataprovider_id);
				$('#txtDataProviderSource').val(data.source);
				$("#txtDataProviderSourcePathFilter").val(data.source_path_filter);
				$("#txtDataProviderSourceFilenameFilter").val(data.source_filename_filter);
				$("#txtDataProviderDestination").val(data.destination);
				
				// S3 specific
				$("#txtDataProviderS3BucketName").val(data.bucket_name);
				$("#txtDataProviderS3AccessKey").val(data.access_key);
				$("#txtDataProviderS3SecretKey").val(data.secret_key);				
			});
		});
						
		$("#btnDataProviderSave").on("click", function(e) {
			e.preventDefault();
			
			var data = {
				name : $("#txtDataProviderName").val(),
				dataprovider_id : $("#cboDataProviderType").val() || 0,
				source : $('#txtDataProviderSource').val(),
				source_path_filter : $("#txtDataProviderSourcePathFilter").val(),
				source_filename_filter : $("#txtDataProviderSourceFilenameFilter").val(),
				destination : $("#txtDataProviderDestination").val(),
				bucket_name : $("#txtDataProviderS3BucketName").val(),
				access_key : $("#txtDataProviderS3AccessKey").val(),
				secret_key : $("#txtDataProviderS3SecretKey").val()
			}
						
			if (data.name == "") {
				showAlert("danger", "Achtung!", "Das Namensfeld ist zwingend benötigt.");
				return;
			}
			
			var uri = $("#divDataProvider tr.info").first().data("uri");
			
			if (uri == undefined) {
				addApi(api_prefix + "datadef", data, ajax.getDataProvider);
			} else {
				updateApi(uri, data, ajax.getDataProvider)
			}
			
			resetDataProviderForm();
		});

		$("#btnDataProviderCancel").on("click", function(e) {
			e.preventDefault();
			resetDataProviderForm();
			unselectRows();
		});	
		
		$("#txtDataProviderS3AccessKey").on("keyup", function(e) {
			showKeyWarning();
		});
		
		$("#txtDataProviderS3SecretKey").on("keyup", function(e) {
			showKeyWarning();
		});
						
	}
	
	ajax.deleteDataProvider = function(url) {
		deleteApi(url, ajax.getDataProvider);
	}
	
	ajax.getDataProvider = function() {
		getApi(api_prefix + "datadef", $("#tmplDataProviderList"), $("#tblDataProvider tbody"));
	};
		
	ajax.getDataProvidertype = function() {
		getApi(api_prefix + "dataprovider", $("#tmplDataProviderType"), $("#cboDataProviderType"));
	}
		
	
	// Helper functions
	function resetDataProviderForm() {
		$("#txtDataProviderName").val("");
		$("#cboDataProviderType")[0].selectedIndex = 0;
		$('#txtDataProviderSource').val("");
		$("#txtDataProviderSourcePathFilter").val("");
		$("#txtDataProviderSourceFilenameFilter").val("");
		$("#txtDataProviderDestination").val("");
		
		// S3 specific
		$("#txtDataProviderS3BucketName").val("");
		$("#txtDataProviderS3AccessKey").val("");
		$("#txtDataProviderS3SecretKey").val("");
	}
	
	function unselectRows() {
		$("#divDataProvider tr.info").removeClass("info");
	}
	
	function showKeyWarning() {
		if ($("#txtDataProviderS3AccessKey").val() != "" || $("#txtDataProviderS3SecretKey").val() != "") {
			$("#txtDataProviderS3KeyInfo").show();
		} else {
			$("#txtDataProviderS3KeyInfo").hide();
		}
	}
    
    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.DataProvider.init() });
///////////
// End DataProvider
///////////
