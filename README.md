pywms.py
--------

Dummiest possible implementation of a WMS server.

Allows you to serve a single image using the WMS protocol.
It supports only 2 commands:
  * `GetCapabilities`
  * `GetMap`

Most GetMap parameters are **ignored**, the only used ones are:
  * `FORMAT`: the format of the returned image
  * `BBOX`: the extracted area
  * `WIDTH`, `HEIGHT`: dimension of the returned image

Tested with QGIS and OpenLayers.

Example usage:
```
python pywms.py foo.png EPSG:2154 0,0,100,200
```

The first parameter is the image to serve and the second one is the bounding-box covered by the image (minx,miny,maxx,maxy).

If you have a big image (say 30.000x15.000 pixels), you can use a pyramidal format (tif for instance) to get faster response time.

Example command line to convert your image:
```
vips im_vips2tiff --vips-progress myimage.png  myimage.tif:jpeg:75,tile:256x256,pyramid
```

Notes regarding ImageMagick:
`pywms` uses [Wand](http://docs.wand-py.org/en/0.4.4/index.html) python binding to ImageMagick.
If you try to use it with big images you might hit ImageMagick's default [security policy](https://www.imagemagick.org/script/security-policy.php).

You can simply write a custom policy.xml, e.g:
```xml
<policymap>
  <policy domain="resource" name="width" value="40KP"/>
  <policy domain="resource" name="height" value="40KP"/>
  <policy domain="resource" name="memory" value="4GB"/>
  <policy domain="resource" name="map" value="4GB"/>
  <policy domain="resource" name="area" value="4GB"/>
  <policy domain="resource" name="disk" value="1GB"/>
</policymap>
```
and then set `MAGICK_CONFIGURE_PATH` value to the folder containing your custom `policy.xml`.




