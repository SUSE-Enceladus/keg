#!/bin/bash
#================
# FILE          : images.sh
#----------------
# PROJECT       : openSUSE KIWI Image System
# COPYRIGHT     : (c) 2020 SUSE LLC. All rights reserved
#               : 
# AUTHOR        : The Team bob@example.net
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : OS configuration script
#               :
#               :
# STATUS        : Production
#----------------
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

#======================================
# Fail build on error
#--------------------------------------
set -e


# keg: included from JeOS-image
bob
