"""Đối chiếu bảng gộp với file mẫu ở phần năm trùng nhau (2016-2024)."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
import build_dataset as b, openpyxl

out = b.load()
tw = openpyxl.load_workbook(b.TEMPLATE, read_only=True)
rows = list(tw['DỮ LIỆU TỪ 2013 kltn'].iter_rows(values_only=True))
hdr = rows[0]
mism, tot, ex = collections.Counter(), collections.Counter(), {}
for r in rows[1:]:
    k = (r[0], r[1])
    if k not in out:
        continue
    for c in range(2, 97):
        t, o = r[c], out[k][c]
        if isinstance(t, str) or (t is None and o is None):
            continue
        tot[c] += 1
        t, o = t or 0, o or 0
        if abs(t - o) > max(2000, abs(t) * 0.001):
            mism[c] += 1
            ex.setdefault(c, (k, t, o))
print('overlap rows', sum(1 for r in rows[1:] if (r[0], r[1]) in out))
for c in sorted(mism):
    print(c, str(hdr[c])[:40].replace('\n', ' '), mism[c], '/', tot[c], ex[c])
print('banks in output not in template:', sorted({k[0] for k in out} - {r[0] for r in rows[1:]}))
print('banks in template not in output:', sorted({r[0] for r in rows[1:] if r[0]} - {k[0] for k in out}))
