pywms.py
--------

Dummiest possible implementation of a WMS server.

Allows you to serve a single image using the WMS protocol.
Most-of wms parameters are **ignored**, the only used ones are:
  * FORMAT: the format of the returned image
  * BBOX: the extracted area
  * WIDTH/HEIGHT: dimension of the returned image

Example usage:
```
python pywms.py foo.png 0,0,100,200
```

The first parameter is the image to serve and the second one is the bounding-box covered by the image (minx,miny,maxx,maxy).


