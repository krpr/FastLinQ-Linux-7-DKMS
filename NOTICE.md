# FastLinQ maintenance notices

This repository is a maintained Debian/Ubuntu-oriented fork of the
QLogic/Cavium FastLinQ 8.70.12.0 Linux driver package.

## Original notices

Original QLogic and Cavium copyright, license and warranty notices are retained
in the source tree. Do not remove or rewrite those notices when modifying or
redistributing this driver.

The driver source files identify the original copyright holders, including
QLogic Corporation and Cavium, Inc. Many files are marked as licensed under the
GNU General Public License version 2, available in `COPYING`.

`COPYING` is the GPLv2 license text. It should remain verbatim.

## 2026 maintenance statement

Copyright (c) 2026 FastLinQ Maintainers.

The 2026 maintenance work in this repository covers Linux 7.0 compatibility,
Debian/Ubuntu installation behavior, DKMS integration, DKMS `.deb` packaging,
documentation and related build-system changes.

These maintenance changes are distributed under the same GPLv2 terms as the
driver tree. No additional restrictions are imposed.

## Distribution note

When distributing this driver, keep the complete corresponding source available
with the package or through an equivalent source distribution path. The DKMS
package produced by `make deb` installs source into
`/usr/src/qlgc-fastlinq-8.70.12.0` and builds modules locally for the target
kernel.

## Product and trademark note

QLogic, Cavium, Marvell and FastLinQ names are used only to identify the
hardware family and upstream driver lineage. This maintained fork is not
presented as an official QLogic, Cavium or Marvell release.
