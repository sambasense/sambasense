Name:           sambasense
Version:        1.1.1
Release:        1%{?dist}
Summary:        Samba Configuration & Management Application
License:        MIT
URL:            https://github.com/sambasense/sambasense
Source0:        sambasense-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       python3 >= 3.10
Requires:       python3-qt6
Requires:       samba
Requires:       samba-client
Requires:       cifs-utils

%description
SambaSense is a desktop application for installing, configuring, and
managing Samba shares. Features include rich storage visualizations
with pie charts and line graphs, Material-You theming with dark/light
modes, and a full CLI interface.

%prep
%autosetup -n sambasense-%{version}

%build
%py3_build

%install
%py3_install

# Desktop file
install -Dm644 packaging/rpm/sambasense.desktop %{buildroot}%{_datadir}/applications/sambasense.desktop

# Icon
install -Dm644 assets/sambasense.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/sambasense.svg

%files
%license LICENSE
%{python3_sitelib}/sambasense/
%{python3_sitelib}/sambasense-*.egg-info/
%{_bindir}/sambasense
%{_datadir}/applications/sambasense.desktop
%{_datadir}/icons/hicolor/scalable/apps/sambasense.svg

%changelog
* Fri Feb 14 2026 SambaSense <contact@sambasense.com> - 1.0.0-1
- Initial release
