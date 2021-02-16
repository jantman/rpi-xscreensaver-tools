#!/usr/bin/env python3
"""
Script to control and monitor xscreensaver via HTTP.

Written for Python 3.7

Requires Flask from PyPI, tested against 1.0.2

Canonical source: https://github.com/jantman/rpi-xscreensaver-tools

MIT License

Copyright (c) 2021 Jason Antman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import struct
import ctypes
import logging
import subprocess

from flask import Flask, request, jsonify

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

if 'XAUTHORITY' not in os.environ:
    os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

app = Flask(__name__)
app.logger.propagate = True


def uptime():
    libc = ctypes.CDLL('libc.so.6')
    buf = ctypes.create_string_buffer(4096)
    if libc.sysinfo(buf) != 0:
        print('failed')
        return -1
    uptime = struct.unpack_from('@l', buf.raw)[0]
    return uptime


def humantime(secs):
    if secs > 31536000:
        return '%s years' % round(secs / 31536000, 1)
    if secs > 2592000:
        return '%s months' % round(secs / 2592000, 1)
    if secs > 86400:
        return '%s days' % round(secs / 86400, 1)
    if secs > 3600:
        return '%s hours' % round(secs / 3600, 1)
    if secs > 60:
        return '%s minutes' % round(secs / 60, 1)
    return '%s seconds' % secs


def _is_screen_blanked():
    app.logger.debug('Getting current state of screensaver')
    p = subprocess.run(
        ['xscreensaver-command', '-time'], stdout=subprocess.PIPE
    )
    app.logger.debug('Command output: %s', p.stdout)
    if 'screen blanked since' in p.stdout.decode():
        app.logger.info('Screen is currently blanked (screensaver active)')
        return True
    if 'screen non-blanked since' in p.stdout.decode():
        app.logger.info(
            'Screen is currently not blanked (screensaver inactive)'
        )
        return False
    raise RuntimeError(
        'ERROR: Unable to determine screensaver state from output: '
        f'{p.stdout.decode()}'
    )


def get_status():
    try:
        is_blanked = _is_screen_blanked()
    except Exception as ex:
        app.logger.error(
            'Exception running xscreensaver-command -time', exc_info=True
        )
        return {
            'success': False,
            'is_on': False,
            'state': 'unknown',
            'exception': str(ex)
        }
    return {
        'success': True,
        'is_on': is_blanked,
        'state': 'on' if is_blanked else 'off'
    }


@app.route('/', methods=['GET', 'POST'])
def handle():
    app.logger.info('Got request with values: %s' % dict(request.form))
    if request.method == 'POST':
        data = request.get_json()
        app.logger.info('Got POST from %s: %s', request.remote_addr, data)
        status = get_status()
        if data.get('state') is True and status['is_on'] is False:
            app.logger.info('Turning on screensaver')
            p = subprocess.run(
                ['xscreensaver-command', '-activate'], stdout=subprocess.PIPE
            )
            app.logger.debug('Command output: %s', p.stdout)
        elif data.get('state') is False and status['is_on'] is True:
            app.logger.info('Turning off screensaver')
            p = subprocess.run(
                ['xscreensaver-command', '-deactivate'], stdout=subprocess.PIPE
            )
            app.logger.debug('Command output: %s', p.stdout)
        else:
            app.logger.info('POST but no state change')
    status = get_status()
    status['uptime'] = uptime()
    status['server'] = 'https://github.com/jantman/rpi-xscreensaver-tools'
    return jsonify(status)


if __name__ == '__main__':
    debug = 'FLASK_DEBUG' in os.environ
    app.run(
        host="0.0.0.0", port=int(os.environ.get('FLASK_PORT', '8080')),
        debug=debug
    )
