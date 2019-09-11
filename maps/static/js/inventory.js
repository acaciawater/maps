class Inventory {
	
	constructor () {
		this.data = {}
		this.styles = {}
		this.attribute = ''
		this.layer = undefined
	}
	
	loadStyles(url='/static/styles.json') {
		return $.getJSON(url).then(response => {
			return this.styles = response
		})
	}
	
	loadData(url='/static/inventory.json') {
		return $.getJSON(url).then(response => {
			return this.data = response
		})
	}

	getColor(value) {
		if (value != undefined) {
			const attr = this.getAttribute()
			const classes = this.styles.classes[attr]
			const colors = this.styles.colors[attr]
			if (colors && classes) {
				const index = classes.findIndex(x => x > value)
				if (index < 0)
					//  not found: take last color
					return colors[colors.length-1]
				return colors[index]
			}
		}
		return 'gray'
	}
	
	getStyle(feature) {
		const value = feature.properties[this.getAttribute()]
		if (value == undefined) {
			return {
                radius : 3,
	            color : 'gray',
	            fillColor: 'gray',
	            weight : 1,
	            opacity : 0.5,
	            fillOpacity : 0.3
			}
		}
		else {
			return {
                radius : 5,
                fillColor : this.getColor(value),
                color : 'white',
                weight : 1,
                opacity : 1,
                fillOpacity : 0.8
			}
		}
	}

	getLegendContent() {
		const attr = this.getAttribute()
		if (attr == undefined)
			return ''
		if (this.styles == undefined)
			return ''
		const colors = this.styles.colors[attr]
		const classes = this.styles.classes[attr]
		if (classes == undefined || colors == undefined)
			return ''
		let html = `<strong>${attr}</strong>`
		for(let i=0;i<classes.length;i++) {
			let txt = ''
			if (i==0) {
				txt =  `<  ${classes[i]}`
			}
			else if (i < classes.length-1) {
				txt = `${classes[i-1]} - ${classes[i]}`
			}
			else  {
				txt = `> ${classes[i-1]}` 
			}
			html += `<div><i class="fas fa-circle fa-xs pr-2" style="color:${colors[i]}"></i>${txt}</div>`
		}
		return html
	}

	getAttribute() {
		return this.attribute
	}
	
	createLayer(data) {
		this.data = data
		const attr = this.getAttribute()
		return this.layer = L.geoJSON(data, {
			onEachFeature: (feature, layer) => {
				layer.bindTooltip(`${attr}: ${feature.properties[attr]}`);
			},
	        pointToLayer: (feature, latlng) => {
	            return L.circleMarker(latlng, this.getStyle(feature))
	       }
		})
	}

	redraw(map) {
		if (this.layer) {
			this.layer.remove()
			this.layer = undefined
		}
		this.createLayer(this.data).addTo(map)
	}
}