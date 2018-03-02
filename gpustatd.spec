Name:		gpustatd
Version:	0.1
Release:	1%{?dist}
Summary:	Nvidia GPU Fan controller from Minotaur project
Group:		MIT
License:	Proprietary
URL:		https://github.com/m4rkw/gpustatd
Source0:	%{name}-%{version}.tar.gz
Source1:	gpustatd.service


BuildRequires:	PyYAML
BuildRequires:	nuitka

%description
gpustatd is a fan control daemon intended for use with Excavator by Nicehash.
It serves as a lightweight and decoupled mechanism for regulating fan speeds
on Nvidia cards when running intensive processes such as mining.

%prep
%setup -q

%build
nuitka --recurse-all gpustatd.py
mv gpustatd.exe gpustatd

%install
mkdir -p %{buildroot}/%{_bindir}
install --mode=755 gpustatd %{buildroot}/%{_bindir}/

mkdir -p %{buildroot}/%{_sysconfdir}
install --mode=644 gpustatd.conf.example %{buildroot}/%{_sysconfdir}/gpustatd.conf

mkdir -p %{buildroot}/%{_docdir}/%{name}-%{version}
install --mode=644 LICENSE README.md %{buildroot}/%{_docdir}/%{name}-%{version}/

mkdir -p %{buildroot}/%{_unitdir}
install --mode=644 %{SOURCE1} %{buildroot}/%{_unitdir}/gpustatd.service

mkdir -p %{buildroot}/var/log/gpustatd


%pre
if [ "$1" = "1" ]; then
        useradd --home-dir=/tmp gpustatd
fi


%postun
if [ "$1" = "0" ]; then
        userdel gpustatd
fi
i

%files
%defattr(-,root,root)
%{_sysconfdir}/gpustatd.conf
%{_unitdir}/gpustatd.service
%doc README.md LICENSE
%{_bindir}/gpustatd
%attr(755,gpustatd,root) /var/log/gpustatd


%changelog

