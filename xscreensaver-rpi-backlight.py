#!/usr/bin/env python3
"""
Script to dim RPi touchscreen backlight when the screensaver comes on, and
raise the brightness when it goes off.

Written for Python 3.7

Requires rpi-backlight from PyPI, tested against 2.2.0

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

import sys
import argparse
import logging
import subprocess
from rpi_backlight import Backlight

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()


class XScreensaverRpiBacklight:

    def __init__(self):
        logger.debug('Initializing Backlight()')
        self.backlight = Backlight()
        logger.info(
            'Backlight starting brightness is %d', self.backlight.brightness
        )

    def _is_screen_blanked(self):
        logger.debug('Getting current state of screensaver')
        p = subprocess.run(
            ['xscreensaver-command', '-time'], stdout=subprocess.PIPE
        )
        logger.debug('Command output: %s', p.stdout)
        if 'screen blanked since' in p.stdout.decode():
            logger.info('Screen is currently blanked (screensaver active)')
            return True
        if 'screen non-blanked since' in p.stdout.decode():
            logger.info(
                'Screen is currently not blanked (screensaver inactive)'
            )
            return False
        raise RuntimeError(
            'ERROR: Unable to determine screensaver state from output: '
            f'{p.stdout.decode()}'
        )

    def run(self, dim=5, bright=100):
        current = self._is_screen_blanked()
        if current:
            logger.info('Set initial backlight to dim state (%d)', dim)
            self.backlight.brightness = dim
        else:
            logger.info('Set initial backlight to bright state (%d)', bright)
            self.backlight.brightness = bright
        logger.info('Executing: xscreensaver-command -watch')
        p = subprocess.Popen(
            ['xscreensaver-command', '-watch'], stdout=subprocess.PIPE,
            bufsize=1, universal_newlines=True
        )
        logger.info('Started PID %d', p.pid)
        for line in p.stdout:
            logger.debug('watch line: %s', line)
            if line.strip().startswith('UNBLANK'):
                logger.info('Screensaver disabled; set backlight to %d', bright)
                self.backlight.brightness = bright
            elif line.strip().startswith('BLANK'):
                logger.info('Screensaver enabled; set backlight to %d', dim)
                self.backlight.brightness = dim


def parse_args(argv):
    p = argparse.ArgumentParser(
        description='Control RaspberryPi touchscreen backlight with screensaver'
    )
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-d', '--dim', dest='dim', action='store', type=int,
                   default=5,
                   help='Backlight level when dimmed, 0 to 100. Default is 5, '
                        'the lowest visible level on my displays.')
    p.add_argument('-b', '--bright', dest='bright', action='store', type=int,
                   default=100,
                   help='Backlight level when bright, 0 to 100. Default is '
                        '100, max brightness.')
    args = p.parse_args(argv)
    if not 0 < args.dim < 101 or not 0 < args.bright < 101:
        raise ValueError(
            'ERROR: dim and bright values must be between 0 and 100, inclusive.'
        )
    return args


def set_log_info():
    """set logger level to INFO"""
    set_log_level_format(logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug():
    """set logger level to DEBUG, and debug-level output format"""
    set_log_level_format(
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(level, format):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    # set logging level
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()
    XScreensaverRpiBacklight().run(dim=args.dim, bright=args.bright)
