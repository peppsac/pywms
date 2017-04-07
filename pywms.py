#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import sys
from timeit import default_timer as timer
import BaseHTTPServer
from urlparse import urlparse, parse_qs
from wand.image import Image
from wand.color import Color

HOST_NAME = '127.0.0.1'
PORT_NUMBER = 8181

bbox = []
crs = None


def timed_transform(left, right, bottom, top, width, height, img, func):
    print('{}:{} {}:{}'.format(left, right, top, bottom))

    begin = timer()
    result = func(left, right, bottom, top, width, height, img)
    end = timer()

    print('{} duration: {} (image size: {}x{})'.format(
      func.func_name,
      end - begin,
      right - left, top - bottom))

    return result


def crop_sample(left, right, bottom, top, width, height, img):
    border_width = [-left if left < 0 else 0, (right - img.width)
                    if right > img.width else 0]
    border_height = [-bottom if bottom < 0 else 0, (top - img.height)
                     if top > img.height else 0]

    print ('border_width={}'.format(border_width))
    print ('border_height={}'.format(border_height))
    copy = img[max(0, left):min(img.width, right),
               max(0, bottom):min(img.height, top)]

    # ...
    if sum(border_width) > 0 or sum(border_height) > 0:
        copy.border(Color('transparent'), sum(border_width), sum(border_height))
        copy.crop(border_width[1],
                  border_height[1],
                  copy.width - border_width[0],
                  copy.height - border_height[0])

    copy.sample(width, height)
    return copy


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.find('SERVICE=WMS') < 0:
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(urlparse(self.path).query)

        if 'REQUEST' not in params:
            self.send_response(503)
            self.end_headers()
            return

        command = params['REQUEST'][0]

        if command == 'GetMap':

            # we're only interested by:
            #  - FORMAT=
            #  - BBOX=minx,miny,maxx,maxy
            #  - WIDTH|HEIGHT

            self.send_response(200)
            self.send_header('Content-type', params['FORMAT'][0])
            self.end_headers()

            request_bbox = [float(t) for t in params['BBOX'][0].split(',')]

            dimx = bbox[2] - bbox[0]
            dimy = bbox[3] - bbox[1]

            print 'REQ:', request_bbox
            print 'SRC:', bbox

            target_width = int(params['WIDTH'][0])
            target_height = int(params['HEIGHT'][0])

            best_candidate = image

            # If we're using a pyramidal image, pick the best one
            # The best one is the smallest image where the ratio
            # pixel_source/pixel_target is > 1 (== no upscaling)
            if image.sequence is not None:
                ratios = [(request_bbox[2+i] - request_bbox[i]) /
                          (bbox[2+i] - bbox[i]) for i in [0, 1]]
                pixels_dest_count = [float(target_width), float(target_height)]

                best_candidate = image.sequence[0]
                for img in image.sequence[1:]:
                    pixels_source_count = [ratios[0] * img.width,
                                           ratios[1] * img.height]

                    ratio = [pixels_source_count[i] / pixels_dest_count[i]]
                    if min(ratio) >= 1:
                        best_candidate = img
                    else:
                        break

                print '{}x{}|,{}x{} taken from {}x{}'.format(
                    ratios[0], ratios[1],
                    target_width, target_height,
                    best_candidate.width, best_candidate.height)

            # Compute extraction area
            left = (best_candidate.width * (request_bbox[0] - bbox[0])) / dimx
            right = (best_candidate.width * (request_bbox[2] - bbox[0])) / dimx

            top = (best_candidate.height * ((bbox[3] - request_bbox[1])) / dimy)
            bottom = (best_candidate.height * ((bbox[3] - request_bbox[3])) / dimy)

            out = timed_transform(int(left), int(right),
                                  int(bottom), int(top),
                                  int(params['WIDTH'][0]), int(params['HEIGHT'][0]),
                                  best_candidate,
                                  crop_sample)

            out.format = params['FORMAT'][0].split('/')[1]
            out.save(file=self.wfile)

        elif command == 'GetCapabilities':
            self.send_response(200)
            self.send_header('Content-type', 'text/xml; charset=UTF-8')
            self.end_headers()

            self.wfile.write(
              '''<?xml version='1.0' encoding="UTF-8" standalone="no" ?>
              <WMS_Capabilities version="1.3.0"  xmlns="http://www.opengis.net/wms"   xmlns:sld="http://www.opengis.net/sld"   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"   xsi:schemaLocation="http://www.opengis.net/wms http://schemas.opengeospatial.net/wms/1.3.0/capabilities_1_3_0.xsd  http://www.opengis.net/sld http://schemas.opengeospatial.net/sld/1.1.0/sld_capabilities.xsd ">

              <Service>
                <Name>WMS</Name>
                <Title>foofoo</Title>
                <Abstract>barbar</Abstract>
                <Fees>no conditions apply</Fees>
                <AccessConstraints>None</AccessConstraints>
                <MaxWidth>4096</MaxWidth>
                <MaxHeight>4096</MaxHeight>
              </Service>

              <Capability>
                <Request>
                  <GetCapabilities>
                    <Format>text/xml</Format>
                  </GetCapabilities>
                  <GetMap>
                    <Format>image/png</Format>
                    <Format>image/gif</Format>
                    <Format>image/jpeg</Format>
                    <Format>image/tiff</Format>
                    <Format>image/png; mode=8bit</Format>
                  </GetMap>
                </Request>
                <Exception>
                  <Format>XML</Format>
                  <Format>INIMAGE</Format>
                  <Format>BLANK</Format>
                </Exception>
                <Layer>
                  <Name>FooFoo</Name>
                  <Title>BarBar</Title>
                  <Abstract>foobarfoobar</Abstract>

                  <CRS>{crs}</CRS>
                  <EX_GeographicBoundingBox>
                      <westBoundLongitude>-180</westBoundLongitude>
                      <eastBoundLongitude>180</eastBoundLongitude>
                      <southBoundLatitude>-90</southBoundLatitude>
                      <northBoundLatitude>90</northBoundLatitude>
                  </EX_GeographicBoundingBox>
                  <BoundingBox CRS="{crs}"
                              minx="{minx}" miny="{miny}" maxx="{maxx}" maxy="{maxy}" />
                </Layer>
              </Capability>
              </WMS_Capabilities>
            '''.format(crs=crs, minx=bbox[0], maxx=bbox[2], miny=bbox[1], maxy=bbox[3]))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python dummywms.py image_full_path crs minx,miny,maxx,maxy')
        sys.exit(1)
    image = Image(filename=sys.argv[1])
    crs = sys.argv[2]
    bbox = [float(t) for t in sys.argv[3].split(',')]
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
