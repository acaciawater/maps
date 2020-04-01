/**
 * @author: theo
 */

var baseMaps = {}

var storage = sessionStorage // or localStorage?

function changeBaseLayer (e) {
  storage.setItem('baselayer', e.name)
}

function restoreMap (map) {
  let succes = false
  var name = storage.getItem('baselayer')
  if (name) {
	let bm = baseMaps[name] 
    if (bm) {
    	bm.addTo(map)
        succes = true
    }
  }
  return succes
}

function saveBounds (map) {
  const b = map.getBounds()
  const key = `bounds${map.id}`
  storage.setItem(key, b.toBBoxString())
}

function restoreBounds (map) {
  const key = `bounds${map.id}`
  const b = storage.getItem(key)
  if (b) {
    const corners = b.split(',').map(Number)
    map.fitBounds([[corners[1], corners[0]], [corners[3], corners[2]]])
    return true
  }
  return false
}

var redBullet = L.icon({
  iconUrl: '/static/red_marker16.png',
  iconSize: [12, 12],
  iconAnchor: [6, 6],
  popupAnchor: [0, 0]
})

var theMap = null
var markers = [] // Should be associative array: {} ??

/**
 * Adds a location item (marker) to the map
 * @param map
 * @param item
 * @returns
 */
function addItemToMap (item, map, urls) {
  const marker = L.marker([item.lat, item.lon], { title: item.name, icon: redBullet })
  markers[item.id] = marker
  marker.bindPopup('Loading...', { maxWidth: 'auto' })
  marker.bindTooltip(item.name, { permanent: true, className: 'label', opacity: 0.7, direction: 'top', offset: [0, -10] })
  marker.on('click', function (e) {
    const popup = e.target.getPopup()
    // retrieve popup content from remote site
    $.get(urls.popup + item.id)
      .done(function (data) {
        // convert paths like href="/net/.." or src="/static/.." to absolute urls using server url as base
        data = data.replace(/(((href|src)=['"])\/)/g, '$2' + urls.server + '/')
        popup.setContent(data)
        popup.update()
      })
      .fail(function () {
        popup.closePopup()
      })
  })
  return marker.addTo(map)
}

/**
 * Adds location item to list
 * @param item
 * @param list
 * @returns
 */
function addItemToList (item, list) {
  let date = ''
  let value = ''
  if (item.latest) {
    date = new Date(item.latest.time).toLocaleDateString('nl-NL', dateOptions)
    value = `${item.latest.value.toPrecision(3)} ${item.latest.unit}`
  }
  list.append(`<a class="list-group-item list-group-item-action" 
    href="/chart/${item.id}/" onmouseover="showMarker(${item.id});" onmouseout="hideMarker();">
    ${item.name}
    <span class="float-right"><small>${date}</small></span><br>
    <small>${item.description}<span class="float-right">${value}</span></small></a>`)
}

function addItems (map, list, urls) {
  return $.getJSON(urls.items).then(data => {
    const bounds = new L.LatLngBounds()
    $.each(data, (key, item) => {
      const marker = addItemToMap(item, map, urls)
      bounds.extend(marker.getLatLng())
      addItemToList(item, list)
    })
    map.fitBounds(bounds)
    return data
  })
}

var overlayLayers = []
const iconVisible = 'far fa-check-square'
const iconInvisible = 'far fa-square'

function reorderOverlays (layers) {
  // show layers in proper order on map
  layers.forEach(layer => {
    if (layer.options.visible) {
      layer.bringToFront()
    }
  })
}

function sortOverlays (layers, keys) {
  // sort overlay layers by displayName using ordered array keys and display on map
  reorderOverlays(layers.sort((a, b) => {
    const indexA = keys.indexOf(a.options.displayName)
    const indexB = keys.indexOf(b.options.displayName)
    return indexA > indexB ? 1 : indexA < indexB ? -1 : 0
  }))
}

function toggleLayer (event) {
  const icon = event.target
  const legend = $(icon).next()
  const name = legend.text()
  const layer = overlayLayers.find(o => o.options.displayName === name)
  if (layer.options.visible) {
    theMap.removeLayer(layer)
    layer.options.visible = false
    icon.className = icon.className.replace(iconVisible, iconInvisible)
    legend.next('.collapse').collapse('hide')
  } else {
    theMap.addLayer(layer)
    layer.options.visible = true
    icon.className = icon.className.replace(iconInvisible, iconVisible)
    legend.next('.collapse').collapse('show')
  }
  reorderOverlays(overlayLayers)
  // inform backend about visibility change
  $.post('toggle/', JSON.stringify([name]))
}

async function addOverlay (map, layer) {
  if (layer) {
    const overlay = L.tileLayer.betterWms(layer.url, layer)
    if (layer.visible) {
      overlay.addTo(map)
    }
    return overlay
  }
}

async function addOverlays (map, list, layers) {
  return Object.keys(layers).map(name => {
    const layer = layers[name]
    return addOverlay(map, layer).then(overlay => {
      const id = overlayLayers.push(overlay) - 1
      const icon = layer.visible ? iconVisible : iconInvisible
      let item = `<li id=item_${id} class="list-group-item">
        <i class="statusicon pr-2 pl-0 pt-1 ${icon} float-left" onclick="toggleLayer(event)"></i>
        <div data-toggle="collapse" href="#legend_${id}">${name}</div>`
      if (layer.downloadUrl) {
        item += `<a href="${layer.downloadUrl}"><i class="fas fa-file-download float-right" title="download"></i></a>`
      }
      item += `<div class="collapse" id="legend_${id}"><img src="${layer.legend}"></img></div></li>`
      list.append(item)
    })
  })
}

var hilite = null
var hiliteVisible = false

function showHilite (marker) {
  if (marker == null || theMap == null) { return }

  if (!hilite) {
    hilite = new L.circleMarker(marker.getLatLng(), { radius: 20, color: 'green' })
      .addTo(theMap)
  } else {
    hilite.setLatLng(marker.getLatLng())
    if (!hiliteVisible) {
      theMap.addLayer(hilite)
    }
  }
  hiliteVisible = true
}

function hideHilite () {
  if (hiliteVisible) {
    hilite.remove()
    hiliteVisible = false
  }
}

function panToMarker (marker) {
  theMap.panTo(marker.getLatLng())
}

var panTimeoutId

function clearPanTimer () {
  window.clearTimeout(panTimeoutId)
  panTimeoutId = undefined
}

function showMarker (m) {
  const marker = markers[m]
  showHilite(marker)
  panTimeoutId = window.setTimeout(panToMarker, 1000, marker)
}

function hideMarker () {
  hideHilite()
  clearPanTimer()
}

L.Control.LabelControl = L.Control.extend({
  onAdd: function (map) {
    var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom')
    var img = L.DomUtil.create('a', 'fa fa-lg fa-tags', container)
    img.title = 'Toggle labels'
    img.setAttribute('role', 'button')
    img.setAttribute('aria-label', 'Toggle Labels')

    L.DomEvent.on(container, 'click', function (e) {
      toggleLabels()
      L.DomEvent.preventDefault()
      L.DomEvent.stopPropagation()
    })

    return container
  },

  onRemove: function (map) {
    // Nothing to do here
  }

})

L.control.labelcontrol = function (opts) {
  return new L.Control.LabelControl(opts)
}

var labelsShown = true

function showLabels () {
  if (!labelsShown) {
    if (markers) {
      markers.forEach(function (marker) {
        marker.openTooltip()
      })
    }
    labelsShown = true
  }
}

function hideLabels () {
  if (labelsShown) {
    if (markers) {
      markers.forEach(function (marker) {
        marker.closeTooltip()
      })
    }
    labelsShown = false
  }
}

function toggleLabels () {
  if (labelsShown) {
    hideLabels()
  } else {
    showLabels()
  }
}

/**
 * Initializes leaflet map
 * @param div where map will be placed
 * @options initial centerpoint and zoomlevel
 * @returns the map
 */
function initMap (div, options, id) {
  var map = L.map(div, options)
  // assign id to map
  map.id = id

  const basePane = map.createPane('basePane')
  basePane.style.zIndex = 100

  var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    pane: 'basePane'
  })

  var stamen = L.tileLayer('http://tile.stamen.com/terrain/{z}/{x}/{y}.png', {
    attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>.',
    pane: 'basePane',
  })
  
  var roads = L.gridLayer.googleMutant({
    type: 'roadmap', // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid'
    pane: 'basePane'
  })

  var satellite = L.gridLayer.googleMutant({
    type: 'satellite', // valid values are 'roadmap', 'satellite', 'terrain' and 'hybrid',
    pane: 'basePane'
  })

  var topo = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri',
    pane: 'basePane'
  })

  var imagery = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri',
    pane: 'basePane'
  })

  const baseMaps = { Openstreetmap: osm, 'Terrain': stamen, 'Google maps': roads, 'Google satellite': satellite, 'ESRI topo': topo, 'ESRI satellite': imagery }
  const overlayMaps = {}
  map.layerControl = L.control.layers(baseMaps, overlayMaps).addTo(map)

  if (!restoreMap(map)) {
    // use default map
    osm.addTo(map)
  }

  restoreBounds(map)

  // var control = L.control.labelcontrol({ position: 'topleft' }).addTo(map);

  L.control.scale({position:'bottomleft'}).addTo(map);
  
  map.on('baselayerchange', function (e) { changeBaseLayer(e) })
  map.on('zoomend', function () { saveBounds(map) })
  map.on('moveend', function () { saveBounds(map) })
  theMap = map
  return map
}
