#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

for tool in dpkg-deb md5sum rsync tar; do
	if ! command -v "$tool" >/dev/null 2>&1; then
		echo "$tool is required to build the package" >&2
		exit 1
	fi
done

dkms_name=$(sed -n 's/^PACKAGE_NAME="\([^"]*\)".*/\1/p' dkms.conf)
dkms_version=$(sed -n 's/^PACKAGE_VERSION="\([^"]*\)".*/\1/p' dkms.conf)

if [ -z "$dkms_name" ] || [ -z "$dkms_version" ]; then
	echo "failed to read PACKAGE_NAME/PACKAGE_VERSION from dkms.conf" >&2
	exit 1
fi

deb_package=${DEB_PACKAGE:-${dkms_name}-dkms}
deb_version=${DEB_VERSION:-${dkms_version}-linux7maint1}
deb_arch=${DEB_ARCH:-all}
maintainer=${DEB_MAINTAINER:-FastLinQ Maintainers <root@localhost>}

tmp_root=$(mktemp -d "${TMPDIR:-/tmp}/fastlinq-deb.XXXXXX")
trap 'rm -rf "$tmp_root"' EXIT

pkg_root="$tmp_root/${deb_package}_${deb_version}_${deb_arch}"
control_dir="$pkg_root/DEBIAN"
src_root="$pkg_root/usr/src/${dkms_name}-${dkms_version}"
doc_root="$pkg_root/usr/share/doc/$deb_package"
firmware_root="$pkg_root/lib/firmware/qed"
udev_rules_root="$pkg_root/etc/udev/rules.d"
udev_script_root="$pkg_root/lib/udev"
dist_dir="$repo_root/dist"

validate_deb() {
	local deb_path=$1
	local control_check=$tmp_root/control-check
	local members_file=$tmp_root/package-members
	local member=

	mkdir -p "$control_check"
	dpkg-deb -e "$deb_path" "$control_check"
	sh -n "$control_check/postinst"
	sh -n "$control_check/prerm"
	sh -n "$control_check/postrm"

	dpkg-deb --fsys-tarfile "$deb_path" | tar -tf - > "$members_file"
	for member in \
		"./usr/src/${dkms_name}-${dkms_version}/dkms.conf" \
		"./usr/src/${dkms_name}-${dkms_version}/Makefile" \
		"./usr/src/${dkms_name}-${dkms_version}/qed-8.70.12.0/src/qed_main.c" \
		"./usr/src/${dkms_name}-${dkms_version}/qede-8.70.12.0/src/qede_main.c" \
		"./usr/src/${dkms_name}-${dkms_version}/qedr-8.70.12.0/src/main.c" \
		"./lib/firmware/qed/qed_init_values-8.70.4.0.bin" \
		"./lib/firmware/qed/qed_init_values_zipped-8.70.4.0.bin" \
		"./etc/udev/rules.d/99-qed.rules" \
		"./lib/udev/qed_udev_dbg.sh" \
		"./usr/share/doc/${deb_package}/INSTALL.md" \
		"./usr/share/doc/${deb_package}/PACKAGING.md"; do
		if ! grep -Fx "$member" "$members_file" >/dev/null; then
			echo "package validation failed: missing $member" >&2
			exit 1
		fi
	done
}

mkdir -p "$control_dir" "$src_root" "$doc_root" "$firmware_root" \
	"$udev_rules_root" "$udev_script_root" "$dist_dir"

rsync -a \
	--exclude='/.git/' \
	--exclude='/.agents/' \
	--exclude='/.codex/' \
	--exclude='/build/' \
	--exclude='/dist/' \
	--exclude='/.tmp_versions/' \
	--exclude='.DS_Store' \
	--exclude='*.deb' \
	--exclude='*.o' \
	--exclude='*.ko' \
	--exclude='*.mod' \
	--exclude='*.mod.c' \
	--exclude='Module.symvers' \
	--exclude='modules.order' \
	--exclude='.*.cmd' \
	./ "$src_root/"

install -m 0644 add-ons/udev/99-qed.rules "$udev_rules_root/99-qed.rules"
install -m 0755 add-ons/udev/qed_udev_dbg.sh "$udev_script_root/qed_udev_dbg.sh"

for firmware in qed-8.70.12.0/src/qed_init_values-*.bin \
	qed-8.70.12.0/src/qed_init_values_zipped-*.bin; do
	install -m 0644 "$firmware" "$firmware_root/"
done

