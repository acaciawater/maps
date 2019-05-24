/**
 * @author: theo
 */

var overlays = new Set();
var baseMaps;

var storage = sessionStorage; // or localStorage?

function addOverlay(e) {
	overlays.add(e.name);
	storage.setItem('overlays', JSON.stringify(Array.from(overlays)));
}

function removeOverlay(e) {
	overlays.delete(e.name);
	storage.setItem('overlays', JSON.stringify(Array.from(overlays)));
}

function changeBaseLayer(e) {
	storage.setItem("baselayer", e.name);
}

function restoreMap(map) {
	let succes = false;
//	var items = storage.getItem('overlays');
//	if (items) {
//		let names = new Set(JSON.parse(items));
//		names.forEach(function(name) {
//			overlays[name].addTo(map);
//			succes = true;
//		});
//	}
//	else {
//		overlays = new Set();
//	}
	var name = storage.getItem('baselayer');
	if (name) {
		baseMaps[name].addTo(map);
		succes = true;
	}
	return succes;
}

function saveBounds(map) {
	var b = map.getBounds();
	storage.setItem('bounds',b.toBBoxString());
}

function restoreBounds(map) {
	var b = storage.getItem('bounds');
	if (b) {
		corners = b.split(',').map(Number);
		map.fitBounds([[corners[1],corners[0]],[corners[3],corners[2]]]);
		return true;
	}
	return false;
}

var redBullet = L.icon({
    iconUrl: '/static/red_marker16.png',
    iconSize: [12, 12],
    iconAnchor: [6,6],
    popupAnchor: [0, 0],
});

var theMap = null;
var markers = []; // Should be associative array: {} ??

/**
 * Adds a location item (marker) to the map 
 * @param map
 * @param item
 * @returns
 */
