var map;
var ajaxRequest;
var plotlist;
var plotlayers=[];

function makeSensor(map, sensor_name, lat, lon) {
  var pos = new L.LatLng(lat, lon);
  var c = new L.circle(pos, { "radius": 20 })
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

  xmlhttp.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var response = JSON.parse(this.responseText);
      initSensors(map, response.sensors);
    }
  };

  xmlhttp.open("GET", url, true);
  xmlhttp.send();

}

initmap();
