# 步兵补丁（CROSS†CHANNEL Steam Edition）项目约定

## 项目定位

为 [内容还原补丁](../Cross_Channel_Content_Restoration_Patch/) 提供**可选、独立发布**的 CG 替换增量包。两者解耦：还原补丁负责忠实还原官方内容与汉化；本补丁只提供官方之外的替换素材。

**不修改游戏可执行文件、不做 DLL 注入。** 一切通过归档与 `Script.arc` 里的 Lua 完成。

## 与还原补丁的边界

| 归属 | 内容 |
|---|---|
| 还原补丁 | `asset/*.arc`（根目录层）、`asset/zh-CN/*.arc`、`zh-CN/AdvHDLang.dll` |
| 本补丁 | `<游戏根>\Script.arc`（槽位版）、`<游戏根>\patch.arc` |

- `Script.arc` 是本补丁**拥有**的文件，也是与还原补丁唯一的耦合点：双方共同维护其中的 `ArcFileName.lua`。改动它必须与还原补丁对齐。
- 明确边界后，还原补丁的仓库**不再因本补丁而改动**。

## 关键约束

### 槽位只接收与脚本无关的资源

`ws2` 与其 `lng` 译文是同一逻辑单元（`lng` 按脚本槽位/消息下标替换文本），脚本一变译文必然错配。

- ✅ 可以：CG、语音、BGM、音效、UI 图。
- ❌ 不可以：中文译文（`lng`）；修改 `ws2`（必须自带对应 `lng`，且属于另一类补丁）。
- ❌ 不可以：字体（引擎用固定名字加载，不在 `ArcFileName.lua` 分派表里）。

### 成员名一律小写

槽位探测是**字节比较**（先把请求名转小写，再在归档成员表里找同样的 UTF-16LE 字节）。归档里写大写会导致探测漏判、成员回落原生归档。构建脚本统一小写。

### 必须做成员级探测

引擎在**同一个请求名**上依次试四级链，不会把槽位名还原成原名重试。对槽位里不存在的成员返回槽位名 → 空流 → `0x33` 卡死。详见 [doc/slot-contract.md](doc/slot-contract.md)。

## 产物与基准

- `resource/Script.steam.arc`：**Steam 原版** `Script.arc`，基准存档。不依赖游戏目录当前状态、不依赖还原补丁产物。
- `resource/slots/ArcFileName.lua`：槽位版映射表，唯一被改动的成员。
- `resource/cg/*.png`：替换素材，文件名即归档成员名。
- `out/`：构建产物（不入库）。

## 脚本

```bash
python script/build_patch.py          # 构建 out/patch.arc + out/Script.arc
python script/build_patch.py --check  # 只回读校验
python script/make_test_package.py    # 最小验证包（out/test/，单成员 + 标记图）
```

所有脚本必须**幂等**、**带回读校验**，从项目根执行。

## 命名与文件

- 归档成员名小写；素材文件名不限大小写。
- 临时文件放 `tmp/`，任务结束后清理；长期产物放 `out/`，不入库。

## 文档

| 文档 | 内容 |
|---|---|
| [doc/architecture.md](doc/architecture.md) | 产物形态、与还原补丁的边界、为什么用槽位、成员命名 |
| [doc/slot-contract.md](doc/slot-contract.md) | 槽位机制的引擎判据与实现约束、TOC 探测口径、验收口径 |

改动机制相关的代码前先读 `doc/slot-contract.md`；改动边界或产物形态时同步更新 `doc/architecture.md`。
