PACKAGE_NAME := qlgc-fastlinq
PACKAGE_VERSION := 8.70.12.0
DEB_PACKAGE ?= $(PACKAGE_NAME)-dkms
DEB_VERSION ?= $(PACKAGE_VERSION)-linux7maint1
DEB_ARCH ?= all
DEB_MAINTAINER ?= FastLinQ Maintainers <root@localhost>
DEB_FILE := $(CURDIR)/dist/$(DEB_PACKAGE)_$(DEB_VERSION)_$(DEB_ARCH).deb
QED_DIR := $(CURDIR)/qed-8.70.12.0/src/
QEDE_DIR := $(CURDIR)/qede-8.70.12.0/src/
QEDR_DIR := $(CURDIR)/qedr-8.70.12.0/src/
QEDF_DIR := $(CURDIR)/qedf-8.70.12.0
QEDI_DIR := $(CURDIR)/qedi-8.70.12.0
LIBQEDR_DIR := $(CURDIR)//
WITH_STORAGE ?= 0
DISABLE_WERROR ?= 1
SUBDIRS := $(QED_DIR) $(QEDE_DIR) $(QEDR_DIR)
ifneq ($(WITH_STORAGE),0)
SUBDIRS += $(QEDF_DIR) $(QEDI_DIR)
endif
export QED_DIR
export QEDE_DIR
export DISABLE_WERROR

UBUNTU_DISTRO := $(shell lsb_release -is 2> /dev/null | grep Ubuntu)
ifeq ($(UBUNTU_DISTRO),)
    LIBQEDR_CONFIGURE_CMD := ./configure --prefix=/usr --libdir=${exec_prefix}/lib64 --sysconfdir=/etc
else
    LIBQEDR_CONFIGURE_CMD := ./configure --prefix=/usr --libdir=${exec_prefix}/lib --sysconfdir=/etc
endif

.PHONY: subsystem udev_install udev_uninstall install light_install clean deb package deb-info deb-path libqedr_uninstall libqedr libqedr_install libqedr_clean

ADDONS_DIR := add-ons

subsystem:
	@for dir in $(SUBDIRS); do		\
		$(MAKE) -C $$dir || exit 1;	\
	done

udev_install:
	@ - DESTDIR=$(PREFIX) bash $(ADDONS_DIR)/udev/udev_install.sh --install

udev_uninstall:
	@ - DESTDIR=$(PREFIX) bash $(ADDONS_DIR)/udev/udev_install.sh --uninstall

install: udev_install
	@for dir in $(SUBDIRS); do			\
		$(MAKE) -C $$dir install || exit 1;	\
	done

light_install: udev_install
	@for dir in $(SUBDIRS); do                              \
		$(MAKE) -C $$dir light_install || exit 1;       \
	done

clean:
	@for dir in $(SUBDIRS); do			\
		$(MAKE) -C $$dir clean || exit 1;	\
	done

deb package:
	@DEB_PACKAGE="$(DEB_PACKAGE)" \
	DEB_VERSION="$(DEB_VERSION)" \
	DEB_ARCH="$(DEB_ARCH)" \
	DEB_MAINTAINER="$(DEB_MAINTAINER)" \
		$(CURDIR)/scripts/build-dkms-deb.sh

deb-info:
	@dpkg-deb -I "$(DEB_FILE)"
	@dpkg-deb -c "$(DEB_FILE)" | sed -n '1,80p'

deb-path:
	@echo "$(DEB_FILE)"

libqedr_uninstall:
	- rm -f /etc/libibverbs.d/qedr.driver
	- rm -f /usr/local/etc/libibverbs.d/qedr.driver
	- rm -f /usr/lib64/libqedr*
	- rm -f /usr/lib64/libibverbs/libqedr*
	- rm -f /usr/lib/libqedr*
	- rm -f /usr/lib/libibverbs/libqedr*
	- rm -f /lib64/libqedr*
	- rm -f /lib64/libibverbs/libqedr*
	- rm -f /lib/libqedr*
	- rm -f /lib/libibverbs/libqedr*

libqedr:
	@(cd $(LIBQEDR_DIR) && exec $(LIBQEDR_CONFIGURE_CMD)) && $(MAKE) -C $(LIBQEDR_DIR)

libqedr_install:
	@(cd $(LIBQEDR_DIR) && exec $(LIBQEDR_CONFIGURE_CMD)) && $(MAKE) -C $(LIBQEDR_DIR) install

libqedr_clean:
	$(MAKE) clean -C $(LIBQEDR_DIR)
