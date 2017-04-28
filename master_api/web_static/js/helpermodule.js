var api_prefix = '/v1/';

$.ajaxSetup({
    contentType: "application/json; charset=utf-8",
    dataType: "json",
	error: defaultAjaxErrorMsg,
    timeout: 30000
});

function defaultAjaxErrorMsg(jqXHR, textStatus, errorThrown) {
	if (jqXHR.responseJSON != null && jqXHR.responseJSON.data != null && jqXHR.responseJSON.data.error != null) {
		errorThrown = jqXHR.responseJSON.data.error;
	} 
	showAlert("danger", jqXHR.status || "", errorThrown || "Unbekannter Fehler");
}


function hidePages() {
	$(".page").hide();
}

function showPage(id) {
	hidePages()
	$(id).show();
}

function getSpinner() {
	return "<i class=\"fa fa-spinner fa-spin fa-lg\"></i>";
}

function setActiveNav(ele) {
	$("nav .active").removeClass("active");
	
	var ele = $(ele)
	ele.addClass("active");
	
	// In case this is a menu entry in a dropdown menu, make sure to mark the parent dropdown element as active as well
	var dropdownParent = ele.closest("li.dropdown");
	
	if (dropdownParent.length > 0) {
		dropdownParent.addClass("active");
	}	
}

function showAlert(type, caption, text) {
	var data = {
		alertType : type,
		alertCaption : caption,
		alertText : text
	};
	var output = Mustache.render($("#tmplAlert").html(), data);
	$(document).scrollTop(0);
	$(output).appendTo("#divAlert").delay(4000).fadeOut(500, function() { $(this).remove() });
}


function deleteApi(url, func, preventAlert) {
	return $.ajax({
		url: url,
		type: 'DELETE',
		success: function (msg) {
			if (preventAlert) 
				showAlert("success", "Gelöscht!", "Löschen erfolgreich.");
				
			if (func != undefined) 
				func();
		}
	});
}

function addApi(url, data, func) {
	return $.ajax({
		url: url,
		type: 'POST',
		data: JSON.stringify(data),
		success: function (msg) {
			showAlert("success", "Angelegt!", "Anlegen erfolgreich.");
			if (func != undefined) 
				func();
		}
	});
}

function updateApi(url, data, func) {
	return $.ajax({
		url: url,
		type: 'PUT',
		data: JSON.stringify(data),
		success: function (msg) {
			showAlert("success", "Aktualisiert!", "Aktualisierung erfolgreich.");
			if (func != undefined) 
				func();
		}
	});
}

function getApi(url, template, destination, func) {
	destination.html("<tr><td>" + getSpinner() + "</td><td class=\"col-md-2\"></tr>");
	
	return $.ajax({
		url: url,
		success: function (msg) {
			var output = Mustache.render(template.html(), msg);
			destination.html(output);
			
			if (func != undefined) 
				func(msg);
		}
	});
}

function baseEdit(elem, unselectFunc, funcSuccess) {
	var parent = $(elem).parent();
	var uri = parent.data().uri;
	
	if (uri == undefined)
		return
		
	unselectFunc();
	parent.addClass("info");
	
	$.ajax({
		url: uri,
		success: function (msg) {
			funcSuccess(msg);
		}
	});
}

function baseDelete(elem, funcOnConfirm) {
	var elem = $(elem);
	var uri = elem.data().uri;
	
	if (uri == undefined)
		return		
	
	elem.confirmation({
		placement: 'top',
		btnOkLabel: 'Löschen',
		btnCancelLabel: 'Abbrechen',
		title: 'Sicher löschen?',
		onConfirm: function() {
				funcOnConfirm(uri);
			}
	});
	
	elem.confirmation('show');
}

function baseCopy(elem, unselectFunc, funcSuccess) {
	var elem = $(elem);
	var uri = elem.data().uri;
	
	if (uri == undefined)
		return
	
	unselectFunc();
	
	$.ajax({
		url: uri,
		success: function (msg) {
			funcSuccess(msg);
		}
	});
}

