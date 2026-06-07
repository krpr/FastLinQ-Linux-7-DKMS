# 中文变更日志

本文件只记录 `FastLinQ Linux 7 DKMS` 维护分支的变更，不翻译原 QLogic/Cavium
驱动包自带的历史 changelog 或 release notes。

本维护分支基于原 QLogic/Cavium FastLinQ Linux 驱动包 `8.70.12.0`。

## 8.70.12.0-linux7-maint.1 - 2026-06-08

Linux 7.0 / Debian/Ubuntu 初始维护基线。

### 新增

- 增加 `dkms.conf`，支持 `qed`、`qede`、`qedr` 在内核更新后自动重建。
- 增加 `DKMS.md` 和 `INSTALL.md`，记录 Debian/Ubuntu 安装、staged install
  和内核更新流程。
- 增加 `scripts/build-dkms-deb.sh`，用于构建本地 Debian/Ubuntu DKMS 源码包。
- 增加固定打包入口：`make deb`、`make package`、`make deb-info` 和
  `PACKAGING.md`。
- 增加 `NOTICE.md`，保留原始 QLogic/Cavium 声明并记录 2026 维护归属。
- 增加 GitHub 首页文档 `README.md` 和中文文档 `README.zh-CN.md`。
- 增加 `WITH_STORAGE` 顶层开关。默认维护模块为 `qed`、`qede`、`qedr`；
  存储卸载模块仅在显式指定 `WITH_STORAGE=1` 时尝试构建。
- 增加顶层包名和版本变量，便于维护打包。

### 调整

- 重做模块 Makefile，让模块构建直接使用内核 Kbuild 规则，不再覆盖 Kbuild 模块
  目标。
- 通过 `ccflags-y` 传递 `EXTRA_CFLAGS`，确保兼容性探测参数进入所有对象文件。
- 顶层默认 `DISABLE_WERROR=1`。Linux 7.0 头文件和现代 GCC 会对旧驱动树产生
  一些兼容性 warning，默认不再让 warning 阻断安装。
- 调整 staged install 行为，使 `PREFIX=/path` 安装到该根目录，并跳过在线
  initramfs 更新。
- 调整 udev 安装流程，改为通过 `bash` 执行并支持 `DESTDIR`。

### 修复

- 修复 `qed`、`qede`、`qedr` 在 Linux 7.0 上的构建失败。
- 增加已删除或已变化内核 API 的兼容处理，包括 `strlcpy`、PCIe AER helpers、
  `local_clock`、sysfs binary attributes、`netif_napi_add_weight`、PTP
  `adjfine`、非 const `cyclecounter.read`、新的 `ethtool_rxfh_param`、
  `kernel_ethtool_ts_info` 和 `ethtool_keee`。
- 在 Linux 7.0 上禁用旧的 `qed`/`qede` devlink 集成，因为旧实现不再匹配当前
  上游 devlink API。
- 修复 `qedr` 对较新 RDMA core `create_cq` 和 `reg_user_mr` 签名的兼容。
- 修复 `qedr` 对已移除 `in_irq()` 和变化后的 `ip_route_output()` 签名的兼容。
- 修复 `qedr` 默认 `QED_DIR` 解析，使独立构建和顶层构建都能找到正确的
  `Module.symvers`。

### 验证

在 Linux `7.0.0-22-generic` 上验证：

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

当前测试环境没有安装 `dkms` 命令，因此 `dkms add/build/install` 已记录流程，
但未在该环境中实际执行。

### 已知限制

- `qedf` 和 `qedi` 不属于该基线的维护范围。Linux 7.0 SCSI/FCoE/iSCSI API
  变化需要更大的存储驱动移植工作，完成移植和测试前不应启用。
- Secure Boot 模块签名依赖现场策略，本源码树不自动处理签名。
- 后续 Linux 内核可能继续需要兼容性维护。若内核更新导致 DKMS 构建失败，应按
  常规维护事件处理：检查 DKMS build log，增加有边界的兼容性探测，重建，并
  更新 changelog。
