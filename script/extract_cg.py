"""从 AI 步兵补丁（下载地址见 README 致谢节）的 `chip.arc` 提取 CG，放大到 Steam 画布并改成槽位成员名。

三步：

1. 读 `chip.arc`（**原版 WillPlus 格式**，见 `tool/arc.py` 的 `read_old_arc`）；
2. 按 `resource/cg_map.json` 把「原版名 → 槽位成员名」落到文件上；
3. **分辨率**：原版素材 800×600，Steam 版事件 CG 画布 1280×960。按 **LANCZOS** 放大
   （与还原补丁 `script/build_restored_cgs.py` 的放大方法一致 —— 该方法已被证实
   可让原版图与既有还原 CG 逐像素相同）。

若给了 `--orig-arc`（默认 `../CROSS_CHANNEL_Original/Chip.arc`，存在则自动启用），
还会做一次**差异审计**：AI 包相对原版真正改过的成员，必须与映射表的键集合完全一致。
这样素材包换版本、或映射表漏项，都会当场报错，而不是静默少发一张图。

产物：`resource/cg/<成员名>.png`（小写，文件名即 `patch.arc` 成员名，不入库）。

用法（项目根目录）：
    python script/extract_cg.py                     # 提取（默认读同级 AI_uncensored_patch/chip.arc）
    python script/extract_cg.py --check             # 只核对已有产物
    python script/extract_cg.py --ai-arc <path>     # 指定 AI 包
"""
import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image                                          # noqa: E402
from tool import arc                                           # noqa: E402

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CG_MAP = ROOT / 'resource' / 'cg_map.json'
CG_DIR = ROOT / 'resource' / 'cg'
AI_ARC = ROOT.parent / 'AI_uncensored_patch' / 'chip.arc'
ORIG_ARC = ROOT.parent / 'CROSS_CHANNEL_Original' / 'Chip.arc'
TARGET = (1280, 960)


def load_map():
    doc = json.loads(CG_MAP.read_text(encoding='utf-8'))
    target = tuple(doc.get('_目标尺寸', TARGET))
    return {k.upper(): v.lower() for k, v in doc['map'].items()}, target


def read_members(path):
    """原版归档 -> {大写名: data}。名字是窄字节，ASCII 安全。"""
    return {n.decode('ascii').upper(): d for n, d in arc.read_old_arc(path)}


def upscale(data, target):
    """RGB + LANCZOS 放大；返回 PNG 字节。尺寸已等于目标时仍重编码，保证输出口径单一。"""
    im = Image.open(io.BytesIO(data)).convert('RGB')
    if im.size != target:
        im = im.resize(target, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    return buf.getvalue()


def audit(orig, ai, want):
    """AI 包相对原版改过的成员集合，必须等于映射表的键集合。"""
    changed = {k for k in ai if orig.get(k) != ai[k]}
    missing = sorted(changed - set(want))
    extra = sorted(set(want) - changed)
    if missing:
        print('[审计] AI 改过但映射表未收录：%s' % ', '.join(missing))
    if extra:
        print('[审计] 映射表收录但 AI 未改动：%s' % ', '.join(extra))
    if missing or extra:
        raise SystemExit('映射表与 AI 包不一致：先更新 resource/cg_map.json')
    print('[审计] AI 改动的 %d 个成员与映射表一致' % len(changed))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--ai-arc', type=Path, default=AI_ARC)
    ap.add_argument('--orig-arc', type=Path, default=ORIG_ARC)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)

    want, target = load_map()
    print('映射表：%d 条，目标尺寸 %dx%d' % (len(want), target[0], target[1]))
    if not args.ai_arc.exists():
        raise SystemExit('缺少 AI 包：%s' % args.ai_arc)

    ai = read_members(args.ai_arc)
    print('AI 包：%d 个成员（%s）' % (len(ai), args.ai_arc.name))
    if args.orig_arc.exists():
        audit(read_members(args.orig_arc), ai, want)
    else:
        print('[审计] 跳过：找不到原版归档 %s' % args.orig_arc)

    lack = sorted(set(want) - set(ai))
    if lack:
        raise SystemExit('AI 包里缺少映射表要的成员：%s' % ', '.join(lack))

    if args.check:
        bad = 0
        for oname in sorted(want):
            p = CG_DIR / want[oname]
            if not p.exists():
                print('[缺失] %s <- %s' % (p.name, oname))
                bad += 1
                continue
            im = Image.open(p)
            if im.size != target or im.format != 'PNG':
                print('[失配] %s %s %s' % (p.name, im.format, im.size))
                bad += 1
        print('[check] %s' % ('通过' if not bad else '%d 处问题' % bad))
        return 0 if not bad else 1

    CG_DIR.mkdir(parents=True, exist_ok=True)
    done = same = 0
    total = 0
    for oname in sorted(want):
        member = want[oname]
        png = upscale(ai[oname], target)
        total += len(png)
        p = CG_DIR / member
        if p.exists() and hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256(png).digest():
            same += 1
            continue
        p.write_bytes(png)
        done += 1
    print('[素材] 写入 %d，未变 %d，合计 %d 字节；输出 %d 个成员'
          % (done, same, total, len(want)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
