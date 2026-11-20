# CROSS†CHANNEL AI 步兵 CG 替换

将 Steam 版[《CROSS†CHANNEL Steam Edition》](https://store.steampowered.com/app/812560/)的 H 场景 CG 换成 AI 步兵版，作为**可选叠加的独立增量包**。同时提供一层可拓展的槽位机制：其他补丁也能用这套注入钩子覆盖任意资源，并向第三方开放 `patch` / `patch2` / `patch3` 三个槽位（原理见[生效机制](#生效机制优先级最高的通用成员覆盖)）。

> **本补丁以[内容还原补丁](https://github.com/Madao-1639/Cross_Channel_Content_Restoration_Patch)为基础，请先安装它。**
>
> 本补丁**只为还原后的游戏准备**，不能脱离还原补丁使用：大部分 CG 在 Steam 版里被删除，其编号已被还原补丁重新分配为 `EVCC9XXX`。

> 本仓库只包含分析、映射与构建工具，不含游戏本体文件与素材原图；素材版权属原作者，补丁仅供已购买正版的用户使用。

![Banner](https://shared.steamstatic.com/store_item_assets/steam/apps/812560/library_hero.jpg?t=1573643366)


---

## 安装 / 更新 / 卸载

### 前置

先按[内容还原补丁的说明](https://github.com/Madao-1639/Cross_Channel_Content_Restoration_Patch)装好还原补丁与中文语言包，确认游戏能正常启动、剧情与中文显示无异常。**本补丁是它的叠加层**，顺序不能反。

### 安装

1. 从 [Releases](../../releases) 下载 `Cross_Channel_Uncensored_Patch_vX.X.X.zip`；
2. 打开游戏安装目录（Steam 库 → 右键游戏 →【管理】→【浏览本地文件】）；
3. 建议把官方 `Script.arc` 改名备份为 `Script.arc.orig`，补丁会替换这个文件，备份方便卸载；
4. 将压缩包里的 `patch.arc` 与 `Script.arc` 复制进游戏目录；

### 更新

下载新版 `patch.arc` 覆盖游戏目录里的旧文件即可；没有特殊说明 `Script.arc` 不用动（它只在槽位机制本身变更时才更新）。

### 卸载

删除游戏目录里的 `patch.arc`；再把之前备份的 `Script.arc.orig` 改名回 `Script.arc`，或者通过 Steam 验证游戏完整性还原该文件。若之前备份过 `patch.arc.orig`，同样改回原名即可恢复被本补丁顶替的旧槽位包。

两个文件都是单文件、无残留。还原补丁与中文语言包（`zh-CN/` 目录）**不受影响，也不需要重装**。


---

## 实现原理

### 生效机制：优先级最高的通用成员覆盖

引擎不把归档名写死 —— 每次「按资源名取归档」都要问 `Script.arc` 里的 `ArcFileName.lua`，由它按资源名前缀返回归档名。这是**整个引擎里唯一一处**归档名可控的接口。

`Script.arc` 是官方的 Lua 归档：引擎用 `luaL_loadbufferx` 加载成员，**明文 Lua 可直接使用**（不需字节码编译器）；`WinMain` 里 `luaL_openlibs` 已开齐标准库（`io` / `string` 含 `string.unpack`）。

所以所谓“注入钩子”就是：重用官方自己的扩展点，改写 `ArcFileName.lua` 一个成员，在四个映射函数前面插一段槽位探测。**不 patch 内存、不注入 DLL、不改 exe、不写 `%APPDATA%`**。它只动一个归档里的一个脚本成员，不碰任何内容产物 —— 因此这层机制与还原补丁无关，与任何内容补丁也无关。

探测的做法：取资源前先查 `patch.arc` / `patch2.arc` / `patch3.arc` 的成员表，**命中就返回槽位归档名，未命中才回落到原生归档**。

于是有两层语义：

**1. 优先级最高。** 槽位归档在四级解析链里先于 `Chip2.arc` 被查，命中的成员直接顶替原生同名资源 —— 这是**通用的成员级覆盖**，对被覆盖的成员而言等价于「官方内容被替换」，没有任何白名单或前缀限制。

**2. 但它是精确到成员的。** 槽位里没有的成员一律回落原生归档，所以一个 25 张图的包不需要附带 236 张图的完整归档，也不会影响任何未被列出的资源。这条是硬约束：引擎在**同一个请求名**上依次试四级链，不会把槽位名还原成原名重试，所以若对槽位里不存在的成员返回了槽位名，就会得到空流、`0x33` 硬载入卡死 —— 探测必须逐成员进行。

### 全局生效，对英文版无影响

`Script.arc` 是**根目录层**的文件，不随语言包切换；`ArcFileName.lua` 的四个函数对中英文模式一视同仁。所以：

- **英文模式**（未安装中文语言包，或注册表语言值为空）：补丁照样生效，CG 照样被替换；
- **中文模式**：同样生效。

就**内容**而言，本补丁只替换 `.PNG` 图像资源，不碰任何与文本相关的成员（`lng`、`ws2`、`NameTable.txt`、字体、UI 图），因此**对英文版的文本、界面、字体、存档没有任何影响** —— 英文玩家看到的唯一变化就是那 25 张 CG 变成了无修正版本。

### 必须注意：中文语言包的适配边界

槽位覆盖排在四级链最前，**它会遮蔽语言包层的同名成员**。对纯图像这不成问题，但这条机制有一个必须写明的风险，供其他补丁作者参考：
> **若某个补丁通过槽位修改了 `ws2` 剧情脚本，而语言包的 `lng` 译文没有同步更新，就会出现对应语言下的文本错位或缺失。**

原因是 `ws2` 与它的 `lng` 是**同一逻辑单元**：`lng` 按脚本槽位与消息下标替换文本，下标一挪，译文就落到别的行上。被遮蔽或被改写的行会失去译文，**落回 `ws2` 内嵌的原始台词**（也就是英文/日文原文），表现为该句突然变成外语，或者整段文本前移/后移。

因此本补丁在**内容上**的自我约束是：

- **只替换与脚本无关的资源**（CG、语音、BGM、音效、UI 图）；
- **绝不**用槽位承载中文译文（`lng`），**绝不**用槽位修改 `ws2` —— 那必须连同一份同步的 `lng` 一起发，属于另一类补丁的职责。

> 机制本身不替你检查这件事：它只保证「成员能覆盖、能回落」。上述约束是使用槽位的**交通规则**，而不是机制能自动验证的性质。

### 补丁槽位（可拓展部分的核心）

槽位优先级为 `patch` < `patch2` < `patch3`（后注册优先）。**本补丁的 CG 占用最低的 `patch`**，意味着其他补丁可以用 `patch2` / `patch3` 覆盖本补丁的成员，而本补丁不会挡住它们。

`patch`、`patch2`、`patch3` **全部向第三方开放**（本仓库自己也不例外，占的是最低顺位），只需遵循以下约定（详见 [`doc/slot-contract.md`](doc/slot-contract.md) 与 [GalRev 的 AdvHD 引擎卷](https://github.com/Madao-1639/GalRev/tree/main/docs/engines/advhd)）：

1. **成员名一律小写**。引擎查成员是大小写不敏感的，但槽位探测是**字节比较**：探测时先把请求名转小写，再在归档成员表里找同样的 UTF-16LE 字节序列。归档里写大写会导致漏判、成员回落原生归档。
2. **必须做成员级探测**，不能无条件返回槽位名（否则见上文的 `0x33` 卡死）。
3. **只搜索 TOC 区**（`1 .. 8 + 表大小`）。整文件子串搜索会被图片数据里的字节序列假命中。
4. **只放与脚本无关的资源**。`ws2` 与 `lng` 必须同源同版本，不能靠优先级在两者之间仲裁。
5. **字体不能走槽位**。字体归档名是 `LegacyGame.lua` 里 `CLegacyFontInfo:extention('Fonts.arc', ...)` 的调用点常量，不经过 `ArcFileName.lua` 分派；要换字体只能由语言包放同名 `Fonts.arc`。


### 素材处理（CG 替换这一层）

原版 CG 是 800×600，Steam 版事件 CG 画布 1280×960（4:3 同比例、1.6 倍），所以素材一律 **LANCZOS 放大到 1280×960**；方法与还原补丁重建 CG 时一致。命名则沿用还原补丁做的**同名冲突隔离**：Steam 现有同名 CG 的保持原名（如 `EVCC0023B.PNG`），被删除后由还原补丁补回的走 `EVCC9XXX` 段 —— 这也是**CG 替换以还原补丁为基础**的具体原因。素材来源与下载说明见 [`resource/cg/README.md`](resource/cg/README.md)，细节见 [`doc/architecture.md`](doc/architecture.md)。

---

## 已知情况

| 项 | 内容 |
|---|---|
| 替换 CG | 25 张（事件 CG） |
| 归档成员 | 25 个（最小包，未列出的 211 张由引擎回落原生归档） |
| 分辨率 | 1280×960（原版 800×600 经 LANCZOS 放大） |
| 影响范围 | 仅图像；文本、界面、字体、存档均不变 |

---

## 目录结构

```
doc/        技术文档（架构与约定、槽位契约）
resource/   映射表与槽位 Lua（素材与 Steam 基准不入库）
script/     提取（含差异审计）与构建
tool/       AdvHD Arc 读写（Steam 格式 + 原版 WillPlus 格式）
release/    交付物
```

## 从源码构建

```bash
python script/extract_cg.py     # AI chip.arc -> resource/cg/*.png（提取 + 放大 + 改名 + 差异审计）
python script/build_patch.py    # -> release/patch.arc + release/Script.arc
python script/build_patch.py --check
```

需要把 Steam 原版 `Script.arc` 放到 `resource/Script.steam.arc`（该文件不入库），并把 AI 素材包放到同级目录的 `AI_uncensored_patch/chip.arc`。详见 [`resource/README.md`](resource/README.md)。

---

## 反馈

遇到问题请提交 [Issue](../../issues)，附上：

- 补丁版本
- 出现问题的具体场景（哪条线、哪张 CG；最好附上截图）
- 是否已安装内容还原补丁与中文语言包
- 游戏弹出的错误日志（如有）

---

## 致谢

- [AI 步兵 CG](https://fan2d.top/downloads/39301)（原版 MediaBox 版）
- 命名隔离、放大方法与槽位验证：[内容还原补丁](https://github.com/Madao-1639/Cross_Channel_Content_Restoration_Patch)
- 引擎机制分析：[GalRev](https://github.com/Madao-1639/GalRev)
