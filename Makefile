buildroot = /
docdir = /usr/share/doc/packages
python_version = 3
python_lookup_name = python$(python_version)
python = $(shell which $(python_lookup_name))

LC = LC_MESSAGES
PKG = python-kiwi-keg

version := $(shell \
    $(python) -c \
    'from kiwi_keg.version import __version__; print(__version__)'\
)

install_package_docs:
	install -d -m 755 ${buildroot}${docdir}/$(PKG)
	install -m 644 LICENSE \
		${buildroot}${docdir}/$(PKG)/LICENSE
	install -m 644 README.rst \
		${buildroot}${docdir}/$(PKG)/README.rst

install:
	# manual pages
	install -d -m 755 ${buildroot}usr/share/man/man1
	for man in doc/build/man/*.1 ; do \
		install -m 644 $$man ${buildroot}usr/share/man/man1 ;\
	done
	# keg obs service
	install -d -m 755 ${buildroot}usr/lib/obs/service
	mv ${buildroot}usr/bin/compose_kiwi_description \
		${buildroot}usr/lib/obs/service
	install -m 644 obs/compose_kiwi_description.service \
		${buildroot}usr/lib/obs/service

tox:
	tox "-p 4"

git_attributes:
	# the following is required to update the $Format:%H$ git attribute
	# for details on when this target is called see setup.py
	git archive HEAD kiwi_keg/version.py | tar -x

clean_git_attributes:
	# cleanup version.py to origin state
	# for details on when this target is called see setup.py
	git checkout kiwi_keg/version.py

build: clean tox
	# create setup.py variant for rpm build.
	# delete module versions from setup.py for building an rpm
	# the dependencies to the python module rpm packages is
	# managed in the spec file
	sed -ie "s@>=[0-9.]*'@'@g" setup.py
	# build the sdist source tarball
	$(python) -m build
	# restore original setup.py backed up from sed
	mv setup.pye setup.py
	# update rpm changelog using reference file
	helper/update_changelog.py --since package/$(PKG).changes > \
		dist/$(PKG).changes
	helper/update_changelog.py --file package/$(PKG).changes >> \
		dist/$(PKG).changes
	# copy spec file
	cp package/$(PKG).spec dist/

pypi: clean tox
	$(python) setup.py sdist upload

clean: clean_git_attributes
	$(python) setup.py clean
	rm -rf doc/build
	rm -rf doc/dist
