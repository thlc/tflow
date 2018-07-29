var map;
var ajaxRequest;
var plotlist;
var plotlayers=[];

function makeSensor(map, sensor_name, lat, lon) {
  var pos = new L.LatLng(lat, lon);
  var request = new XMLHttpRequest();
  var color = '#aaaaaa';

  // FIXME: single file for all sensors, loaded once, async + id.
  // THIS IS WAY TOO SLOW!!!
  request.open('GET', 'data/' + sensor_name, false);
  request.send(null);

  console.log("request.status=" + request.status);
  if (request.status == 200) {
    var response = JSON.parse(request.responseText);
    var data = response[sensor_name];

    if (data['occupancy'] > 10) {
      color = '#ff0000';
    } else if (data['occupancy'] > 5) {
      color = '#ffff00';
    }

    // actual speed takes precedence over occupancy
    if (data['speed'] > 70) {
      color = '#00aa00';
    } else if (data['speed'] > 40) {
      color = '#774422';
    } else if (data['speed'] == 0) {
      color = '#dddddd'; // no data?
    }
    console.log("color:"+color)
  }

  console.log("color_real:"+color)
  var c = new L.circle(pos, { "radius": 20, "color": color })
  c.bindPopup("<img src=\"/~thomas/tflow/graphs/" + sensor_name + ".png\"/>");
  c.on('mouseover', function(e) { this.openPopup(); });
  c.on('mouseout',  function(e) { this.closePopup(); });
  c.addTo(map);
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
}

function initmap() {
  // set up the map
  map = new L.Map('mapid');

  // create the tile layer with correct attribution
  var osmUrl='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
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
