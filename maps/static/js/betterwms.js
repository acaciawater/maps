/**
 * 
 */
L.TileLayer.BetterWMS = L.TileLayer.WMS.extend({
  
	/**
	 * creates an XSLTProcessor and loads stylesheet
	 */
  loadStylesheet: function(url) {
  	let http = new XMLHttpRequest();
	http.open("GET",url,false);
	http.send("");
	let xsl = http.responseXML;
//	console.debug(xsl);
	let processor = new XSLTProcessor();
	processor.importStylesheet(xsl);
	return processor;
  },
  
  onAdd: function (map) {
    // Triggered when the layer is added to a map.
    L.TileLayer.WMS.prototype.onAdd.call(this, map);
    if (this.wmsParams.clickable) {
    	map.on('click', this.getFeatureInfo, this);
    }
  },
  
  onRemove: function (map) {
    // Triggered when the layer is removed from a map.
    L.TileLayer.WMS.prototype.onRemove.call(this, map);
    if (this.wmsParams.clickable) {
    	map.off('click', this.getFeatureInfo, this);
    }
  },
  
  formatFeatureInfoResponseXSLT: function(response) {
	  // format FeatureInfoResponse using a stylesheet
	    if (this.xsltProcessor === undefined) {
	    	this.xsltProcessor = this.loadStylesheet("/static/xsl/getfeatureinforesponse.xsl");
	    }
		let doc = this.xsltProcessor.transformToDocument(response);
		return doc.firstChild.innerHTML;
	  },

  formatFeatureInfoResponse: function(response) {
    // customized formatting of FeatureResponse
    let props = this.wmsParams.propertyName;
    if (props)
    	// use specified properties only
    	props = props.split(',');
    // use displayname instead of layer name
    let displayName = this.wmsParams.displayName;
    const resp= xml2json.docToJSON(response);
    let html = '';
    let itemCount = 0;
    if (resp.tagName === 'GetFeatureInfoResponse') {
    	if (resp.children) {
	    	resp.children.forEach(layer => {
	    		let layerName = layer.attr.name;
	    		if (layerName === this.wmsParams.layers)
	    			// use provided display name (wmslayer's title)
	    			layerName = displayName;
	    		if (layer.children) {
		    		layer.children.forEach(item => {
		    			if (item.tagName === 'Attribute') {
		    				//  Raster Info: single attribute without feature(s)
	    					const value = item.attr.value;
	    					itemCount++;
	    					html += `<tr>
		    					<td>${layerName}</td>
		    					<td>${value}</td>
		    					</tr>`
		    			}
		    			else if (item.tagName === 'Feature') {
		    				// Vector Info (features)
			    			const id = item.attr.id;
			    			if (item.children) {
			    				item.children.forEach(property => {
				    				if (property.tagName === 'Attribute') {
				    					const name = property.attr.name;
				    					if (!props || props.includes(name)) {
					    					const value = property.attr.value;
					    					// console.info(`layer=${layerName}, feature=${id}, ${name}=${value}`);
					    					itemCount++;
					    					html += `<tr>
					    					<td>${name}</td>
					    					<td>${value}</td>
					    					</tr>`
				    					}
				    				}
				    			})
			    			}
		    			}
		    		})
	    		}
	    	})
    	}
    }
    return itemCount? html: null;
  },

  getFeatureInfo: function(evt) {
    const params = this.getFeatureInfoParams(evt.latlng);
    $.get(this._url,params).then(response => {
    	const html = this.formatFeatureInfoResponse(response);
	    if (html) {
	    	L.popup({ maxWidth: 800})
		    .setLatLng(evt.latlng)
		    .setContent('<html><body><table>' + html + '</table></body></html>')
		    .openOn(this._map)  	
	    }
	});
  },

  getFeatureInfoParams: function (latlng) {
    // Construct parameters object for a GetFeatureInfo request at a given point
	const lat = latlng.lat;
	const lon = latlng.lng;
    const params = {
          request: 'GetFeatureInfo',
          service: 'WMS',
          srs: 'EPSG:4326',
          version: '1.3.0',      
          bbox: [lat, lon, lat + 0.00001, lon + 0.00001].join(','),
          height: 100,
          width: 100,
          i: 0,
          j: 0,
          layers: this.wmsParams.layers,
          query_layers: this.wmsParams.layers,
          info_format: 'text/xml',
        };
    
    if ('propertyName' in this.wmsParams)
    	params['propertyName'] = this.wmsParams.propertyName;
    return params;    
  }
});

L.tileLayer.betterWms = function (url, options) {
  return new L.TileLayer.BetterWMS(url, options);  
};