# Copyright (c) 2021 SUSE Software Solutions Germany GmbH. All rights reserved.
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
class KegError(Exception):
    """
    **Base class to handle all known exceptions**

    Specific exceptions are implemented as sub classes of KegError

    Attributes

    :param string message: Exception message text
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return format(self.message)


class KegLogFileSetupFailed(KegError):
    """
    Exception raised if the log file could not be created.
    """


class KegDescriptionNotFound(KegError):
    """
    Exception raised if the keg written description could not be found
    """


class KegKiwiValidationError(KegError):
    """
    Exception raised if the validation of the keg written
    description against the KIWI API has failed
    """


class KegKiwiDescriptionError(KegError):
    """
    Exception raised if the creation of the keg written description
    through the KIWI API has failed
    """
