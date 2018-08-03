var map;
var ajaxRequest;
var plotlist;
var plotlayers=[];

// holds a reference to each Circle
var sensors = new Object();


function dec2hex(d) {
  if (d > 15) {
    return d.toString(16);
  } else {
    return "0" + d.toString(16);
  }
}

function rgb(r, g, b)
{
  return "#" + dec2hex(r) + dec2hex(g) + dec2hex(b);
}

// an index is between 0-100.
// 0 is free flowing, 100 is congested.
function make_congestion_index(value, congested_thr, freeflow_thr) {
  idx = ((value - freeflow_thr) * 100.0) / (congested_thr - freeflow_thr);
  return Math.floor(idx);
}

function handleCongestion(response) {
  var color;
  var data;

  for (key in response['sensors']) {
    data = response['sensors'][key];
    sensor_name = data['sensorName'];

    occ = data['occupancy']
    speed = data['speed']
    flow = data['vehicleFlow']

    if (speed > 0 && occ > 0 && flow > 0) {
      speed_weight = make_congestion_index(speed, 30, 90);
      occ_weight   = make_congestion_index(occ, 20, 7);

      congestion_factor = (speed_weight + occ_weight) / 2
      if (congestion_factor > 100)
	congestion_factor = 100;
      if (congestion_factor < 0)
	congestion_factor = 0;

      // remap it to 0-255
      congestion_factor = congestion_factor * 2.5;

      color = rgb(Math.floor(congestion_factor), Math.floor(255 - congestion_factor), 0);
      console.log("sensor[" + sensor_name + "] cong[" + congestion_factor + "] color[" + color + "]");
    } else {
      color = '#eeeeee';
    }

    if (typeof sensors[sensor_name] != 'undefined') {
      sensors[sensor_name].setStyle({ "color": color, "opacity": 1 });
    } else {
      console.log("unknown sensor " + sensor_name);
    }
  }
}

function makeSensor(map, sensor_name, lat, lon) {
  var pos = new L.LatLng(lat, lon);
  var c = new L.circle(pos, { "radius": 20, "color": '#eeeeee', "opacity": 0.2 })
  c.bindPopup("<img src=\"/~thomas/tflow/graphs/" + sensor_name + ".png\"/>", { "keepInView": "true", "clocseOnClick": "true", "minWidth": "400px" });
  c.on('onclick', function(e) { this.openPopup(); });
  //c.on('mouseout',  function(e) { this.closePopup(); });
  c.addTo(map);
  // store a reference of the object to update the color (async)
  sensors[sensor_name] = c;
}

function updateCongestionCallback() {
// perform an asynchronous AJAX request to the sensors data file.
  var xmlhttp = new XMLHttpRequest();

  xmlhttp.responseType = 'json';
  xmlhttp.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      handleCongestion(this.response);
    } else {
      console.log("unable to get sensors.json (readyState: " + this.readyState + ", status: " + this.status + ")");
    }
  };
  xmlhttp.open("GET", "data/sensors-latest.json", true);
  xmlhttp.send();
}


// sensors: array of Objects { "sensor_name": "lat,long" }
function initSensors(map, sensors) {
  for (var i = 0; i < sensors.length; i++) {
    sensor = sensors[i];
    for (var key in sensor) {
      sensorName = key;
      sensorCoords = sensor[key].split(",");
      makeSensor(map, sensorName, sensorCoords[1], sensorCoords[0]);
    }
  }

  updateCongestionCallback();

  setInterval(function() { updateCongestionCallback(); }, 10000);
}

function initmap() {
  // set up the map
  map = new L.Map('mapid');

  // original OSM
  //var osmUrl='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  // grayscale
  var osmUrl='https://tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png';

  // pure B&W
  //var osmUrl='http://a.tile.stamen.com/toner/{z}/{x}/{y}.png';
  
  var osmAttrib='Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors';
  var osm = new L.TileLayer(osmUrl, {minZoom: 8, maxZoom: 18, attribution: osmAttrib});        

  // start the map in South-East England
  map.setView(new L.LatLng(43.4, 5.3),11.3);
  map.addLayer(osm);

  var xmlhttp = new XMLHttpRequest();
  var url = "sensors.json";

  xmlhttp.responseType = 'json';
  xmlhttp.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      initSensors(map, this.response.sensors);
    }
  };

  xmlhttp.open("GET", url, true);
  xmlhttp.send();

}

initmap();
