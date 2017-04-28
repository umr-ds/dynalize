///////////
// Start Cloud
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.Cloud = parent.Cloud || {};
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
		$("#aClouds").on("click", function(e) {
			showPage("#divClouds");
			setActiveNav($(this).parent())
			ajax.getCloud();
			ajax.getCloudtype();
			ajax.getLayers();
		});
		
		$("#aInstances").on("click", function(e) {
			showPage("#divInstances");
			setActiveNav($(this).parent())
			ajax.getInstances();
		});		
	};
	
	ui.bindContent = function() {
		doc.on("click", "#tblClouds [id|='delete']", function(e) {
			e.preventDefault();
			
			baseDelete(this, function(uri) {
				ajax.deleteCloud(uri);
			});
		});
		
		doc.on("click", "#tblInstances [id|='stop']", function(e) {
			e.preventDefault();
			
			var elem = $(this);
			var uri = elem.data().uri;
			
			if (uri == undefined)
				return		
			
			elem.confirmation({
				placement: 'top',
				btnOkLabel: 'Stoppen',
				btnCancelLabel: 'Abbrechen',
				title: 'Sicher stoppen?',
				onConfirm: function() {
						$.ajax({
							type: 'POST',
							url: uri + "/stop",
							success: function (msg) {
								showAlert("success", "Gestoppt!", "Die Instanz wird gestoppt.");
								ajax.getInstances();
							}
						});
					}
			});
			
			elem.confirmation('show');
		});	

		doc.on("click", "#tblInstances [id|='terminate']", function(e) {
			e.preventDefault();
			
			var elem = $(this);
			var uri = elem.data().uri;
			
			if (uri == undefined)
				return		
			
			elem.confirmation({
				placement: 'top',
				btnOkLabel: 'Terminieren',
				btnCancelLabel: 'Abbrechen',
				title: 'Sicher terminieren?',
				onConfirm: function() {
					$.ajax({
						type: 'POST',
						url: uri + "/terminate",
						success: function (msg) {
							showAlert("success", "Terminiert!", "Die Instanz wird terminiert.");
							ajax.getInstances();
						}
					});
				}
			});
			
			elem.confirmation('show');
		});	
		
		doc.on("click", "#tblInstances [id|='start']", function(e) {
			e.preventDefault();
			
			var elem = $(this);
			var uri = elem.data().uri;
			
			if (uri == undefined)
				return		
			
			elem.confirmation({
				placement: 'top',
				btnOkLabel: 'Starten',
				btnCancelLabel: 'Abbrechen',
				title: 'Sicher starten?',
				onConfirm: function() {
					$.ajax({
						type: 'POST',
						url: uri + "/start",
						success: function (msg) {
							showAlert("success", "Gestartet!", "Die Instanz wird gestartet.");
							ajax.getInstances();
						}
					});
				}
			});
			
			elem.confirmation('show');
		});
		
		doc.on("click", "#tblInstances [id|='snapshot']", function(e) {
			e.preventDefault();
			
			var elem = $(this);
			var uri = elem.data().uri;
			
			if (uri == undefined)
				return		
			
			elem.confirmation({
				placement: 'top',
				btnOkLabel: 'Erstellen',
				btnCancelLabel: 'Abbrechen',
				title: 'Snapshot erstellen und als Standard für zukünftige Instanzen verwenden?',
				onConfirm: function() {
					$.ajax({
						type: 'POST',
						url: uri + "/createsnapshot",
						success: function (msg) {
							showAlert("success", "Erstellung gestartet!", "Der Snapshot wird erstellt.");
							ajax.getInstances();
						}
					});
				}
			});
			
			elem.confirmation('show');
		});

		doc.on("click", "#tblClouds [id|='start']", function(e) {
			e.preventDefault();
			
			var elem = $(this);
			var uri = elem.data().uri;
			var id = elem.data().id;
			
			if (uri == undefined)
				return;
			
			// Remove all popovers 
			$(".popover").popover("destroy");

			msg = {
				data : {
					clouddef_id : id
				}
			};
			
			// see: http://stackoverflow.com/questions/12128425/contain-form-within-a-bootstrap-popover
			elem.popover({ 
				placement : "left",
				trigger : "click",
				html : true,
				title: "Details zum Start",
				content: function() {
				  return Mustache.render($("#tmplCloudInstancePopover").html(), msg);
				}
			});
			
			elem.popover("show");
			
			$("#btnCloudStartInstance_" + id).on("click", function(e) {
				var numberOfInstances = $("#txtCloudInstanceCount_" + id).val();
				var instanceType = $("#txtCloudInstanceType_" + id).val();

				if (numberOfInstances != parseInt(numberOfInstances, 10)) {
					showAlert("danger", "Fehler", "Die Anzahl der Instanzen muss ganzzahlig sein!");
					return;
				}
				
				if (instanceType == "") {
					instanceType = null;
				}
				
				data = {
					number_of_instances : numberOfInstances,
					instance_type : instanceType
				};
				
				$.ajax({
					type: 'POST',
					data : JSON.stringify(data),
					url: uri + "/startinstance",
					success: function() {
						elem.popover("destroy");
					}
				});
				
			});
		});			

		doc.on("click", "#tblClouds [id|='copy']", function(e) {
			e.preventDefault();
			
			baseCopy(this, unselectRows, function(msg) {
				var data = msg.data;
				
				$("#txtCloudName").val(data.name)
				$("#cboCloudType").val(data.cloudprovider_id)
				$('#txtCloudEC2BaseAMI').val(data.base_ami);
				$("#txtCloudEC2Key").val(data.keypair);
				$("#txtCloudEC2SecurityGroup").val(data.security_group);
				$("#txtCloudEC2SubnetId").val(data.subnet);
				$("#txtCloudEC2AccessKey").val(data.access_key);
				$("#txtCloudEC2SecretKey").val(data.secret_key);
				$("#cboCloudVirtualDeviceLayer").val(data.virtual_device_layer_id);
				$("#cboCloudTestLayer").val(data.test_layer_id);
				$("#txtCloudClientStartupParameters").val(data.client_startup_parameters);
			});
		});		

		doc.on("click", "#tblClouds tr td.clickable", function(e) {
			e.preventDefault();
			
			baseEdit(this, unselectRows, function(msg) {
				var data = msg.data;
				
				$("#txtCloudName").val(data.name)
				$("#cboCloudType").val(data.cloudprovider_id)
				$('#txtCloudEC2BaseAMI').val(data.base_ami);
				$("#txtCloudEC2Key").val(data.keypair);
				$("#txtCloudEC2SecurityGroup").val(data.security_group);
				$("#txtCloudEC2SubnetId").val(data.subnet);
				$("#txtCloudEC2AccessKey").val(data.access_key);
				$("#txtCloudEC2SecretKey").val(data.secret_key);
				$("#cboCloudVirtualDeviceLayer").val(data.virtual_device_layer_id);
				$("#cboCloudTestLayer").val(data.test_layer_id);
				$("#txtCloudClientStartupParameters").val(data.client_startup_parameters);
				$("#txtCloudSnapshotId").val(data.snapshot_id);
				$("#txtCloudSnapshotImageId").val(data.snapshot_image_id);
			});
		});
						
		$("#btnCloudSave").on("click", function(e) {
			e.preventDefault();
			
			var data = {
				name : $("#txtCloudName").val(),
				cloudprovider_id : $("#cboCloudType").val() || 0,
				base_ami : $('#txtCloudEC2BaseAMI').val(),
				keypair : $("#txtCloudEC2Key").val(),
				security_group : $("#txtCloudEC2SecurityGroup").val(),
				subnet : $("#txtCloudEC2SubnetId").val(),
				access_key : $("#txtCloudEC2AccessKey").val(),
				secret_key : $("#txtCloudEC2SecretKey").val(),
				virtual_device_layer_id : $("#cboCloudVirtualDeviceLayer").val() || 0,
				test_layer_id : $("#cboCloudTestLayer").val() || 0,
				client_startup_parameters : $("#txtCloudClientStartupParameters").val()
			}
						
			if (data.name == "") {
				showAlert("danger", "Achtung!", "Das Namensfeld ist zwingend benötigt.");
				return;
			}
			
			var uri = $("#divClouds tr.info").first().data("uri");
			
			if (uri == undefined) {
				addApi(api_prefix + "clouddef", data, ajax.getCloud);
			} else {
				updateApi(uri, data, ajax.getCloud)
			}
			
			resetCloudForm();
		});

		$("#btnCloudCancel").on("click", function(e) {
			e.preventDefault();
			resetCloudForm();
			unselectRows();
		});	
		
		$("#txtCloudEC2AccessKey").on("keyup", function(e) {
			showKeyWarning();
		});
		
		$("#txtCloudEC2SecretKey").on("keyup", function(e) {
			showKeyWarning();
		});
		
		$("#btnInstanceRefresh").on("click", function(e) {
			$.ajax({
				url: api_prefix + "clouddef",
				success: function (msg) {
					$.each(msg.data, function(key, value) {
						$.ajax({
							type: 'POST',
							url: value.uri + "/refreshinstances"
						});
					});
					
					ajax.getInstances();
				}
			});
		});		
		
		$("#btnCloudSnapshotCreate").on("click", function(e) {
			e.preventDefault();
			$.ajax({
				url: api_prefix + "clouddef",
				success: function (msg) {
					$.each(msg.data, function(key, value) {
						$.ajax({
							type: 'POST',
							url: value.uri + "/createsnapshot"
						});
					});
					
					ajax.getInstances();
				}
			});
		});		

		$("#btnCloudStartDeploymentInst").on("click", function(e) {
			e.preventDefault();
			$.ajax({
				url: api_prefix + "clouddef",
				success: function (msg) {
					$.each(msg.data, function(key, value) {
						$.ajax({
							type: 'POST',
							url: value.uri + "/startdeploymentinstance"
						});
					});
					
					ajax.getInstances();
				}
			});
		});		
	}
	
	ajax.deleteCloud = function(url) {
		deleteApi(url, ajax.getCloud);
	}
	
	ajax.getCloud = function() {
		getApi(api_prefix + "clouddef", $("#tmplCloudList"), $("#tblClouds tbody"));
	};
	
	ajax.getLayers = function() {
		getApi(api_prefix + "layer", $("#tmplLayers"), $("#cboCloudVirtualDeviceLayer"));
		getApi(api_prefix + "layer", $("#tmplLayers"), $("#cboCloudTestLayer"));
	}		
	
	ajax.getInstances = function() {
		getApi(api_prefix + "instance", $("#tmplCloudInstanceList"), $("#tblInstances tbody"));
	};
	
	ajax.getCloudtype = function() {
		getApi(api_prefix + "cloudprovider", $("#tmplCloudtype"), $("#cboCloudType"));
	}
		
	
	// Helper functions
	function resetCloudForm() {
		$("#txtCloudName").val("");
		$("#cboCloudType")[0].selectedIndex = 0;
		$('#txtCloudEC2BaseAMI').val("");
		$("#txtCloudEC2Key").val("");
		$("#txtCloudEC2SecurityGroup").val("");
		$("#txtCloudEC2SubnetId").val("");
		$("#txtCloudEC2AccessKey").val("");
		$("#txtCloudEC2SecretKey").val("");
		$("#cboCloudVirtualDeviceLayer")[0].selectedIndex = 0
		$("#cboCloudTestLayer")[0].selectedIndex = 0
		$("#txtCloudSnapshotId").val("");
		$("#txtCloudSnapshotImageId").val("");
	}
	
	function unselectRows() {
		$("#divClouds tr.info").removeClass("info");
	}
	
	function showKeyWarning() {
		if ($("#txtCloudEC2AccessKey").val() != "" || $("#txtCloudEC2SecretKey").val() != "") {
			$("#txtCloudEC2KeyInfo").show();
		} else {
			$("#txtCloudEC2KeyInfo").hide();
		}
	}
    
    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.Cloud.init() });
///////////
// End Cloud
///////////
