"""构建步兵补丁产物（`patch.arc` 与槽位版 `Script.arc`）。

用法：
    python script/build_patch.py                 # 产出 out/patch.arc + out/Script.arc
    python script/build_patch.py --check         # 只回读校验已有产物

约定：
- `resource/Script.steam.arc` = Steam 原版 `Script.arc`（基准，只读）。
- `resource/slots/ArcFileName.lua` = 槽位版映射表（唯一改动成员）。
- `resource/cg/*.png` = 替换素材，**文件名即归档成员名**，一律小写。
- `patch.arc` 只放被替换的成员，未命中由引擎回落原生归档。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tool import arc

BASE_SCRIPT = ROOT / 'resource' / 'Script.steam.arc'
SLOT_LUA = ROOT / 'resource' / 'slots' / 'ArcFileName.lua'
CG_DIR = ROOT / 'resource' / 'cg'
OUT = ROOT / 'out'

SLOT_MEMBER = 'ArcFileName.lua'


def build_script_arc():
    """Steam 原版 Script.arc 内联，只把 ArcFileName.lua 换成槽位版。"""
    members = arc.read(BASE_SCRIPT)
    lua = SLOT_LUA.read_bytes()
    out = []
    hit = 0
    for name, data in members:
        if name.decode('utf-16le') == SLOT_MEMBER:
            out.append((name, lua))
            hit += 1
        else:
            out.append((name, data))
    if hit != 1:
        raise SystemExit('基准 Script.arc 里 %s 出现 %d 次（应为 1）' % (SLOT_MEMBER, hit))
    target = OUT / 'Script.arc'
    size, _ = arc.write(out, target)
    print('[Script.arc] %d 成员；%s %d 字节 -> 归档 %d 字节'
          % (len(out), SLOT_MEMBER, len(lua), size))
    return target


def build_patch_arc():
    """一个素材文件 = 一个成员；名字取文件名（小写）。"""
    files = sorted(CG_DIR.glob('*.png'))
    if not files:
        raise SystemExit('resource/cg/ 下没有素材，无法构建 patch.arc')
    members = []
    seen = set()
    for f in files:
        name = f.stem.lower()
        if name in seen:
            raise SystemExit('成员名重复（大小写不敏感）：%s' % name)
        seen.add(name)
        members.append((name.encode('utf-16le'), f.read_bytes()))
    target = OUT / 'patch.arc'
    size, _ = arc.write(members, target)
    print('[patch.arc] %d 成员，%d 字节' % (len(members), size))
    return target


def check():
    ok = True
    for name, expect in (('Script.arc', None), ('patch.arc', None)):
        p = OUT / name
        if not p.exists():
            print('[缺失] %s' % p)
            ok = False
            continue
        try:
            n, size = arc.verify(p, expect)
            print('[OK] %-12s %d 成员 %d 字节' % (name, n, size))
        except Exception as e:
            print('[FAIL] %s: %s' % (name, e))
            ok = False
    return ok


def main(argv):
    if '--check' in argv:
        return 0 if check() else 1
    OUT.mkdir(parents=True, exist_ok=True)
    build_script_arc()
    build_patch_arc()
    return 0 if check() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
