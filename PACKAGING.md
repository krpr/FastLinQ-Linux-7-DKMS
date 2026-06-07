# FastLinQ package build flow

This is the maintained package flow for Debian/Ubuntu systems. The package is
a DKMS source package, not a prebuilt kernel-module package.

Before publishing a package, review `NOTICE.md` and keep the original
QLogic/Cavium notices plus the 2026 maintenance attribution in the distributed
source and package documentation.

## Build requirements

Install package build tools on the build host:

```sh
sudo apt update
sudo apt install dpkg-dev rsync tar
```

The target host that installs the package must have DKMS, build tools and
headers for the running kernel:

```sh
sudo apt install dkms build-essential linux-headers-$(uname -r)
```

## Standard build

Build the package from a clean git checkout:

```sh
git status --short
make deb
```

The output path is:

```sh
make deb-path
```

The default package is:

```text
dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint1_all.deb
```

`make deb` also validates the generated package by checking the Debian control
scripts and required payload files.

## Versioned build

When cutting a new maintenance package, update `CHANGELOG.md` first and then
build with an explicit Debian package version:

```sh
make deb DEB_VERSION=8.70.12.0-linux7maint2
```

Optional metadata:

```sh
make deb \
  DEB_VERSION=8.70.12.0-linux7maint2 \
  DEB_MAINTAINER="FastLinQ Maintainers <network@example.com>"
```

## Inspect package

```sh
make deb-info
```

This prints the package control metadata and the first part of the file list.

## Install on target host

Use `apt` so dependencies are resolved:

```sh
sudo apt install ./dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint1_all.deb
```

The package installs source into `/usr/src/qlgc-fastlinq-8.70.12.0`, installs
the required `qed` firmware and udev assets, and runs DKMS to build `qed`,
`qede` and `qedr` for the running kernel.

## Post-install checks

```sh
dkms status qlgc-fastlinq
modinfo qede | grep -E 'filename|version'
lsmod | grep -E 'qed|qede|qedr'
```

If package configuration fails, inspect:

```sh
sudo less /var/lib/dkms/qlgc-fastlinq/8.70.12.0/build/make.log
```
