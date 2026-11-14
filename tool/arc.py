"""AdvHD Arc 归档的最小读写实现（纯标准库）。

格式：`[u32 成员数][u32 表大小]` 后接成员表，每项 `[u32 大小][u32 相对偏移]` + UTF-16LE 名 + `0x0000`；
成员表之后是数据区，偏移量相对数据区起点（`8 + 表大小`）。

只做本补丁需要的事：读（校验用）与写（产出 patch.arc）。成员名按原始字节携带，不经过文件系统。
"""
import struct
from pathlib import Path

HEADER = struct.Struct('<II')
ENTRY = struct.Struct('<II')
SEP = b'\x00\x00'


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
