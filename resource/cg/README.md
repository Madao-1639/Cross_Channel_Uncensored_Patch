# 替换素材

本目录由 `script/extract_cg.py` 生成，**不要手工维护**。

## 素材来源

- 来源：AI 步兵补丁（下载地址见 [README](../../README.md) 致谢节）的 `chip.arc`，即原版 `Chip.arc` 的全量替换包
- 下载后放到同级目录：`../AI_uncensored_patch/chip.arc`（或用 `--ai-arc <path>` 指定）
- 版权属原作者，**不入库**；本仓库只保留映射表与构建工具

## 生成规则

- 输入是原版 WillPlus 归档格式，用 `tool/arc.py` 的 `read_old_arc` 读（不是 Steam 格式的 `read`）
- 每个文件 = `patch.arc` 的一个成员，**文件名即成员名**（小写，带 `.png`）
- 图像一律 RGB、**1280×960**（原版 800×600 经 LANCZOS 放大，与 Steam 版事件 CG 画布一致）
- 命名按 `resource/cg_map.json`：沿用还原补丁的同名冲突隔离（`EVCC9XXX`），Steam 版现有同名的保持原名
- 只放被替换的成员；未列出的成员由引擎回落原生归档

## 命令

```bash
python script/extract_cg.py           # 生成 25 个成员（含与原版归档的差异审计）
python script/extract_cg.py --check   # 只核对已有素材的格式与尺寸
```
