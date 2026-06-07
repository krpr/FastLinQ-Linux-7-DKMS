# Changelog

This changelog tracks the maintained Debian/Ubuntu fork of the QLogic/Cavium
FastLinQ 8.70.12.0 driver package.

## 8.70.12.0-linux7-maint.1 - 2026-06-08

Initial maintenance baseline for Linux 7.0 on Debian/Ubuntu.

### Added

- Added DKMS metadata in `dkms.conf` for automatic rebuilds of `qed`, `qede`
  and `qedr` after kernel updates.
- Added `DKMS.md` and `INSTALL.md` with Debian/Ubuntu installation,
  staged-install and kernel-update workflows.
- Added `scripts/build-dkms-deb.sh` for building a local Debian/Ubuntu DKMS
  source package.
- Added fixed package build entry points through `make deb`, `make package`,
  `make deb-info` and `PACKAGING.md`.
- Added `NOTICE.md` to preserve original QLogic/Cavium notices and document
  the 2026 maintenance attribution.
- Added top-level `WITH_STORAGE` switch. The default maintained module set is
  now `qed`, `qede` and `qedr`; storage offload modules can be attempted with
  `WITH_STORAGE=1`.
- Added top-level package name/version variables for the maintained tree.

### Changed

- Reworked module Makefiles to use kernel build system rules directly instead
  of overriding Kbuild module targets.
- Propagated `EXTRA_CFLAGS` through `ccflags-y` so compatibility probes reach
  every object in the module builds.
- Defaulted `DISABLE_WERROR=1` at the top level. Linux 7.0 headers and modern
  GCC emit compatibility warnings for this older driver tree; warnings should
  not block normal installation.
- Updated staged install behavior so `PREFIX=/path` installs under that root
  and skips live initramfs updates.
- Updated udev installation to run through `bash` and respect `DESTDIR`.

### Fixed

- Fixed Linux 7.0 build failures for `qed`, `qede` and `qedr`.
- Added compatibility for removed or changed kernel APIs, including:
  `strlcpy`, PCIe AER helpers, `local_clock`, sysfs binary attributes,
  `netif_napi_add_weight`, PTP `adjfine`, non-const `cyclecounter.read`,
  new `ethtool_rxfh_param`, `kernel_ethtool_ts_info` and `ethtool_keee`.
- Disabled legacy `qed`/`qede` devlink integration on Linux 7.0 where the
  driver implementation no longer matches the upstream devlink API.
- Fixed `qedr` compatibility with newer RDMA core signatures for `create_cq`
  and `reg_user_mr`.
- Fixed `qedr` compatibility for removed `in_irq()` and changed
  `ip_route_output()` signatures.
- Fixed `qedr` default `QED_DIR` resolution so standalone and top-level builds
  find the correct `Module.symvers`.

### Verification

Validated on Linux `7.0.0-22-generic`:

```sh
make clean
make PREFIX=/tmp/fastlinq-install install
```

The staged install produced:

- `qed.ko`
- `qede.ko`
- `qedr.ko`

Also validated the DKMS build command body:

```sh
make KVER=7.0.0-22-generic WITH_STORAGE=0 DISABLE_WERROR=1 subsystem
```

The test environment did not have the `dkms` command installed, so
`dkms add/build/install` was documented but not executed there.

### Known limitations

- `qedf` and `qedi` are not maintained in this baseline. Linux 7.0 SCSI/FCoE
  and iSCSI API changes require a larger storage-driver port before they should
  be enabled.
- Secure Boot module signing is site-specific and is not automated by this
  source tree.
- Future Linux kernels may require additional compatibility work. Treat each
  kernel update that breaks DKMS as a normal maintenance event: inspect the
  DKMS build log, add a scoped compatibility probe, rebuild, and update this
  changelog.
