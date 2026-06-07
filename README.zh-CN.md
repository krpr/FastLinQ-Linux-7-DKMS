# FastLinQ Linux 7 DKMS

这是一个非官方 Debian/Ubuntu 后期维护分支，基于原 QLogic/Cavium FastLinQ
Linux 驱动包 `8.70.12.0`，目标是适配 Linux 7.0 内核，并提供 DKMS 化部署。

建议的 GitHub 仓库名：

```text
fastlinq-linux7-dkms
```

## 维护范围

本分支默认维护网络/RDMA 模块：

- `qed`：FastLinQ 核心硬件驱动
- `qede`：以太网驱动
- `qedr`：RoCE/RDMA 驱动

旧的存储卸载模块仍保留在源码树中，但不属于默认维护和默认构建范围：

- `qedf`：FCoE 存储卸载
- `qedi`：iSCSI 存储卸载

`qedf` 和 `qedi` 默认不会被 `make install`、DKMS 或 deb 包构建/安装。Linux
7.0 的 SCSI、FCoE、iSCSI API 变化较大，这两个模块需要单独移植和测试后才能
用于生产环境。

## 相比原 8.70.12.0 的维护内容

本分支保留原 `8.70.12.0` 驱动谱系，在此基础上增加当前 Debian/Ubuntu 部署所
需的维护改动：

- 修复 `qed`、`qede`、`qedr` 在 Linux 7.0 上的构建问题。
- 增加 DKMS 元数据，支持内核更新后的自动重建。
- 增加本地 DKMS `.deb` 打包流程，标准入口为 `make deb`。
- 默认构建范围收敛到已维护的 `qed`、`qede`、`qedr`。
- 通过 `WITH_STORAGE=0` 默认排除 `qedf` 和 `qedi`。
- 清理内核模块构建流程，使用标准 Kbuild 规则，并通过 `ccflags-y` 传递兼容性
  编译参数。
- 支持 Debian/Ubuntu 风格的 staged install：`PREFIX=/path`。
- udev 安装流程改为通过 `bash` 执行，并支持 `DESTDIR`。
- 默认启用 `DISABLE_WERROR=1`，避免现代编译器对旧驱动树产生的 warning 阻断
  正常安装。
- 增加 Linux 7.0 兼容修复，包括 `strlcpy`、PCIe AER helpers、
  `local_clock`、sysfs binary attributes、`netif_napi_add_weight`、PTP
  `adjfine`、`cyclecounter.read`、`ethtool_rxfh_param`、
  `kernel_ethtool_ts_info` 和 `ethtool_keee`。
- 修复较新 RDMA core API 下的 `create_cq`、`reg_user_mr` 签名变化，移除
  `in_irq()` 依赖，并适配 `ip_route_output()` 签名变化。
- 在 Linux 7.0 上禁用旧的 `qed`/`qede` devlink 集成，因为旧实现已经不匹配
  当前上游 devlink API。
- 在 Hyper-V + VF 环境中，Ubuntu inbox `qede` 驱动被观察到显示 VF 状态为
  “已降级 (SR-IOV 未运行)”。本维护驱动被观察到显示为“确定 (SR-IOV 活动)”。
- 增加安装、DKMS、deb 打包、维护声明和 changelog 文档。

完整维护记录见 `CHANGELOG.zh-CN.md` 和 `CHANGELOG.md`。

## 快速安装

构建本地 DKMS `.deb` 包：

```sh
make deb
```

在目标 Debian/Ubuntu 主机上安装：

```sh
sudo apt install ./dist/qlgc-fastlinq-dkms_8.70.12.0-linux7maint1_all.deb
```

该包会把源码安装到 `/usr/src/qlgc-fastlinq-8.70.12.0`，安装 `qed` 所需固件和
udev 文件，并通过 DKMS 为当前内核构建 `qed`、`qede`、`qedr`。

## 依赖

目标主机需要：

```sh
sudo apt update
sudo apt install dkms build-essential linux-headers-$(uname -r)
```

如果启用了 Secure Boot，未签名的第三方内核模块可能无法加载。请按现场策略
签名模块或关闭 Secure Boot。

## 内核更新

DKMS 包设置了 `AUTOINSTALL="yes"`，Debian/Ubuntu 安装新内核时应自动为
`qed`、`qede`、`qedr` 重建模块。

手动为指定内核重建：

```sh
sudo dkms autoinstall -k <kernel-version>
sudo update-initramfs -u -k <kernel-version>
```

检查 DKMS 状态：

```sh
dkms status qlgc-fastlinq
modinfo qede | grep -E 'filename|version'
```

## 源码直接安装

仅针对当前运行内核的一次性安装：

```sh
make clean
sudo make install
sudo depmod -a
```

源码直接安装也默认只安装 `qed`、`qede`、`qedr`。

## 打包流程

标准打包命令：

```sh
make deb
make deb-path
make deb-info
```

发布新的维护包时可以指定版本：

```sh
make deb DEB_VERSION=8.70.12.0-linux7maint2
```

完整发布流程见 `PACKAGING.md`。

## 验证记录

维护基线已在 Linux `7.0.0-22-generic` 上验证：

```sh
make clean
make PREFIX=/tmp/fastlinq-install install
```

staged install 产出：

- `qed.ko`
- `qede.ko`
- `qedr.ko`

同时验证了 DKMS 构建命令主体：

```sh
make KVER=7.0.0-22-generic WITH_STORAGE=0 DISABLE_WERROR=1 subsystem
```

在 Hyper-V + VF 环境中，Ubuntu inbox `qede` 驱动被观察到显示为“已降级
(SR-IOV 未运行)”。本维护驱动被观察到显示为“确定 (SR-IOV 活动)”。

## 文档

- `README.md`：英文 README
- `README.zh-CN.md`：中文 README
- `INSTALL.md`：安装、DKMS 和卸载指南
- `DKMS.md`：DKMS 使用说明
- `PACKAGING.md`：deb 构建和发布流程
- `CHANGELOG.md`：英文维护 changelog
- `CHANGELOG.zh-CN.md`：中文维护 changelog
- `NOTICE.md`：版权、许可证和维护声明

## 许可证和声明

原始驱动源码保留 QLogic/Cavium 的版权和许可证声明。GPLv2 许可证文本位于
`COPYING`，应保持原样。

本仓库 2026 年维护改动按驱动树相同的 GPLv2 条款分发。发布包或再分发修改后
的源码前，请阅读 `NOTICE.md`。

QLogic、Cavium、Marvell 和 FastLinQ 名称仅用于识别硬件系列和上游驱动谱系。
本项目不是 QLogic、Cavium 或 Marvell 的官方发布。
