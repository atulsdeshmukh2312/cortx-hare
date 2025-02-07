# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

# build number
%define h_build_num  %(test -n "$build_number" && echo "$build_number" || echo 1)

# motr version
%define h_motr_version %(rpm -q --whatprovides cortx-motr | xargs rpm -q --queryformat '%%{VERSION}-%%{RELEASE}')

# parallel build jobs
%define h_build_jobs_opt  %(test -n "$build_jobs" && echo "-j$build_jobs" || echo '')

Summary: Hare (Halon replacement)
Name: cortx-hare
Version: %{h_version}
Release: %{h_build_num}_%{h_gitrev}%{?dist}
License: Seagate
Group: System Environment/Daemons
Source: %{name}-%{h_version}.tar.gz

BuildRequires: binutils-devel
BuildRequires: cortx-motr
BuildRequires: cortx-motr-devel
BuildRequires: cortx-py-utils
BuildRequires: git
%if %{rhel} < 8
BuildRequires: python36
BuildRequires: python36-devel
BuildRequires: python36-pip
BuildRequires: python36-setuptools
%else
BuildRequires: python3
BuildRequires: python3-devel
BuildRequires: python3-pip
BuildRequires: python3-setuptools
%endif

Requires: consul >= 1.9.0, consul < 1.12.0
%if %{rhel} < 8
Requires: puppet-agent >= 6.13.0
%else
Requires: facter >= 3.14.2
%endif
Requires: jq
Requires: cortx-motr = %{h_motr_version}
Requires: cortx-py-utils
%if %{rhel} < 8
Requires: python36
%else
Requires: python3
%endif

Conflicts: halon

%description
Cluster monitoring and recovery for high-availability.

%prep
%setup -qn %{name}

%build
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
sed -i -e 's@^#!.*\.py3venv@#!/usr@' %{buildroot}/opt/seagate/cortx/hare/bin/*

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{_bindir}/*
%{_exec_prefix}/lib/systemd/system/*
%{_sharedstatedir}/hare/
%{_localstatedir}/motr/hax/
%{_sysconfdir}/cron.hourly/*
%{_sysconfdir}/logrotate.d/*
/opt/seagate/cortx/hare/*

%post
systemctl daemon-reload
install --directory --mode=0775 /var/lib/hare
groupadd --force hare
chgrp hare /var/lib/hare
chmod --changes g+w /var/lib/hare

%if %{rhel} < 8
# puppet-agent provides a newer version of facter, but sometimes it might not be
# available in /usr/bin/, so we need to fix this
if [[ ! -e /usr/bin/facter && -e /opt/puppetlabs/bin/facter ]] ; then
    ln -vsf /opt/puppetlabs/bin/facter /usr/bin/facter
fi
%endif

%postun
systemctl daemon-reload

# Instruct rpm's built-in python syntax linter /usr/lib/rpm/brp-python-bytecompile
# to target python3 syntax instead of the default python2 syntax, which yeilds
# linter errors, like
#   SyntaxError: invalid syntax
%global __python %{__python3}

# Consul binaries are stripped and don't contain build id, so rpmbuild fails
# with:
#   "ERROR: No build ID note found in consul"
%undefine _missing_build_ids_terminate_build
