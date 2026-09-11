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
dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint2_all.deb
```

`make deb` also validates the generated package by checking the Debian control
scripts and required payload files.

## Versioned build

The current maintenance revision is `8.70.12.0-linux7maint2`. Its Debian
revision changes while the upstream driver and DKMS version remain
`8.70.12.0`. To build with an explicit Debian package version:

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
sudo apt install ./dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint2_all.deb
```

The package installs source into `/usr/src/qlgc-fastlinq-8.70.12.0`, installs
the required `qed` firmware and udev assets, and runs DKMS to build `qed`,
`qede` and `qedr` for the running kernel.

## Upgrading maintenance revisions

The existing package upgrade scripts remove the old DKMS registration for all
kernels, then build for `KERNELRELEASE` or, when unset, the running kernel.
They do not immediately rebuild every previously installed kernel. Before
upgrading, record the kernels you need from `dkms status` and ensure their
matching headers are installed.

After upgrading, explicitly rebuild and install for each required kernel.
For example, for an installed Ubuntu `7.0.0-31-generic` kernel:

```sh
qlogic_kernel=7.0.0-31-generic
sudo dkms build -m qlgc-fastlinq -v 8.70.12.0 -k "$qlogic_kernel" --force
sudo dkms install -m qlgc-fastlinq -v 8.70.12.0 -k "$qlogic_kernel" --force
sudo update-initramfs -u -k "$qlogic_kernel"
```

Repeat with each other kernel you intend to boot. The package's current
post-install script does not propagate an initramfs update failure, so check
the direct update command and DKMS state before a later reboot. These commands
update disk files; they do not request a reboot or reload the running driver.

The maintenance fixes were validated through source-patch deployments on
Ubuntu `7.0.0-29`, `-30`, and `-31`. A complete upgrade of the newly versioned
`.deb` has not been tested. This release does not change package lifecycle
behavior.

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
