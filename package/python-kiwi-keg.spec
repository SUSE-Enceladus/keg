#
# spec file for package python-kiwi-keg
#
# Copyright (c) 2025 SUSE LLC
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

%if 0%{?suse_version} >= 1600
%define pythons %{primary_python}
%else
%{?sle15_python_module_pythons}
%endif

# ------------------------------------------------------------------
# SLE-15-SP3 ships python-setuptools 40.x – too old for a plain
# PEP-517 build.  Everywhere else we have >= 42.
#
#   new_setuptools = 1   … modern setuptools (default)
#   new_setuptools = 0   … SLE-15-SP3 or older
# ------------------------------------------------------------------
%define new_setuptools 1
%if 0%{?sle_version} <= 150300
%define new_setuptools 0
%endif
# ------------------------------------------------------------------


%define skip_python2 1
%define skip_fdupes 1
%define upstream_name keg
Name:          python-kiwi-keg
Version:       2.1.1
Release:       0
URL:           https://github.com/SUSE-Enceladus/keg
Summary:       KEG - Image Composition Tool
Group:         Development/Tools/Building
License:       GPL-3.0-or-later
Source0:       %{upstream_name}-%{version}.tar.gz
# PATCH-FIX-UPSTREAM https://github.com/SUSE-Enceladus/keg/pull/154 Fix link to OBS documentation
Patch0:        fix-doc-link.patch
BuildRequires: %{pythons}-pip
BuildRequires: %{pythons}-setuptools
BuildRequires: %{pythons}-wheel
BuildRequires: %{pythons}-Jinja2
BuildRequires: %{pythons}-Sphinx
BuildRequires: %{pythons}-sphinx_rtd_theme
BuildRequires: python-rpm-macros
BuildRequires: fdupes
BuildRequires: make
Provides:      python3-kiwi-keg = %{version}
Provides:      python310-kiwi-keg = %{version}
Provides:      python311-kiwi-keg = %{version}
Provides:      python312-kiwi-keg = %{version}
Provides:      python313-kiwi-keg = %{version}
Obsoletes:     python3-kiwi-keg < %{version}
Obsoletes:     python310-kiwi-keg < %{version}
Obsoletes:     python311-kiwi-keg < %{version}
Obsoletes:     python312-kiwi-keg < %{version}
Obsoletes:     python313-kiwi-keg < %{version}
BuildArch:     noarch
Requires:      %{pythons}-Jinja2
Requires:      %{pythons}-PyYAML
Requires:      %{pythons}-docopt
Requires:      %{pythons}-schema
Requires:      %{pythons}-kiwi >= 9.21.21

%description
KEG is an image composition tool for KIWI image descriptions

%package -n obs-service-compose_kiwi_description
Summary:        An OBS service: generate KIWI description using KEG
Requires:       git
Requires:       %{name} = %{version}

%description -n obs-service-compose_kiwi_description
This is a source service for openSUSE Build Service.

The source service produces a KIWI image description through KEG from one or
more given git repositories that contain keg-recipes source tree. It supports
auto-generation of change log files from commit history.

%prep
%autosetup -p1 -n %{upstream_name}-%{version}

%if !%{new_setuptools}
# setuptools-40.x needs a minimal PEP-517 stub
cat > pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
EOF
%endif

%build
%if !%{new_setuptools}
# workaround for old setuptools
export PYTHONPATH=$PWD
export PIP_NO_BUILD_ISOLATION=1
%pyproject_wheel .
%else
%pyproject_wheel
%endif
# Build man pages
make -C doc man

%install
%pyproject_install
make buildroot=%{buildroot}/ docdir=%{_defaultdocdir}/ install
%python_expand fdupes %{buildroot}%{$python_sitelib}

%check

%files
%{_bindir}/%{upstream_name}
%{_bindir}/generate_recipes_changelog
%{python_sitelib}/kiwi_keg*
%license LICENSE
%doc README.rst
%{_mandir}/man1/%{upstream_name}.1%{?ext_man}
%{_mandir}/man1/generate_recipes_changelog.1%{?ext_man}

# OBS service
%files -n obs-service-compose_kiwi_description
%dir %{_prefix}/lib/obs
%dir %{_prefix}/lib/obs/service
%{_prefix}/lib/obs/service/*

%changelog
