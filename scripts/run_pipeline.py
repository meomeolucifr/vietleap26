"""Chạy toàn bộ pipeline: dữ liệu thô (Data/*.xlsx) -> số liệu dashboard -> phân tích -> kinh tế lượng.

    python scripts/run_pipeline.py          # như CI: sinh dashboard/data.js, analysis.js, econ.js
    python scripts/run_pipeline.py --xlsx   # thêm bảng panel Excel có công thức (cần file mẫu KLTN, chỉ có ở máy local)

Dừng với mã lỗi khác 0 nếu một bước lỗi hoặc kiểm tra dữ liệu không đạt, để GitHub Actions không deploy số sai.
"""
import os, re, json, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DASH = os.path.join(ROOT, 'dashboard')


def run(script):
    print(f'\n>>> {script}', flush=True)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    subprocess.run([sys.executable, os.path.join(HERE, script)], check=True, env=env)


def read_js(name, var):
    with open(os.path.join(DASH, name), encoding='utf-8') as f:
        m = re.search(rf'window\.{var} = (.*?);\n', f.read(), re.S)
    return json.loads(m.group(1))


def check():
    """Kiểm tra nhanh các đồng nhất thức kế toán và đầu ra; trả về danh sách lỗi."""
    rows, errs = read_js('data.js', 'BANK_DATA'), []
    if len(rows) < 250:
        errs.append(f'chỉ có {len(rows)} dòng ngân hàng-năm (kỳ vọng ≥ 250)')
    for r in rows:
        tag = f"{r['bank']} {r['year']}"
        if None not in (r['ppop'], r['prov'], r['pbt']) and abs(r['ppop'] - r['prov'] - r['pbt']) > 1:
            errs.append(f'{tag}: LN trước DP − DP ≠ LNTT')
        if None not in (r['pbt'], r['tax'], r['pat']) and abs(r['pbt'] - r['tax'] - r['pat']) > 1:
            errs.append(f'{tag}: LNTT − thuế ≠ LNST')
        if r['loans'] is not None and r['ta'] is not None and r['loans'] > r['ta']:
            errs.append(f'{tag}: cho vay > tổng tài sản')
    for m in read_js('econ.js', 'ECON')['models']:
        if m['n'] < 30 or not m['coefs']:
            errs.append(f"mô hình {m['id']}: mẫu quá nhỏ hoặc không có hệ số")
    return errs


if __name__ == '__main__':
    if '--xlsx' in sys.argv:
        run('build_dataset.py')
    for s in ('export_dashboard_data.py', 'analysis.py', 'econometrics.py'):
        run(s)
    errs = check()
    print(f'\n>>> kiểm tra dữ liệu: {"đạt" if not errs else f"{len(errs)} lỗi"}')
    for e in errs[:30]:
        print('  -', e)
    sys.exit(1 if errs else 0)