install -m 0644 COPYING "$doc_root/copyright"
install -m 0644 INSTALL.md "$doc_root/INSTALL.md"
install -m 0644 DKMS.md "$doc_root/DKMS.md"
install -m 0644 PACKAGING.md "$doc_root/PACKAGING.md"
install -m 0644 CHANGELOG.md "$doc_root/changelog"

cat > "$control_dir/control" <<EOF
Package: $deb_package
Version: $deb_version
Section: kernel
Priority: optional
Architecture: $deb_arch
Maintainer: $maintainer
Depends: dkms, build-essential, kmod, udev
Recommends: linux-headers-generic | linux-headers-amd64
Description: DKMS source package for QLogic FastLinQ drivers
 Maintained Debian/Ubuntu DKMS package for the FastLinQ qed, qede and
 qedr kernel modules.
 .
 The package installs the driver source under /usr/src/${dkms_name}-${dkms_version},
 installs the required qed firmware and udev files, and uses DKMS to build
 modules for the running kernel during package configuration.
EOF

cat > "$control_dir/postinst" <<EOF
#!/bin/sh
set -e

NAME="$dkms_name"
VERSION="$dkms_version"
DEB_PACKAGE="$deb_package"

case "\$1" in
configure)
	if ! command -v dkms >/dev/null 2>&1; then
		echo "dkms is required. Install dkms and re-run: dpkg --configure \$DEB_PACKAGE" >&2
		exit 1
	fi

	kernel="\${KERNELRELEASE:-\$(uname -r)}"
	if [ ! -e "/lib/modules/\$kernel/build" ]; then
		echo "missing kernel headers for \$kernel" >&2
		echo "install linux-headers-\$kernel and re-run: dpkg --configure \$DEB_PACKAGE" >&2
		exit 1
	fi

	if ! dkms add -m "\$NAME" -v "\$VERSION"; then
		dkms remove -m "\$NAME" -v "\$VERSION" --all >/dev/null 2>&1 || true
		dkms add -m "\$NAME" -v "\$VERSION"
	fi

	dkms build -m "\$NAME" -v "\$VERSION" -k "\$kernel"
	dkms install -m "\$NAME" -v "\$VERSION" -k "\$kernel"

	if command -v depmod >/dev/null 2>&1; then
		depmod -a "\$kernel" || true
	fi
	if command -v update-initramfs >/dev/null 2>&1; then
		update-initramfs -u -k "\$kernel" || true
	fi
	if command -v udevadm >/dev/null 2>&1; then
		udevadm control --reload-rules || true
	fi
	;;
esac

exit 0
EOF

cat > "$control_dir/prerm" <<EOF
#!/bin/sh
set -e

NAME="$dkms_name"
VERSION="$dkms_version"

case "\$1" in
remove|upgrade|deconfigure)
	if command -v dkms >/dev/null 2>&1; then
		dkms remove -m "\$NAME" -v "\$VERSION" --all || true
	fi
	;;
esac

exit 0
EOF

cat > "$control_dir/postrm" <<EOF
#!/bin/sh
set -e

NAME="$dkms_name"
VERSION="$dkms_version"

case "\$1" in
purge)
	if command -v dkms >/dev/null 2>&1; then
		dkms remove -m "\$NAME" -v "\$VERSION" --all >/dev/null 2>&1 || true
	fi
	;;
esac

exit 0
EOF

chmod 0755 "$control_dir/postinst" "$control_dir/prerm" "$control_dir/postrm"
(
	cd "$pkg_root"
	find . -path './DEBIAN' -prune -o -type f -print0 |
		sort -z |
		while IFS= read -r -d '' path; do
			md5sum "${path#./}"
		done
) > "$control_dir/md5sums"
find "$pkg_root" -type d -exec chmod 0755 {} +
find "$src_root" -type f -exec chmod 0644 {} +
find "$src_root" -type f -name '*.sh' -exec chmod 0755 {} +
chmod 0644 "$control_dir/control"
chmod 0644 "$control_dir/md5sums"
chmod 0755 "$control_dir/postinst" "$control_dir/prerm" "$control_dir/postrm"
chmod 0644 "$udev_rules_root/99-qed.rules" "$firmware_root"/*.bin
chmod 0755 "$udev_script_root/qed_udev_dbg.sh"

deb_path="$dist_dir/${deb_package}_${deb_version}_${deb_arch}.deb"
dpkg-deb --root-owner-group --build "$pkg_root" "$deb_path"
validate_deb "$deb_path"

echo "$deb_path"
