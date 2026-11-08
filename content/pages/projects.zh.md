---
title: "项目"
description: "两个给药物化学用的桌面软件、你正在读的这个博客，以及一份诚实的「还没做」清单。"
---

这里的东西都是一个人做的，跑在 Windows 和 Linux 上，离线运行。

## MolStudio

分子建模与对接工作站。

- 3D 构建、受体准备、AutoDock Vina 对接
- 2D 相互作用图，标注距离、π–π 堆积与盐桥
- 绘图、可重新打开的会话，SDF / CSV / PNG / SVG 导出
- Windows 与 Linux，原生安装包

**状态：** v1.0 已发布。免费版没有期限；一次性授权解锁完整流程。

[产品页](https://www.aiddhub.com/molstudio) · [下载](https://www.aiddhub.com/molstudio#download)

## MolInsight

构效分析工作台，用来回答「为什么这个取代基更好」。

- 47 种图表，含小倍数、分面与 3D
- MMP，带对数、离散度与显著性
- R 基团矩阵、骨架与侧链分析
- 聚类、相似性网络与自组织映射
- QSAR：ridge / PLS / 核岭回归 / KNN / GBM，带适用域

**状态：** v1.0 已发布。免费版每次会话 100 个化合物；一次性授权取消限制。

[产品页](https://www.aiddhub.com/molinsight) · [下载](https://www.aiddhub.com/molinsight#download)

## 这个站

Markdown 经一个小 Python 脚本生成静态 HTML。没有框架、没有数据库、没有统计脚本。
构建在 CI 里检查，发布出来的页面不会和源码对不上。

源码公开：[github.com/AIDDHub/AIDDHub.github.io](https://github.com/AIDDHub/AIDDHub.github.io)。

## 还没做的

把话说在前面，比暗示有要便宜得多。

- **macOS。** 近期不做。它不是重新编译一次，而是第二个要维护的平台。
- **团队版。** 没有管理后台、没有 SSO、没有浮动授权。
- **云同步。** 故意不做。文件在磁盘上，备份策略由你决定。
- **插件 API。** 想要，但它会把我还想改的接口提前冻住。

如果上面某一条对你是硬性要求，诚实的回答是：现在还不适合你。这话现在说，比在你付完钱之后说好。
