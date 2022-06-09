# Copyright (c) 2022 SUSE Software Solutions Germany GmbH. All rights reserved.
#
# This file is part of keg.
#
# keg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# keg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with keg. If not, see <http://www.gnu.org/licenses/>
#
import logging
import sys

# project
from kiwi_keg.logger_filter import (
    LoggerSchedulerFilter,
    InfoFilter,
    DebugFilter,
    ErrorFilter,
    WarningFilter
)

from kiwi_keg.exceptions import KegLogFileSetupFailed


class Logger(logging.Logger):
    """
    **Extended logging facility based on Python logging**

    :param string name: name of the logger
    """
    def __init__(self, name):
        logging.Logger.__init__(self, name)
        self.console_handlers = {}
        self.logfile = None
        # log INFO to stdout
        self._add_stream_handler(
            'info',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [InfoFilter(), LoggerSchedulerFilter()]
        )
        # log WARNING messages to stdout
        self._add_stream_handler(
            'warning',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [WarningFilter()]
        )
        # log DEBUG messages to stdout
        self._add_stream_handler(
            'debug',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [DebugFilter()]
        )
        # log ERROR messages to stderr
        self._add_stream_handler(
            'error',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [ErrorFilter()],
            sys.__stderr__
        )
        self.log_level = self.level

    def getLogLevel(self):
        """
        Return currently used log level

        :return: log level number

        :rtype: int
        """
        return self.log_level

    def setLogLevel(self, level):
        """
        Set custom log level for all console handlers

        :param int level: log level number
        """
        self.log_level = level
        for handler_type in self.console_handlers:
            self.console_handlers[handler_type].setLevel(level)

    def set_logfile(self, filename):
        """
        Set logfile handler

        :param string filename: logfile file path
        """
        try:
            logfile = logging.FileHandler(
                filename=filename, encoding='utf-8'
            )
            logfile.setFormatter(
                logging.Formatter(
                    '%(levelname)s: %(asctime)-8s | %(message)s', '%H:%M:%S'
                )
            )
            logfile.addFilter(LoggerSchedulerFilter())
            self.addHandler(logfile)
            self.logfile = filename
        except Exception as e:
            raise KegLogFileSetupFailed(
                '{0}: {1}'.format(type(e).__name__, e)
            )

    def get_logfile(self):
        """
        Return file path name of logfile

        :return: file path

        :rtype: str
        """
        return self.logfile

    def _add_stream_handler(
        self, handler_type, message_format, message_filter,
        channel=sys.__stdout__
    ):
        handler = logging.StreamHandler(channel)
        handler.setFormatter(
            logging.Formatter(message_format, '%H:%M:%S')
        )
        for rule in message_filter:
            handler.addFilter(rule)
        self.addHandler(handler)
        self.console_handlers[handler_type] = handler
