#!/bin/zsh 

wget 'https://www.google.com/maps/d/u/0/kml?hl=en&mid=1Q5zv1UhUZFfh2LyV6HF7bpoFR98&forcekml=1&cid=mp&cv=YRCfAmBgVOI.en.' -O sensors.kml
./parse-kml.py -f sensors.kml >! ../www/sensors.json
