import time
import sys
import BaseHTTPServer
from urlparse import urlparse, parse_qs
from wand.image import Image

HOST_NAME = '127.0.0.1'
PORT_NUMBER = 8181

bbox = []


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.find('SERVICE=WMS') < 0:
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(urlparse(self.path).query)

        # we're only interested by:
        #  - FORMAT=
        #  - BBOX=minx,miny,maxx,maxy
        #  - WIDTH|HEIGHT

        self.send_response(200)
        self.send_header("Content-type", params['FORMAT'][0])
        self.end_headers()

        copy = image.clone()
        request_bbox = [float(t) for t in params['BBOX'][0].split(',')]

        dimx = bbox[2] - bbox[0]
        dimy = bbox[3] - bbox[1]

        left = (image.width * (request_bbox[0] - bbox[0])) / dimx
        right = (image.width * (request_bbox[2] - bbox[0])) / dimx

        top = (image.height * ((bbox[3] - request_bbox[1])) / dimy)
        bottom = (image.height * ((bbox[3] - request_bbox[3])) / dimy)

        # extract area of interest
        copy.crop(int(left), int(bottom), int(right), int(top))
        copy.resize(int(params['WIDTH'][0]), int(params['HEIGHT'][0]))
        copy.format = params['FORMAT'][0].split('/')[1]

        copy.save(file=self.wfile)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python dummywms.py image_full_path minx,miny,maxx,maxy')
        sys.exit(1)
    image = Image(filename=sys.argv[1])
    bbox = [float(t) for t in sys.argv[2].split(',')]
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
