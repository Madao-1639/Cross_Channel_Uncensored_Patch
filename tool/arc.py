"""AdvHD Arc 归档的最小读写实现（纯标准库）。

两套格式：

* **Steam（Amaneko）格式** —— `read` / `write`：
  `[u32 成员数][u32 表大小]` 后接成员表，每项 `[u32 大小][u32 相对偏移]` + UTF-16LE 名 + `0x0000`；
  成员表之后是数据区，偏移量相对数据区起点（`8 + 表大小`）。
* **原版 WillPlus 格式** —— `read_old_arc`：
  `[u32 类型数]` 后接类型表（每项 `[4B 类型名][u32 文件数][u32 条目区偏移]`），
  条目区内每项 `[定长文件名][u32 大小][u32 绝对偏移]`（文件名 13B = V2、9B = V1）。

只做本补丁需要的事：读（取素材 / 校验）与写（产出 `patch.arc`）。成员名按原始字节携带，不经过文件系统。
"""
import struct
from pathlib import Path

HEADER = struct.Struct('<II')
ENTRY = struct.Struct('<II')
SEP = b'\x00\x00'

OLD_TYPE = struct.Struct('<4sII')


def read(path):
    """返回 [(name_bytes, data)]，名字保持归档内的原始 UTF-16LE 字节。"""
    blob = Path(path).read_bytes()
    count, table_size = HEADER.unpack_from(blob, 0)
    data_start = 8 + table_size
    out = []
    off = 8
    for _ in range(count):
        size, rel = ENTRY.unpack_from(blob, off)
        off += 8
        start = off
        while blob[off:off + 2] != SEP:
            off += 2
        name = blob[start:off]
        off += 2
        begin = data_start + rel
        data = blob[begin:begin + size]
        if len(data) != size:
            raise ValueError('成员被截断: %r' % name)
        out.append((name, data))
    return out


def write(members, path):
    """members = [(name_bytes, data)]。成员顺序即写入顺序。"""
    table_size = sum(ENTRY.size + len(n) + len(SEP) for n, _ in members)
    data_start = 8 + table_size
    table = bytearray()
    body = bytearray()
    for name, data in members:
        table += ENTRY.pack(len(data), len(body))
        table += name + SEP
        body += data
    blob = HEADER.pack(len(members), table_size) + bytes(table) + bytes(body)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(blob)
    return len(blob), data_start


def verify(path, expect_count=None):
    """回读校验：能解析、成员数符合、偏移自洽。返回 (成员数, 文件大小)。"""
    members = read(path)
    if expect_count is not None and len(members) != expect_count:
        raise ValueError('成员数 %d != 预期 %d' % (len(members), expect_count))
    return len(members), Path(path).stat().st_size


def read_old_arc(path, name_len=13):
    """读**原版 WillPlus** 归档（如 `CROSS_CHANNEL_Original/Chip.arc`）。

    结构（与 `willplus-adv-tools/will_arc.py` 一致）：
        [u32 类型数] 然后每类 `[4B 类型名][u32 文件数][u32 条目区绝对偏移]`；
        条目区每项 `[定长文件名][u32 大小][u32 绝对偏移]`，定长 = 13（V2）或 9（V1）。

    返回 `[(b'EVCC0002.PNG', data)]`：名字 = 定长字段里的名字 + `.` + 类型名。
    名字是 **ASCII/Shift-JIS 窄字节**，不是 UTF-16LE（用 utf-16-le 解会静默变成乱码）。
    """
    blob = Path(path).read_bytes()
    n_types, = struct.unpack_from('<I', blob, 0)
    off = 4
    types = []
    for _ in range(n_types):
        tname, count, start = OLD_TYPE.unpack_from(blob, off)
        types.append((tname.rstrip(b'\x00'), count, start))
        off += OLD_TYPE.size
    entry_size = name_len + 8
    out = []
    for tname, count, start in types:
        p = start
        for _ in range(count):
            name = blob[p:p + name_len].split(b'\x00')[0]
            size, data_off = struct.unpack_from('<II', blob, p + name_len)
            data = blob[data_off:data_off + size]
            if len(data) != size:
                raise ValueError('成员被截断: %r in %s' % (name, path))
            out.append((name + b'.' + tname, data))
            p += entry_size
    return out
