#
# spec file for package python-kiwi-keg
#
# Copyright (c) 2023 SUSE LLC
# Copyright (c) 2022 SUSE Software Solutions Germany GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#

# If they aren't provided by a system installed macro, define them
%{!?_defaultdocdir: %global _defaultdocdir %{_datadir}/doc}

%if 0%{?suse_version} && 0%{?suse_version} < 1600
%global __python3 /usr/bin/python3.11
%global python3_pkgversion 311
%else
%{!?__python3: %global __python3 /usr/bin/python3}
%{!?python3_pkgversion:%global python3_pkgversion 3}
%endif

%if %{undefined python3_sitelib}
%global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
%endif

%global pygroup Development/Languages/Python
%global sysgroup System/Management
%global develsuffix devel

Name:           python-kiwi-keg
Version:        2.1.1
Release:        0
URL:            https://github.com/SUSE-Enceladus/keg
Summary:        KEG - Image Composition Tool
License:        GPL-3.0-or-later
Source:         keg-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  python%{python3_pkgversion}-%{develsuffix} >= 3.9
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-Sphinx
BuildRequires:  python%{python3_pkgversion}-Jinja2
BuildRequires:  fdupes
BuildArch:      noarch

%description
KEG is an image composition tool for KIWI image descriptions

# python3-kiwi-keg
%package -n python%{python3_pkgversion}-kiwi-keg
Summary:        KEG - Image Composition Tool
Requires:       python%{python3_pkgversion}-Jinja2
Requires:       python%{python3_pkgversion}-docopt
Requires:       python%{python3_pkgversion}-PyYAML
Requires:       python%{python3_pkgversion}-schema
Requires:       python%{python3_pkgversion}-kiwi >= 9.21.21
Provides:       python3-kiwi-keg = %version
Obsoletes:      python3-kiwi-keg < %version

%description -n python%{python3_pkgversion}-kiwi-keg
KEG is an image composition tool for KIWI image descriptions

%package -n obs-service-compose_kiwi_description
Summary:        An OBS service: generate KIWI description using KEG
Group:          Development/Tools/Building
Requires:       git
Requires:       python3-kiwi-keg = %version

%description -n obs-service-compose_kiwi_description
This is a source service for openSUSE Build Service.

The source service produces a KIWI image description through KEG from one or
more given git repositories that contain keg-recipes source tree. It supports
auto-generation of change log files from commit history.

%prep
%setup -q -n kiwi_keg-%{version}

%build
# Build Python 3 version
%python_build

# Build man pages
make -C doc man

%install
%python_install
make buildroot=%{buildroot}/ docdir=%{_defaultdocdir}/ install

%python_clone -a %{buildroot}%{_bindir}/keg
%python_clone -a %{buildroot}%{_bindir}/generate_recipes_changelog
%python_clone -a %{buildroot}%{_mandir}/man1/keg.1
%python_clone -a %{buildroot}%{_mandir}/man1/generate_recipes_changelog.1
%python_expand %fdupes %{buildroot}%{$python_sitelib}

%post
%python_install_alternative keg keg.1 generate_recipes_changelog
%python_install_alternative generate_recipes_changelog.1

%files -n python%{python3_pkgversion}-kiwi-keg
%python_alternative %{_bindir}/generate_recipes_changelog
%python_alternative %{_bindir}/keg
%{python_sitelib}/kiwi_keg
%{python_sitelib}/kiwi_keg-*
%license LICENSE
%doc README.rst
%python_alternative %{_mandir}/man1/keg.1%{?ext_man}
%python_alternative %{_mandir}/man1/generate_recipes_changelog.1%{?ext_man}

%files -n obs-service-compose_kiwi_description
%dir %{_usr}/lib/obs
%{_usr}/lib/obs/service

%changelog
