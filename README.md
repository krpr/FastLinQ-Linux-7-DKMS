# FastLinQ Linux 7 DKMS

Unofficial Debian/Ubuntu maintenance fork based on the original QLogic/Cavium
FastLinQ Linux driver package version `8.70.12.0`, focused on Linux 7.0
kernels and DKMS-based deployment.

Suggested GitHub repository name:

```text
fastlinq-linux7-dkms
```

## Scope

This tree maintains the default network/RDMA module set:

- `qed`: FastLinQ core hardware driver
- `qede`: Ethernet driver
- `qedr`: RoCE/RDMA driver

The legacy storage offload modules are kept in the source tree but are not part
of the maintained default build:

- `qedf`: FCoE storage offload
- `qedi`: iSCSI storage offload

`qedf` and `qedi` are excluded from the default install and DKMS package because
Linux 7.0 SCSI, FCoE and iSCSI API changes require a separate storage-driver
port. Do not enable them in production unless they have been explicitly ported
and tested.

## Maintenance Changes From 8.70.12.0

This fork keeps the original `8.70.12.0` driver lineage and adds the minimum
maintenance needed for current Debian/Ubuntu deployment:

- Linux 7.0 build fixes for `qed`, `qede` and `qedr`.
- DKMS metadata for automatic rebuilds after kernel updates.
- Local DKMS `.deb` packaging through `make deb`.
- Default build narrowed to the maintained network/RDMA modules: `qed`,
  `qede` and `qedr`.
- Storage offload modules `qedf` and `qedi` excluded by default through
  `WITH_STORAGE=0`.
- Kernel build cleanup using normal Kbuild module rules and propagated
  compatibility flags through `ccflags-y`.
- Debian/Ubuntu-oriented staged install behavior with `PREFIX=/path`.
- udev installation updated to use `bash` and respect `DESTDIR`.
- `DISABLE_WERROR=1` by default so modern compiler warnings do not block
  normal installation of this older driver tree.
- Compatibility shims and API updates for Linux 7.0 changes, including
  `strlcpy`, PCIe AER helpers, `local_clock`, sysfs binary attributes,
  `netif_napi_add_weight`, PTP `adjfine`, `cyclecounter.read`,
  `ethtool_rxfh_param`, `kernel_ethtool_ts_info` and `ethtool_keee`.
- RDMA compatibility fixes for newer `create_cq` and `reg_user_mr`
  signatures, removed `in_irq()` usage and changed `ip_route_output()`
  signatures.
- Legacy `qed`/`qede` devlink integration disabled on Linux 7.0 where the old
  implementation no longer matches the upstream devlink API.
- Documentation added for installation, DKMS operation, `.deb` packaging,
  maintenance notices and changelog tracking.

See `CHANGELOG.md` for the full maintenance log.

## Quick Install

Build a local DKMS `.deb` package:

```sh
make deb
```

Install it on the target Debian/Ubuntu host:

```sh
sudo apt install ./dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint1_all.deb
```

The package installs source into `/usr/src/qlgc-fastlinq-8.70.12.0`, installs
the required `qed` firmware and udev files, and uses DKMS to build `qed`,
`qede` and `qedr` for the running kernel.

## Requirements

On the target host:

```sh
sudo apt update
sudo apt install dkms build-essential linux-headers-$(uname -r)
```

If Secure Boot is enabled, unsigned out-of-tree modules may fail to load. Use
your site module-signing process or disable Secure Boot according to policy.

## Kernel Updates

The DKMS package sets `AUTOINSTALL="yes"`, so Debian/Ubuntu kernel updates
should trigger automatic rebuilds for `qed`, `qede` and `qedr`.

Manual rebuild for a specific kernel:

```sh
sudo dkms autoinstall -k <kernel-version>
sudo update-initramfs -u -k <kernel-version>
```

Check DKMS state:

```sh
dkms status qlgc-fastlinq
modinfo qede | grep -E 'filename|version'
```

## Direct Source Install

For one-time installation on the currently running kernel:

```sh
make clean
sudo make install
sudo depmod -a
```

The direct install path also defaults to `qed`, `qede` and `qedr` only.

## Package Build Flow

Standard package commands:

```sh
make deb
make deb-path
make deb-info
```

For a new maintenance package:

```sh
make deb DEB_VERSION=8.70.12.0-linux7maint2
```

See `PACKAGING.md` for the full release flow.

## Verification

This maintained baseline was validated on Linux `7.0.0-22-generic` with:

```sh
make clean
make PREFIX=/tmp/fastlinq-install install
```

The staged install produced:

- `qed.ko`
- `qede.ko`
- `qedr.ko`

The DKMS build command body was also validated:

```sh
make KVER=7.0.0-22-generic WITH_STORAGE=0 DISABLE_WERROR=1 subsystem
```

## Documentation

- `INSTALL.md`: installation, DKMS and uninstall guide
- `DKMS.md`: DKMS-specific workflow
- `PACKAGING.md`: `.deb` build and release flow
- `CHANGELOG.md`: maintenance changelog
- `NOTICE.md`: copyright, license and maintenance attribution notices

## License And Notices

The original driver source retains its QLogic/Cavium copyright and license
notices. The GPLv2 license text is in `COPYING` and should remain verbatim.

The 2026 maintenance work in this repository is distributed under the same
GPLv2 terms as the driver tree. See `NOTICE.md` before publishing packages or
redistributing modified source.

QLogic, Cavium, Marvell and FastLinQ names are used only to identify the
hardware family and upstream driver lineage. This project is not an official
QLogic, Cavium or Marvell release.
