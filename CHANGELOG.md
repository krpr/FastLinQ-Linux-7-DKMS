# Changelog

This changelog tracks the maintained Debian/Ubuntu fork of the QLogic/Cavium
FastLinQ 8.70.12.0 driver package.

## 8.70.12.0-linux7maint2 - 2026-09-12

Maintenance fixes for Ubuntu `7.0.0-31` DKMS compilation and the `qed`
attention descriptor array overrun. The upstream driver and DKMS version
remain `8.70.12.0`; only the Debian package version advances.

### Fixed

- Fixed the `qedr` compatibility probe to detect the exact
  `ib_umem_num_dma_blocks` symbol. Ubuntu `7.0.0-31` headers removed
  `rdma_umem_for_each_dma_block` but retained the counting helper; probing for
  the iterator incorrectly selected the unavailable legacy
  `ib_umem_page_count` API and broke compilation.
- Preserved existing queue counts in firmware 4 KiB pages, MR counts in
  `PAGE_SIZE` pages and the legacy counting fallback.
- Corrected the ninth `qed` AEU descriptor row's reserved length from 9 to 25
  bits, matching the register specification's reserved bits `[31:7]`. The old
  row covered only 16 bits and allowed descriptor walks to enter zero padding
  and overrun the 32-entry array.
- Added array-size bounds to all three attention descriptor walkers and made
  the initialization descriptor index unsigned. No flexible-array layout,
  allocation size or driver ABI was changed.

### Added

- Added `tests/test_qedr_umem_compat.py` for modern headers with and without
  the removed iterator, the legacy API, 4 KiB/64 KiB page sizes, count
  arithmetic and exact-symbol detection.
- Added `tests/test_qed_attention_bounds.py` to exercise the actual descriptor
  table, BB translation and initialization logic through inert user-space
  mocks. Coverage includes all nine 32-bit rows, AH/BB parity masks, UBSAN and
  bounded rejection of the original short row.

### Changed

- Updated the default Debian package version and installation examples to
  `8.70.12.0-linux7maint2`.
- Replaced the suggested repository name with the public
  [krpr/FastLinQ-Linux-7-DKMS](https://github.com/krpr/FastLinQ-Linux-7-DKMS)
  project identity.
- Documented that the existing package upgrade flow rebuilds the running
  kernel; other installed kernels need explicit review and rebuilding as
  described in `PACKAGING.md`.

### Verification

- Completed DKMS build and install of `qed`, `qede` and `qedr` on Ubuntu
  `7.0.0-29-generic`, `7.0.0-30-generic` and `7.0.0-31-generic`.
- Verified that installed module files matched the DKMS outputs. Each QLogic
  module present in the checked initramfs images matched its installed/DKMS
  copy, covering both initramfs-tools and dracut image-generation paths.
- Passed the user-space UMEM compatibility and attention bounds regression
  tests described above, including UBSAN checks for the descriptor logic.
- Booted a Hyper-V VF on `7.0.0-31-generic` with the updated module and link
  up, with no UBSAN report observed during that boot.

### Known limitations

- The bare-metal PF reboot regression for the original attention failure is
  still pending. The VF boot does not exercise that PF initialization path.
- These results validate the source patches and DKMS modules. The new
  `linux7maint2` `.deb` has not been built, and its package upgrade path has not
  been fully tested. See `PACKAGING.md` for the required package checks and
  multi-kernel upgrade handling.
- Existing optional RDMA/tunnel messages and module-signature trust warnings
  were not changed. Signing artifacts alone do not establish Secure Boot
  trust.
- `qedf` and `qedi` remain outside the maintained default module set.

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
- Added `README.md` for GitHub publishing under the `FastLinQ Linux 7 DKMS`
  project name, including the original `8.70.12.0` baseline and maintenance
  change summary.
- Added `README.zh-CN.md` and `CHANGELOG.zh-CN.md`; the Chinese changelog
  tracks this maintenance fork only and does not translate the original
  QLogic/Cavium release history.
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

In a Hyper-V + VF deployment, the Ubuntu inbox `qede` driver was observed to
show the adapter as degraded, with SR-IOV not running. This maintained driver
was observed to show the adapter as OK, with SR-IOV active.

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
