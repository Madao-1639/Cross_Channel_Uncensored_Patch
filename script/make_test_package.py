"""生成最小验证包：只含 1 个 CG 成员 + 槽位版 Script.arc。

用途：实机确认「槽位归档被接管」与「未命中成员回落原生归档」两件事同时成立。

产物（out/test/）：
    patch.arc     1 个成员 evcc0007.png（标记图，品红底 + 中央白横带 + 上下黑边）
    Script.arc    槽位版（Steam 原版内联 + 槽位映射表）

用法：python script/make_test_package.py [成员名] [宽] [高]
"""
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tool import arc

BASE_SCRIPT = ROOT / 'resource' / 'Script.steam.arc'
SLOT_LUA = ROOT / 'resource' / 'slots' / 'ArcFileName.lua'
OUT = ROOT / 'out' / 'test'

DEFAULT_MEMBER = 'evcc0007.png'
DEFAULT_W, DEFAULT_H = 1280, 960


def marker_png(w, h):
    """纯品红底 + 中央白横带 + 上下黑边；任何缩放下都可辨认。"""
    def chunk(tag, payload):
        body = tag + payload
        return struct.pack('>I', len(payload)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

    rows = []
    for y in range(h):
        if y < 8 or y >= h - 8:
            row = b'\x00\x00\x00' * w
        elif h // 2 - 60 <= y < h // 2 + 60:
            row = b'\xff\xff\xff' * w
        else:
            row = b'\xff\x00\xff' * w
        rows.append(b'\x00' + row)

    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b''.join(rows), 6))
            + chunk(b'IEND', b''))


def main(argv):
    member = (argv[0] if argv else DEFAULT_MEMBER).lower()
    w = int(argv[1]) if len(argv) > 1 else DEFAULT_W
    h = int(argv[2]) if len(argv) > 2 else DEFAULT_H

    OUT.mkdir(parents=True, exist_ok=True)

    # patch.arc：单成员
    png = marker_png(w, h)
    patch = OUT / 'patch.arc'
    size, _ = arc.write([(member.encode('utf-16le'), png)], patch)
    print('[patch.arc] 1 成员 %s（%dx%d，%d 字节）-> 归档 %d 字节' % (member, w, h, len(png), size))

    # Script.arc：Steam 原版内联 + 槽位映射表
    lua = SLOT_LUA.read_bytes()
    members = []
    hit = 0
    for name, data in arc.read(BASE_SCRIPT):
        if name.decode('utf-16le') == 'ArcFileName.lua':
            members.append((name, lua))
            hit += 1
        else:
            members.append((name, data))
    if hit != 1:
        raise SystemExit('基准 Script.arc 里 ArcFileName.lua 出现 %d 次（应为 1）' % hit)
    script = OUT / 'Script.arc'
    size, _ = arc.write(members, script)
    print('[Script.arc] %d 成员；ArcFileName.lua %d 字节 -> 归档 %d 字节' % (len(members), len(lua), size))

    arc.verify(patch, 1)
    arc.verify(script, len(members))
    print('回读校验通过；产物目录：%s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
