#!/bin/bash

# keg: included from common-sysconfig
baseUpdateSysConfig /etc/sysconfig/language RC_LANG "C.UTF-8"

# keg: included from common-files
cat >> "/etc/some.conf" <<EOF
Some config
EOF

# keg: included from common-scripts
Some fundamental config stuff

# keg: included from common-services
baseInsertService some-service
baseRemoveService other-service
systemctl enable some.timer


if [[ $kiwi_profiles = Blue ]]; then
    # keg: included from _namespace_blue_scripts
    Configure some blue parameters
fi


if [[ $kiwi_profiles = Orange ]]; then
    # keg: included from _namespace_orange_scripts
    Configure some orange parameters
fi


if [[ $kiwi_profiles = Blue || $kiwi_profiles = Orange ]]; then
    # keg: included from _namespace_common_scripts
    Some common config stuff
fi
