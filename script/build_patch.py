"""构建步兵补丁产物（`patch.arc` 与槽位版 `Script.arc`），输出到 `release/`。

用法：
    python script/build_patch.py                 # 产出 release/patch.arc + release/Script.arc
    python script/build_patch.py --check         # 只回读校验已有产物

约定：
- `resource/Script.steam.arc` = Steam 原版 `Script.arc`（基准，只读）。
- `resource/slots/ArcFileName.lua` = 槽位版映射表（唯一改动成员）。
- `resource/cg/*.png` = 替换素材，**文件名即归档成员名**，一律小写；由
  `script/extract_cg.py` 从 AI 素材包生成（提取 + 放大 + 改名）。
- `patch.arc` 只放被替换的成员，未命中由引擎回落原生归档。

`patch.arc` 是**新增文件**；`Script.arc` 会覆盖 Steam 同名文件，安装前须备份。
"""
import io
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image                                          # noqa: E402
from tool import arc                                           # noqa: E402

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_SCRIPT = ROOT / 'resource' / 'Script.steam.arc'
SLOT_LUA = ROOT / 'resource' / 'slots' / 'ArcFileName.lua'
CG_MAP = ROOT / 'resource' / 'cg_map.json'
CG_DIR = ROOT / 'resource' / 'cg'
RELEASE = ROOT / 'release'

SLOT_MEMBER = 'ArcFileName.lua'


def load_map():
    doc = json.loads(CG_MAP.read_text(encoding='utf-8'))
    return {k.upper(): v.lower() for k, v in doc['map'].items()}, tuple(doc.get('_目标尺寸', (1280, 960)))


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
    target = RELEASE / 'Script.arc'
    size, _ = arc.write(out, target)
    print('[Script.arc] %d 成员；%s %d 字节 -> 归档 %d 字节'
          % (len(out), SLOT_MEMBER, len(lua), size))
    return target


def build_patch_arc():
    """一个素材文件 = 一个成员；名字取文件名（小写），并校验素材口径。"""
    want, target_dims = load_map()
    files = sorted(CG_DIR.glob('*.png'))
    if not files:
        raise SystemExit('resource/cg/ 下没有素材：先跑 python script/extract_cg.py')
    members = []
    seen = set()
    for f in files:
        name = f.name.lower()
        if name in seen:
            raise SystemExit('成员名重复（大小写不敏感）：%s' % name)
        seen.add(name)
        with Image.open(f) as im:
            if im.format != 'PNG' or im.size != target_dims:
                raise SystemExit('%s 是 %s %s，应为 PNG %dx%d'
                                 % (f.name, im.format, im.size, target_dims[0], target_dims[1]))
        members.append((name.encode('utf-16le'), f.read_bytes()))
    allowed = set(want.values())
    stray = sorted(seen - allowed)
    if stray:
        raise SystemExit('resource/cg/ 里有映射表之外的成员：%s' % ', '.join(stray))
    lack = sorted(allowed - seen)
    if lack:
        print('[警告] 映射表里有 %d 个成员没进包：%s' % (len(lack), ', '.join(lack)))
    path = RELEASE / 'patch.arc'
    size, _ = arc.write(members, path)
    print('[patch.arc] %d 成员，%d 字节' % (len(members), size))
    return path


def check():
    ok = True
    for name in ('Script.arc', 'patch.arc'):
        p = RELEASE / name
        if not p.exists():
            print('[缺失] %s' % p)
            ok = False
            continue
        try:
            n, size = arc.verify(p)
            print('[OK] %-12s %d 成员 %d 字节' % (name, n, size))
        except Exception as e:                                  # noqa: BLE001
            print('[FAIL] %s: %s' % (name, e))
            ok = False
    # 槽位探测口径：成员名必须全是小写 ASCII，否则字节比较会漏判
    p = RELEASE / 'patch.arc'
    if p.exists():
        bad = [n.decode('utf-16le') for n, _ in arc.read(p)
               if n.decode('utf-16le') != n.decode('utf-16le').lower()]
        if bad:
            print('[FAIL] patch.arc 有非小写成员名：%s' % ', '.join(bad))
            ok = False
    return ok


def main(argv):
    if '--check' in argv:
        return 0 if check() else 1
    RELEASE.mkdir(parents=True, exist_ok=True)
    build_script_arc()
    build_patch_arc()
    return 0 if check() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
