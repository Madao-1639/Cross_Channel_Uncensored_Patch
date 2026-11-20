# 槽位契约

本补丁依赖引擎的「归档名由 Lua 决定」这一事实。本文记录槽位机制的引擎判据与实现约束，供维护与扩展使用。更完整的引擎分析见 [GalRev 的 AdvHD 卷](../../../GalRevserse/GalRev/docs/engines/advhd/engine-mechanics.md)「归档解析：四级链与可扩展槽位」。

## 引擎侧事实

- 每次「按资源名取归档」都调用 `Script.arc` 的 `ArcFileName.lua`，返回值即归档名，随后进入四级链解析。返回值**不受白名单约束**，任意归档名都会被接受。
- 映射表四个函数按资源名前缀分派：`getRioArcFileName`（主剧本）、`getGraphicsArcFileName`（`sys_`/`efmsk`/`bgcc`/`evcc`）、`getModelArcFileName`（模型）、`getSoundArcFileName`（`SysVoice`/`char`/`bgv`/`bgm`）。
- **两个函数看的是不同参数，这是最容易写错的一处**：

  | 函数 | 形参 | 分派依据 |
  |---|---|---|
  | `getGraphicsArcFileName(a, name)` | 2 个 | **`name`**（文件名，如 `EVCC0007.PNG`） |
  | `getSoundArcFileName(a, name)` | 2 个 | **`a`**（槽名，如 `charMIK` / `se01` / `bgm01`） |

  `getSoundArcFileName` 的 `a` 是脚本里的**槽名**、`name` 只是文件名（`Voice.arc` 的成员名能出现在任意角色的槽里，所以按文件名分派必然把整条音轨归错）。它的兜底是 **`Se.arc`**，不是 `SysVoice.arc`——`SysVoice.arc` 只装 12 条 `*_SAMPLE.ogg` 菜单试听音。

  > 写错的后果**不报错、不崩、不卡死，而是游戏静音**：所有音效与语音都被送进一个装不下它们的归档，只有 BGM 因 `bgm` 前缀独立分支仍然正常。这就是「打过补丁后只剩 BGM」的真实成因。`build_patch.py --check` 现在会实际执行映射表跑回归用例拦截这一类错。
- **字体不走这张表**：字体归档名是 `LegacyGame.lua` 里 `CLegacyFontInfo:extention('Fonts.arc', 成员, 族名, charset)` 的**调用点常量**，不经过 `ArcFileName.lua` 分派，所以槽位机制覆盖不到它（要重定向就得重写那块 147 KB 字节码的常量）。
- 四级链：裸文件目录 → 用户数据根（`%APPDATA%\<厂商>\<英文标题>\`）→ 语言包目录 → 游戏根目录。其中：
  - 裸文件目录层由调用点编译期常量控制，CG 恒关；
  - 用户数据根层**整包独占且成员缺失不回落**，任何方案都必须视为禁用；
  - 语言包层与游戏根目录层按成员回落。

## 槽位实现

`resource/slots/ArcFileName.lua`：

1. 启动时对 `patch.arc` / `patch2.arc` / `patch3.arc` 各读一次 TOC 并缓存（文件不在就记为不可用）；
2. 取资源时按 `patch3` → `patch2` → `patch` 顺序探测成员是否存在，命中即返回该槽位名；
3. 全不命中则返回原生归档名，交由引擎四层链解析。

## 缺失即卡死（最关键的约束）

引擎在**同一个请求名**上依次试各层，**不会**把槽位名还原成原名重试。若对槽位里不存在的成员返回了槽位名，最终在游戏根目录的同名归档里也查不到 → 返回空流 → `0x33`（CG 硬载入）**卡死无响应**。

⇒ **必须做成员级探测，不能无条件返回槽位名。**

## TOC 探测口径

Arc 格式：`[u32 成员数][u32 表大小]` 后接成员表，每项 `[u32 大小][u32 相对偏移]` + UTF-16LE 名 + `0x0000`；成员表之后是数据区。

- **只搜索 TOC 区**（`1 .. 8 + 表大小`）。成员表之后是成员数据，整文件子串搜索会被图片数据里的字节序列假命中。
- 成员名是 UTF-16LE，探测前先把请求名转小写，并用 ASCII 字符插入 `0x00` 构造同样的字节模式。
- 因此 `patch.arc` 的成员名必须小写（见 [architecture.md](architecture.md)「成员命名」）。

## 语言与可用性

引擎在 `WinMain` 里 `luaL_newstate` + `luaL_openlibs`，所以 `io` / `string`（含 `string.unpack`）可用。脚本经 `luaL_loadbufferx` 加载，**明文 Lua 可以直接放进归档**，无需字节码编译器。

槽位归档名与语言包无关，因此槽位对所有语言模式生效。

## 验收

`script/build_patch.py --check` 回读校验两个产物的成员数与偏移自洽、`patch.arc` 成员名全小写，并**实际执行 `ArcFileName.lua`** 跑 14 条分派回归用例（声音按槽名、图形按文件名、音频兜底 `Se.arc`）；`script/extract_cg.py --check` 校验素材均为 PNG 1280×960。实机验证口径：

- `EVCC0007` 显示替换图 ⇒ 槽位命中；
- 其他 CG 正常显示 ⇒ 成员级回落成立；
- 主菜单 / 剧情 / BGM 正常 ⇒ 四个映射函数未被破坏；
- **音效与语音有声** ⇒ `getSoundArcFileName` 的槽名分派未被破坏（只有 BGM 有声等于这条挂了）。
