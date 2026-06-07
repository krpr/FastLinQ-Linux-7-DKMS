# DKMS usage on Debian/Ubuntu

This tree includes a `dkms.conf` for the Linux 7.0 compatible FastLinQ
kernel modules:

- `qed`
- `qede`
- `qedr`

`qedf` and `qedi` are FCoE/iSCSI storage offload drivers and are not part of
the default DKMS build. The Linux 7.0 SCSI API requires larger storage-driver
porting work before those modules should be enabled.

## Initial install

Install DKMS and kernel headers:

```sh
sudo apt install dkms linux-headers-$(uname -r)
```

Install firmware, udev rules, and modules once:

```sh
sudo make install
```

Register the source with DKMS:

```sh
sudo install -d /usr/src/qlgc-fastlinq-8.70.12.0
sudo tar --exclude=.git --exclude='*.o' --exclude='*.ko' \
  --exclude='*.mod' --exclude='*.mod.c' --exclude='.tmp_versions' \
  -C . -cf - . | sudo tar -C /usr/src/qlgc-fastlinq-8.70.12.0 -xf -

sudo dkms add -m qlgc-fastlinq -v 8.70.12.0
sudo dkms build -m qlgc-fastlinq -v 8.70.12.0 -k "$(uname -r)"
sudo dkms install -m qlgc-fastlinq -v 8.70.12.0 -k "$(uname -r)"
```

Check status:

```sh
dkms status qlgc-fastlinq
modinfo qede | grep filename
```

## Kernel updates

After a new Debian/Ubuntu kernel is installed, DKMS should rebuild and install
the modules automatically because `AUTOINSTALL="yes"` is set in `dkms.conf`.

To rebuild manually for a specific kernel:

```sh
sudo dkms autoinstall -k <kernel-version>
```

For example:

```sh
sudo dkms autoinstall -k 7.0.0-23-generic
```

If the driver is needed in initramfs, update initramfs after DKMS installs the
modules:

```sh
sudo update-initramfs -u -k <kernel-version>
```

## Removal

```sh
sudo dkms remove -m qlgc-fastlinq -v 8.70.12.0 --all
sudo rm -rf /usr/src/qlgc-fastlinq-8.70.12.0
```
