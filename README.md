# 步兵补丁（CROSS†CHANNEL Steam Edition）

为 [CROSS†CHANNEL Steam Edition 内容还原补丁](../../Cross_Channel_Content_Restoration_Patch/) 提供**可选叠加**的 CG 替换能力：把官方之外的替换素材（民间版本）作为独立增量包装上，不改动还原补丁的任何产物，也不修改游戏可执行文件。

## 它做什么

- 通过 **槽位归档** `patch.arc`（优先级最低的槽位）提供被替换的 CG 成员；
- 通过**槽位版 `Script.arc`** 让引擎在取资源时优先查槽位归档、未命中回落原生归档；
- 与语言包共存：槽位对中/英文模式一视同仁，语言包继续只负责字体、UI、DLL。

## 安装

1. 备份游戏根目录的 `Script.arc` 与 `patch.arc`（若有）；
2. 把 `out/patch.arc` 与 `out/Script.arc` 复制到游戏根目录；
3. 启动游戏。

卸载：删除 `patch.arc`，把备份的 `Script.arc` 还原（或用 Steam 校验还原该文件）。

## 从源码构建

```bash
python script/build_patch.py          # resource/cg/*.png -> out/patch.arc + out/Script.arc
python script/make_test_package.py    # 最小验证包（out/test/，单成员 + 标记图）
```

## 目录

```
resource/
├── Script.steam.arc      Steam 原版 Script.arc（基准，只读）
├── slots/ArcFileName.lua 槽位版映射表（唯一被改动的成员）
└── cg/*.png              替换素材，文件名即归档成员名（小写）
tool/arc.py               AdvHD Arc 最小读写
script/                   构建与验证
doc/                      架构与约定
```

## 当前状态

机制已在实机验证通过（槽位命中 + 成员级回落）。素材尚未接入，`resource/cg/` 为空。

- 架构与约定：[doc/architecture.md](doc/architecture.md)
- 槽位契约（含引擎判据）：[doc/slot-contract.md](doc/slot-contract.md)
