#!/bin/bash

# keg: included from JeOS-sysconfig
baseUpdateSysConfig /etc/sysconfig/language INSTALLED_LANGUAGES ""

# keg: included from JeOS-files
cat >> "/etc/sysconfig/console" <<EOF
CONSOLE_ENCODING="UTF-8"
EOF

# keg: included from JeOS-config
bar
bob

# keg: included from JeOS-services
baseInsertService sshd
baseRemoveService kbd

if [[ $kiwi_profiles = other ]]; then
    # keg: included from foo-timer
    systemctl enable foo.timer

fi
