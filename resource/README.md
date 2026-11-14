# resource

| 路径 | 说明 | 入库 |
|---|---|---|
| `Script.steam.arc` | **Steam 原版 `Script.arc`**，构建基准 | ❌ 自行从游戏复制 |
| `slots/ArcFileName.lua` | 槽位版映射表（唯一被改动的成员） | ✅ |
| `cg/*.png` | 替换素材，文件名即归档成员名 | ❌ 容量与版权原因 |

## 准备 `Script.steam.arc`

从 Steam 版游戏根目录复制 `Script.arc` 到此处并改名：

```powershell
cp "<SteamLibrary>\steamapps\common\CROSS†CHANNEL Steam Edition\Script.arc" `
   "resource\Script.steam.arc"
```

**必须是 Steam 原档**，不能是还原补丁应用后的状态（还原补丁不提供根目录 `Script.arc`，正常安装后该文件仍是原档；若曾被旧版本补丁改动，先用 Steam 校验还原）。

判据：14 个成员，且 `LegacyGame_utf8.lua` 为 2273 字节、`ui_language.lua` 为 246 字节。
