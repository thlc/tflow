var map;
var ajaxRequest;
var plotlist;
var plotlayers=[];

function initmap() {
  // set up the map
  map = new L.Map('mapid');

  // create the tile layer with correct attribution
  var osmUrl='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  var osmAttrib='Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors';
  var osm = new L.TileLayer(osmUrl, {minZoom: 8, maxZoom: 14, attribution: osmAttrib});        

  // start the map in South-East England
  map.setView(new L.LatLng(43.4, 5.3),11.3);
  map.addLayer(osm);


  var pa = new L.LatLng(43.35063, 5.34718);
  var pb = new L.LatLng(43.34978, 5.34609);
  var p = new L.polyline([pa, pb], { 'color': 'red', 'weight': 3 });
  p.addTo(map);
}
initmap();
