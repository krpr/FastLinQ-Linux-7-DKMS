# FastLinQ driver install guide

This repository is maintained as a Debian/Ubuntu-oriented FastLinQ driver tree
for Linux 7.0 kernels. The default maintained modules are:

- `qed`: core hardware driver
- `qede`: Ethernet driver
- `qedr`: RoCE/RDMA driver

The storage offload drivers `qedf` and `qedi` are not built by default. They
depend on FCoE/iSCSI and SCSI kernel APIs which changed substantially in Linux
7.0, so treat them as not maintained in this branch unless they are explicitly
ported and tested.

Read `NOTICE.md` for copyright, license and 2026 maintenance attribution
notes. Keep the original QLogic/Cavium notices and `COPYING` intact when
redistributing this driver.

## Requirements

Install the build tools and headers for the target kernel:

```sh
sudo apt update
sudo apt install build-essential linux-headers-$(uname -r)
```

For DKMS-based maintenance across kernel updates, also install DKMS:

```sh
sudo apt install dkms
```

If Secure Boot is enabled, unsigned out-of-tree modules may fail to load. Either
enroll a Machine Owner Key and sign the modules, or disable Secure Boot according
to your site policy.

## One-time direct install

Use this when installing for the currently running kernel only:

```sh
make clean
sudo make install
sudo depmod -a
```

This installs firmware, udev rules and the default kernel modules. The default
module set is `qed`, `qede` and `qedr`.

Load the Ethernet driver:

```sh
sudo modprobe qede
```

For RoCE/RDMA support:

```sh
sudo modprobe qedr
```

Check the installed module path and version:

```sh
modinfo qede | grep -E 'filename|version'
lsmod | grep -E 'qed|qede|qedr'
dmesg | grep -iE 'qed|qede|qedr' | tail -50
```

## DKMS install

DKMS is the recommended deployment model for machines that receive kernel
updates. It rebuilds and installs the driver modules for each new kernel.

First install the driver once for firmware and udev assets:

```sh
sudo make install
```

Then copy this source tree into `/usr/src` and register it with DKMS:

```sh
sudo install -d /usr/src/qlgc-fastlinq-8.70.12.0
sudo tar --exclude=.git --exclude='*.o' --exclude='*.ko' \
  --exclude='*.mod' --exclude='*.mod.c' --exclude='.tmp_versions' \
  -C . -cf - . | sudo tar -C /usr/src/qlgc-fastlinq-8.70.12.0 -xf -

sudo dkms add -m qlgc-fastlinq -v 8.70.12.0
sudo dkms build -m qlgc-fastlinq -v 8.70.12.0 -k "$(uname -r)"
sudo dkms install -m qlgc-fastlinq -v 8.70.12.0 -k "$(uname -r)"
```

Confirm DKMS state:

```sh
dkms status qlgc-fastlinq
modinfo qede | grep filename
```

## DKMS deb package

For repeatable deployment on Debian/Ubuntu hosts, build a local DKMS `.deb`:

```sh
make deb
```

The generated package is written to `dist/`, for example:

```sh
dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint2_all.deb
```

Install it with `apt` so dependencies are resolved:

```sh
sudo apt install ./dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint2_all.deb
```

This package installs the driver source into `/usr/src/qlgc-fastlinq-8.70.12.0`,
installs the required `qed` firmware and udev files, and runs DKMS to compile
and install `qed`, `qede` and `qedr` for the running kernel. It does not ship
prebuilt `.ko` files, because those are tied to one exact kernel build.

See `PACKAGING.md` for the maintained package build and release flow.

When upgrading an existing maintenance package, follow
[Upgrading maintenance revisions](PACKAGING.md#upgrading-maintenance-revisions)
to rebuild every kernel you intend to boot; the existing package upgrade
scripts initially rebuild only the running kernel.

## Kernel updates

When a new Debian/Ubuntu kernel is installed, DKMS should automatically build
and install `qed`, `qede` and `qedr` because `AUTOINSTALL="yes"` is set in
`dkms.conf`.

After a kernel update:

```sh
dkms status qlgc-fastlinq
sudo dkms autoinstall -k <new-kernel-version>
sudo update-initramfs -u -k <new-kernel-version>
```

Example:

```sh
sudo dkms autoinstall -k 7.0.0-23-generic
sudo update-initramfs -u -k 7.0.0-23-generic
```

If DKMS fails after a future kernel update, check that matching headers are
installed:

```sh
sudo apt install linux-headers-<new-kernel-version>
sudo dkms build -m qlgc-fastlinq -v 8.70.12.0 -k <new-kernel-version>
```

Review the DKMS build log:

```sh
sudo less /var/lib/dkms/qlgc-fastlinq/8.70.12.0/build/make.log
```

## Staged install

For packaging or validation without writing into the live system:

```sh
make clean
make PREFIX=/tmp/fastlinq-install install
find /tmp/fastlinq-install/lib/modules -name '*.ko' -print
```

## Optional storage modules

The old package also contains:

- `qedf`: FCoE storage offload
- `qedi`: iSCSI storage offload

They are excluded from the default build. To attempt a storage build during
future porting work:

```sh
make WITH_STORAGE=1
```

Do not enable these modules in production until they have been fully ported to
the target kernel SCSI APIs and tested.

## Uninstall

Remove DKMS-managed modules:

```sh
sudo dkms remove -m qlgc-fastlinq -v 8.70.12.0 --all
sudo rm -rf /usr/src/qlgc-fastlinq-8.70.12.0
sudo depmod -a
```

Unload modules from a running system:

```sh
sudo modprobe -r qedr
sudo modprobe -r qede
sudo modprobe -r qed
```

If interfaces are up or RDMA resources are active, stop those services before
unloading the modules.
