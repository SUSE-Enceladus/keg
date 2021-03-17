#!/bin/bash
#================
# FILE          : config.sh
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

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]..."

#======================================
# Setup the build keys
#--------------------------------------
suseImportBuildKey


# keg: included from JeOS-sysconfig
baseUpdateSysConfig /etc/sysconfig/language INSTALLED_LANGUAGES ""

# keg: included from JeOS-files
cat >> /etc/sysconfig/console <<EOF
CONSOLE_ENCODING="UTF-8"
EOF

# keg: included from JeOS-config
bar

bob







# keg: included from JeOS-services
suseInsertService sshd
suseRemoveService kbd

if [[ $kiwi_profiles = other ]]; then
    # keg: included from JeOS-sysconfig
    baseUpdateSysConfig /etc/sysconfig/language INSTALLED_LANGUAGES ""

    # keg: included from JeOS-files
    cat >> /etc/sysconfig/console <<EOF
CONSOLE_ENCODING="UTF-8"
EOF
    
    # keg: included from JeOS-config
    bar

    bob

    
    
    
    
    
    
    # keg: included from JeOS-services
    suseInsertService sshd
    suseRemoveService kbd
fi
