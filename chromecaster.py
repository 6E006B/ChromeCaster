#!/usr/bin/env python

import argparse
import os
import pychromecast
import socket
import sys
import tempfile
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor


class ChromeCaster:

    def __init__(self, filename, cast_name=None, ip=None, port=None, verbose=False):
        self.verbose = verbose
        self.filename = filename
        try:
            self.cast = self.get_cast(cast_name)
        except StopIteration:
            print('ERROR: Unable to find device{} to cast to.'.format(" ('{}')".format(cast_name) if cast_name else ""))
            sys.exit(-1)
        self.ip = ip
        if ip == None:
            # guess local ip (other than 127.*.*.*)
            self.ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
        self.port = port if port else 31331
        self.url = 'http://{}:{}/{}'.format(self.ip, self.port, os.path.basename(self.filename))

    def get_cast(self, name=None):
        cast = None
        if name:
            casts = pychromecast.get_chromecasts()
            cast = next(cc for cc in casts if cc.device.friendly_name == name)
        else:
            cast = pychromecast.get_chromecast()
        if self.verbose: print("found cast device '{}'".format(cast.device.friendly_name))
        return cast

    def start_media_server(self):
        if self.verbose: print('creating temporary files')
        directory = tempfile.mkdtemp()
        symlinked_filename = '{}{}{}'.format(directory, os.sep, os.path.basename(self.filename))
        os.symlink(os.path.abspath(self.filename), symlinked_filename)
        if self.verbose: print("starting media server running '{}'".format(self.url))
        resource = File(directory)
        factory = Site(resource)
        reactor.listenTCP(self.port, factory)
        reactor.run()
        os.remove(symlinked_filename)
        os.rmdir(directory)
        if self.verbose: print('cleaned up temporary files')

    def play_file(self):
        if self.verbose: print("requesting to cast '{}'".format(self.url))
        self.cast.media_controller.play_media(self.url, 'video/mp4')
        self.start_media_server()


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Cast a video file to your ChromeCast.')
    parser.add_argument('-f', '--filename', required=True,
        help='video file to play on the ChromeCast')
    parser.add_argument('-c', '--cast-name',
        help='Name of the ChromeCast to use')
    parser.add_argument('-p', '--port', type=int, default=31331,
        help='port to use on this device for providing video data (default: 31331)')
    parser.add_argument('-i', '--ip',
        help='IP to use on this device for serving video data (default: guess)')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='print some information on separate steps')

    args = parser.parse_args()

    caster = ChromeCaster(
        filename=args.filename,
        cast_name=args.cast_name,
        ip=args.ip,
        port=args.port,
        verbose=args.verbose
    )
    caster.play_file()
