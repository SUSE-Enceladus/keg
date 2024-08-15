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

%if 0%{?suse_version} > 1500
%bcond_without libalternatives
%else
%bcond_with libalternatives
%endif

%{?sle15_python_module_pythons}
Name:           python-kiwi-keg
Version:        2.1.1
Release:        0
URL:            https://github.com/SUSE-Enceladus/keg
Summary:        KEG - Image Composition Tool
License:        GPL-3.0-or-later
Source:         keg-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module Sphinx}
BuildRequires:  %{python_module Jinja2}
BuildRequires:  %{python_module schema}
BuildRequires:  %{python_module pytest}
BuildRequires:  %{python_module docopt}
BuildRequires:  %{python_module PyYAML}
# On TW the kiwi package is always the latest python default: python3-kiwi
# On Leap <15.5 and SLES15 <SP5 only one python exists: python3-kiwi
%if 0%{?suse_version} > 1600 || 0%{?sle_version} < 150500
BuildRequires:  python3-kiwi
%else
BuildRequires:  %{python_module kiwi}
%endif
BuildRequires:  fdupes
%if %{with libalternatives}
BuildRequires:  alts
Requires:       alts
%else
Requires(post): update-alternatives
Requires(postun):update-alternatives
%endif
Requires:       python-Sphinx
Requires:       python-Jinja2
Requires:       python-schema
Requires:       python-docopt
Requires:       python-PyYAML
Requires:       python-kiwi
Provides:       python3-kiwi-keg = %version
Obsoletes:      python3-kiwi-keg < %version
BuildArch:      noarch
%python_subpackages

%description
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
%setup -q -n keg-%{version}

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

%files %{python_files}
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
