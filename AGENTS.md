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
- ❌ 不可以：字体 —— 它的归档名是 `LegacyGame.lua` 里 `CLegacyFontInfo:extention('Fonts.arc', ...)` 的**调用点常量**，不经过 `ArcFileName.lua` 分派表，所以槽位机制覆盖不到它（改常量则要重写整块 147 KB 字节码）。

### 成员名一律小写

槽位探测是**字节比较**（先把请求名转小写，再在归档成员表里找同样的 UTF-16LE 字节）。归档里写大写会导致探测漏判、成员回落原生归档。构建脚本统一小写。

### 必须做成员级探测

引擎在**同一个请求名**上依次试四级链，不会把槽位名还原成原名重试。对槽位里不存在的成员返回槽位名 → 空流 → `0x33` 卡死。详见 [doc/slot-contract.md](doc/slot-contract.md)。

## 素材来源与处理

素材 = AI 步兵补丁（用于**原版**游戏，下载地址见 [README](../README.md) 致谢节）的 `chip.arc`，即原版 `Chip.arc` 的全量替换包。素材**不入库**（版权原因），只在本地放为 `../AI_uncensored_patch/chip.arc`。处理三步，全部由 `script/extract_cg.py` 完成：

1. **提取**：原版 `Chip.arc` 是 WillPlus 老格式（类型表 + 定长条目），用 `tool/arc.py` 的 `read_old_arc`；不能用 Steam 格式的 `read`。
2. **分辨率**：原版素材 800×600，Steam 版事件 CG 画布 1280×960 ⇒ **LANCZOS** 放大到 1280×960。方法与还原补丁 `script/build_restored_cgs.py` 一致（已证实原版图按此放大与既有还原 CG 逐像素相同）。
3. **命名映射**：还原补丁对 Steam 删掉的 H 场景 CG 做了**同名冲突隔离**（改名为 `EVCC9XXX`），所以素材不能按原版名进包。映射表 `resource/cg_map.json` 抄自还原补丁 `resource/cg_map.json` 的 `all` 表，成员名一律小写。`EVCC0023B.PNG` 在 Steam 版同名存在（只是裁切不同），保持原名。

**差异审计**：`extract_cg.py` 会拿 `../CROSS_CHANNEL_Original/Chip.arc` 对比 AI 包，AI 实际改过的成员集合必须与映射表**完全一致**；换素材包或漏改映射会当场报错。

## 产物与基准

- `resource/Script.steam.arc`：**Steam 原版** `Script.arc`，基准存档。不依赖游戏目录当前状态、不依赖还原补丁产物。
- `resource/slots/ArcFileName.lua`：槽位版映射表，唯一被改动的成员。
- `resource/cg_map.json`：原版名 → 槽位成员名，25 条。
- `resource/cg/*.png`：替换素材（由 `extract_cg.py` 生成），文件名即归档成员名。
- `release/`：构建产物（不入库）。

## 脚本

```bash
python script/extract_cg.py           # AI chip.arc -> resource/cg/*.png（含差异审计）
python script/extract_cg.py --check   # 只核对已有素材的格式与尺寸
python script/build_patch.py          # 构建 release/patch.arc + release/Script.arc
python script/build_patch.py --check  # 只回读校验
```

所有脚本必须**幂等**、**带回读校验**，从项目根执行。

## 命名与文件

- 归档成员名小写；素材文件名即成员名。
- 临时文件放 `tmp/`，任务结束后清理；长期产物放 `release/`，不入库。

## 文档

| 文档 | 内容 |
|---|---|
| [doc/architecture.md](doc/architecture.md) | 产物形态、与还原补丁的边界、为什么用槽位、素材处理与成员命名 |
| [doc/slot-contract.md](doc/slot-contract.md) | 槽位机制的引擎判据与实现约束、TOC 探测口径、验收口径 |

改动机制相关的代码前先读 `doc/slot-contract.md`；改动边界或产物形态时同步更新 `doc/architecture.md`。
