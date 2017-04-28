///////////
// Start Main
///////////

// see http://www.adequatelygood.com/JavaScript-Module-Pattern-In-Depth.html
var Module = (function(parent, $) {
    var api = parent.Main = parent.Main || {};
    var ajax = api.Ajax = api.Ajax || {};
    var menu = api.Menu = api.Menu || {};
    var dialog = api.Dialog = api.Dialog || {};
	
	var ws = null;

    // Initialisierungsfunktion für jedes Modul
    api.init = function () {
        this.bindUIActions();
    };

    api.bindUIActions = function () {
		bindLogFooter();
		setupWebsocket();
		
		$("#mainLogExpand").on("click", function(e) {			
			if ($("footer").height() >= ($(window).height() * 0.5)) {
				$("footer").height(30).resize();
				$("#mainLogExpand i").removeClass("fa-compress").addClass("fa-expand");
			} else {
				$("footer").height($(window).height() * 0.6).resize();
				$("#mainLogExpand i").removeClass("fa-expand").addClass("fa-compress");
			}
			$("body").css("margin-bottom", $("footer").height());
			$("footer .container").height($("footer").height());
		});
		
		$("#mainLogClear").on("click", function(e) {
			$("footer .container").html("");
		});
    };

	
	function setupWebsocket() {
		// see: http://stackoverflow.com/questions/10406930/how-to-construct-a-websocket-uri-relative-to-the-page-uri
		var loc = window.location, websocketUri;
		
		if (loc.protocol === "https:") {
			websocketUri = "wss:";
		} else {
			websocketUri = "ws:";
		}
		websocketUri += "//" + loc.host + "/ws/";
		
		ws = new ReconnectingWebSocket(websocketUri);
		
		ws.onmessage = function(ev) {
			addToFooterLog(ev.data)
		};
		
		ws.onopen = function(event){
			addToFooterLog("Connected to WebSocket!");
			sendKeepAlive();
		};
		
		ws.onclose = function(event) {
			addToFooterLog("WebSocket closed!");
			ws = null;
		};
	}
	
	function sendKeepAlive() {
		if (ws != null) {
			ws.send("KeepAlive");
			
			setTimeout(function () {
				sendKeepAlive();
			}, 60000);
		}
    }
	
	function addToFooterLog(msg) {
		var container = $("footer .container");
		
		if (msg.indexOf("ERROR") > -1) {
			container.append("<div style='color: red'>" + msg + "<div>");
		} else if (msg.indexOf("WARNING") > -1) {
			container.append("<div style='color: darkorange'>" + msg + "<div>");
		} else {
			container.append("<div>" + msg + "<div>");
		}
		container.scrollTop(container[0].scrollHeight);
	}
	
	function bindLogFooter() {
		// see: http://stackoverflow.com/questions/9486788/jquery-ui-resizable-simple-fixed-footer
		$(function () {
			$('footer').resizable({
			 handles: 'n, s',	// only up and down
			 stop : function(event, ui) {
				// Change body margin so there's no "hidden" content
				$("body").css("margin-bottom", $(this).height());
				$("footer .container").height($(this).height());
			 }
			}).bind('resize', function(){
				$(this).css("top", "auto");
			});
			
			// Make sure container height is identical to footer height on init
			$("footer .container").height($("footer").height())
		});	
	}
    
    return parent;
}(Module || {}, jQuery));

// Wenn das Dokument fertig initialisiert wurde, das Modul initialisieren
$(function () { Module.Main.init() });
///////////
// End Main
///////////