function addItemToMap(item, map, urls) {
	let marker = L.marker([item.lat, item.lon],{title:item.name, icon:redBullet});
	markers[item.id] = marker;
	marker.bindPopup("Loading...",{maxWidth: "auto"});
	marker.bindTooltip(item.name,{permanent:true,className:"label",opacity:0.7,direction:"top",offset:[0,-10]});
	marker.on("click", function(e) {
		const popup = e.target.getPopup();
		// retrieve popup content from remote site
	    $.get(urls.popup+item.id)
		    .done(function(data) {
		    	// convert paths like href="/net/.." or src="/static/.." to absolute urls using server url as base
		    	data = data.replace(/(((href|src)=['"])\/)/g,'$2'+urls.server+'/');
		        popup.setContent(data);
		        popup.update();
		    })
		    .fail(function() {
		    	popup.closePopup();
		    });
	});
	return marker.addTo(map);
}

/**
 * Adds location item to list
 * @param item
 * @param list
 * @returns
 */
function addItemToList(item, list) {
	let date = "";
	let value = "";
	if (item.latest) {
		date = new Date(item.latest.time).toLocaleDateString("nl-NL",dateOptions);
		value = `${item.latest.value.toPrecision(3)} ${item.latest.unit}`;
	}
	list.append(`<a class="list-group-item list-group-item-action" 
		href="/chart/${item.id}/" onmouseover="showMarker(${item.id});" onmouseout="hideMarker();">
		${item.name}
		<span class="float-right"><small>${date}</small></span><br>
		<small>${item.description}<span class="float-right">${value}</span></small></a>`);
}

function addItems(map,list,urls) {
	return $.getJSON(urls.items).then(data => {
		$.each(data, (key,item) => {
			addItemToMap(item, map, urls);
			addItemToList(item, list);
		});
		return data;
	});
}

var overlayLayers = [];

function toggleLayer(id) {
	const layer = overlayLayers[id];
	if (layer.options.visible) {
		theMap.remove(layer);
		layer.options.visible = false;
	}
	else {
		theMap.add(layer);
		layer.options.visible = true;
	}
}

async function addOverlays(map, list, layers) {
	overlayLayers = [];
	$.each(layers, (name, layer) => {
		const overlay = L.tileLayer.wms(layer.url, layer);
		const id = overlayLayers.push(overlay);
		map.layerControl.addOverlay(overlay,name);
		if (layer.visible) {
			overlay.addTo(map);
		}
		list.append(`<li class="list-group-item">
			${name}
			<a data-toggle="collapse" href="#leg${id}">
				<i class="fas fa-list float-right" title="toggle legend"></i>
			</a>
			<div class="collapse hide" id="leg${id}">
				<img src="${layer.legend}"></img>
			</div>
		</li>`);
	});
	return overlayLayers;
}

var hilite = null;
var hiliteVisible = false;

function showHilite(marker) {
	
	if (marker == null || theMap == null)
		return;
	
	if (!hilite) {
		hilite= new L.circleMarker(marker.getLatLng(),{radius:20,color:"green"})
			.addTo(theMap);
	}
	else {
		hilite.setLatLng(marker.getLatLng());
		if (!hiliteVisible) {
			theMap.addLayer(hilite);
		}
	}
	hiliteVisible = true;
}

function hideHilite() {
	if (hiliteVisible) {
		hilite.remove();
		hiliteVisible = false;
	}
}

var panTimeoutId = undefined;

function panToMarker(marker) {
	theMap.panTo(marker.getLatLng());
}

function clearPanTimer() {
	window.clearTimeout(panTimeoutId);
	panTimeoutId = undefined;
}

function showMarker(m) {
	marker = markers[m];
	showHilite(marker);
	panTimeoutId = window.setTimeout(panToMarker,1000,marker);
}

function hideMarker(m) {
	hideHilite();
	clearPanTimer();
}

L.Control.LabelControl = L.Control.extend({
    onAdd: function(map) {
    	var container = L.DomUtil.create('div','leaflet-bar leaflet-control leaflet-control-custom');
        var img = L.DomUtil.create('a','fa fa-lg fa-tags',container);
    	img.title = 'Toggle labels';
        img.setAttribute('role','button');
        img.setAttribute('aria-label','Toggle Labels');

    	L.DomEvent.on(container, 'click', function(e) {
        	toggleLabels();
            L.DomEvent.preventDefault();
            L.DomEvent.stopPropagation();
        });
        
        return container;
    },

    onRemove: function(map) {
        // Nothing to do here
    },
    
});

L.control.labelcontrol = function(opts) {
    return new L.Control.LabelControl(opts);
}

var labelsShown = true;

function showLabels() {
	if (!labelsShown) {
		if (markers) {
			markers.forEach(function(marker){
				marker.openTooltip();
			});
		} 
		labelsShown = true;
	}
}

function hideLabels() {
	if (labelsShown) {
		if (markers) {
			markers.forEach(function(marker){
				marker.closeTooltip();
			}); 
		} 
		labelsShown = false;
	}
}

function toggleLabels() {
	if (labelsShown) {
		hideLabels();
	}
	else {
		showLabels();
	}
}

/**
 * Initializes leaflet map
 * @param div where map will be placed
 * @options initial centerpoint and zoomlevel
 * @returns the map
 */
function initMap(div,options) {
	var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		maxZoom: 19,
 		attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
	});
	
	var roads = L.gridLayer.googleMutant({
	    type: 'roadmap' // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
	});

	var satellite = L.gridLayer.googleMutant({
	    type: 'satellite' // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
	});
	
	var topo = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
		attribution: 'Tiles &copy; Esri'
	});
	
	var imagery = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
		attribution: 'Tiles &copy; Esri'
	});
	
	var map = L.map(div,options);

 	baseMaps = {'Openstreetmap': osm, 'Google wegenkaart': roads, 'Google satelliet': satellite, 'ESRI wegenkaart': topo, 'ESRI satelliet': imagery};
	overlayMaps = {};
	map.layerControl = L.control.layers(baseMaps, overlayMaps).addTo(map);

	if (!restoreMap(map)) {
		// use default map
		osm.addTo(map);
	}
	
	restoreBounds(map);

	var control = L.control.labelcontrol({ position: 'topleft' }).addTo(map);

	map.on('baselayerchange',function(e){changeBaseLayer(e);});
 	map.on('overlayadd',function(e){addOverlay(e);});
 	map.on('overlayremove',function(e){removeOverlay(e);});
 	map.on('zoomend',function(){saveBounds(map);});
 	map.on('moveend',function(){saveBounds(map);});
 	
 	return theMap = map;

}
