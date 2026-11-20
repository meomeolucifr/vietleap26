"""Phân tích hỗ trợ dashboard giảm lãi suất cho vay.

1. Tương quan (Spearman) giữa các tỷ số ngân hàng, dữ liệu gộp ngân hàng × năm.
2. Truyền dẫn (pass-through): khi lợi suất tài sản thay đổi, chi phí vốn thay đổi bao nhiêu?
   -> kiểm tra giả định "giữ nguyên chi phí huy động" của mô phỏng.
3. Yếu tố quyết định độ nhạy LNST với 1 bp giảm lãi (mặt cắt năm gần nhất).
Kết quả ghi ra dashboard/analysis.js để dashboard hiển thị.
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import build_dataset as b
from export_dashboard_data import FIELDS
from sample import keep

OUT = os.path.join(b.ROOT, 'dashboard', 'analysis.js')
MACRO = os.path.join(b.ROOT, 'Data', 'macro', 'macro_vn.csv')
MACRO_VARS = ['gdp_growth', 'cpi_avg', 'deposit_rate_12m', 'credit_growth']
RNG = np.random.default_rng(2026)


def panel():
    out = b.load()
    rows = []
    for (code, year), r in out.items():
        if not keep(code, year):
            continue
        rec = {'bank': code, 'year': year}
        for k, i in FIELDS.items():
            rec[k] = None if r[i] is None else r[i] / 1000  # tỷ VND
        g = [r[i] for i in range(120, 125)]
        rec['npl'] = sum(g[2:]) / sum(g) if None not in g and sum(g) else None
        rec['liab'] = None if r[57] is None else r[57] / 1000
        rows.append(rec)
    df = pd.DataFrame(rows).sort_values(['bank', 'year']).reset_index(drop=True)
    lag = df.groupby('bank').shift(1)
    consecutive = (df['year'] - lag['year']) == 1
    avg = lambda c: np.where(consecutive, (df[c] + lag[c]) / 2, np.nan)
    df['avg_ta'], df['avg_liab'] = avg('ta'), avg('liab')
    df['yield'] = df['ii'] / df['avg_ta']            # lợi suất tài sản (thu nhập lãi / TTS bình quân)
    df['cost'] = df['ie'] / df['avg_liab']           # chi phí vốn (chi phí lãi / nợ phải trả bình quân)
    df['nim'] = df['nii'] / df['avg_ta']
    df['roa'] = df['pat'] / df['avg_ta']
    df['roe'] = df['pat'] / df['equity']
    df['cir'] = df['opex'] / df['toi']
    df['ldr'] = df['loans'] / df['deposits']
    df['loans_ta'] = df['loans'] / df['ta']
    df['nonii'] = (df['toi'] - df['nii']) / df['toi']
    df['cap'] = df['equity'] / df['ta']
    df['size'] = np.log(df['ta'])
    df['cov'] = df['ppop'] / df['prov']
    df['car'] = np.where(df['vtc'].notna() & df['rwa'].notna(), df['vtc'] / df['rwa'], np.nan)
    # độ nhạy: % LNST mất cho mỗi 10 bp giảm lãi trên toàn bộ dư nợ (thuế 20%)
    df['sens10'] = np.where(df['pat'] > 0, df['loans'] * 0.001 * 0.8 / df['pat'], np.nan)
    lagy = df.groupby('bank')[['yield', 'cost', 'nim', 'roa']].shift(1)
    cons2 = consecutive & ((df['year'] - df.groupby('bank')['year'].shift(1)) == 1)
    for c in ['yield', 'cost', 'nim', 'roa']:
        df['d_' + c] = np.where(cons2, df[c] - lagy[c], np.nan)
    # biến cho mô hình rủi ro tín dụng
    df['avg_loans'] = avg('loans')
    df['llp'] = df['prov'] / df['avg_loans']                                  # chi phí dự phòng / dư nợ bình quân
    df['loang'] = np.where(consecutive, df['loans'] / lag['loans'] - 1, np.nan)  # tăng trưởng dư nợ của ngân hàng
    df['npl_lag'] = np.where(consecutive, lag['npl'], np.nan)
    df['dep_share'] = df['deposits'] / df['liab']
    # vĩ mô (giống nhau cho mọi ngân hàng trong năm), đổi % -> tỷ lệ cho cùng đơn vị với biến ngân hàng
    mac = pd.read_csv(MACRO)
    for c in MACRO_VARS:
        mac[c] = mac[c] / 100
    return df.merge(mac[['year'] + MACRO_VARS], on='year', how='left')


def ols(x, y):
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    r2 = 1 - resid.var() / y.var()
    return beta, r2


def cluster_boot(d, xcol, ycol, n=2000):
    """CI 95% của hệ số góc, bootstrap theo cụm ngân hàng (giữ tương quan trong cùng ngân hàng)."""
    banks = d['bank'].unique()
    groups = {k: g for k, g in d.groupby('bank')}
    slopes = []
    for _ in range(n):
        s = pd.concat([groups[k] for k in RNG.choice(banks, len(banks))])
        slopes.append(ols(s[xcol].values, s[ycol].values)[0][1])
    return np.percentile(slopes, [2.5, 97.5]).tolist()


VARS = {  # mã -> nhãn hiển thị
    'yield': 'Lợi suất tài sản', 'cost': 'Chi phí vốn', 'nim': 'NIM', 'roa': 'ROA', 'roe': 'ROE',
    'cir': 'CIR', 'ldr': 'LDR', 'loans_ta': 'Cho vay/TTS', 'nonii': 'TN ngoài lãi',
    'cap': 'VCSH/TTS', 'npl': 'Nợ xấu', 'size': 'Quy mô', 'sens10': 'Độ nhạy LNST',
}
VARS_EN = {
    'yield': 'Asset yield', 'cost': 'Funding cost', 'nim': 'NIM', 'roa': 'ROA', 'roe': 'ROE',
    'cir': 'Cost/income', 'ldr': 'Loan/deposit', 'loans_ta': 'Loans/assets', 'nonii': 'Non-interest income',
    'cap': 'Equity/assets', 'npl': 'NPL ratio', 'size': 'Size (log assets)', 'sens10': 'Profit sensitivity',
}

if __name__ == '__main__':
    df = panel()
    res = {}

    # 1. ma trận tương quan Spearman (bỏ năm LNST âm vì ROE/độ nhạy mất ý nghĩa)
    d1 = df[df['pat'] > 0][list(VARS)].replace([np.inf, -np.inf], np.nan)
    corr = d1.corr(method='spearman', min_periods=60)
    res['corr'] = {'vars': list(VARS), 'labels': list(VARS.values()), 'labels_en': list(VARS_EN.values()),
                   'matrix': [[None if pd.isna(v) else round(v, 3) for v in row] for row in corr.values],
                   'n': [[int(d1[[a, c]].dropna().shape[0]) for c in VARS] for a in VARS]}

    # 2. truyền dẫn: Δ chi phí vốn theo Δ lợi suất tài sản
    d2 = df[['bank', 'year', 'd_yield', 'd_cost']].dropna()
    q = d2[['d_yield', 'd_cost']].quantile([0.01, 0.99])
    d2 = d2[(d2['d_yield'].between(*q['d_yield'])) & (d2['d_cost'].between(*q['d_cost']))]
    beta, r2 = ols(d2['d_yield'].values, d2['d_cost'].values)
    res['passthrough'] = {
        'beta': round(beta[1], 3), 'alpha_bp': round(beta[0] * 1e4, 1), 'r2': round(r2, 3),
        'r': round(float(np.corrcoef(d2['d_yield'], d2['d_cost'])[0, 1]), 3),
        'ci95': [round(v, 3) for v in cluster_boot(d2, 'd_yield', 'd_cost')],
        'n': len(d2), 'banks': int(d2['bank'].nunique()),
        'years': [int(d2['year'].min()), int(d2['year'].max())],
        'points': [{'bank': r.bank, 'year': int(r.year), 'x': round(r.d_yield * 1e4, 1), 'y': round(r.d_cost * 1e4, 1)}
                   for r in d2.itertuples()],
    }
    # theo năm: trung vị Δ lợi suất và Δ chi phí (bp)
    yr = df.dropna(subset=['d_yield', 'd_cost']).groupby('year')[['d_yield', 'd_cost']].median() * 1e4
    res['by_year'] = [{'year': int(y), 'd_yield': round(r.d_yield, 1), 'd_cost': round(r.d_cost, 1)} for y, r in yr.iterrows()]

    # 3. độ nhạy năm gần nhất và các yếu tố đi kèm
    last = df['year'].max()
    d3 = df[(df['year'] == last) & df['sens10'].notna()].copy()
    drivers = {}
    for c in ['roa', 'loans_ta', 'nim', 'cir', 'npl', 'cap', 'size', 'nonii']:
        s = d3[['sens10', c]].dropna()
        drivers[c] = {'label': VARS[c], 'label_en': VARS_EN[c], 'rho': round(s.corr(method='spearman').iloc[0, 1], 3), 'n': len(s)}
    res['sensitivity'] = {
        'year': int(last), 'drivers': drivers,
        'points': [{'bank': r.bank, 'roa': round(r.roa, 5), 'loans_ta': round(r.loans_ta, 4),
                    'sens10': round(r.sens10, 5), 'nim': round(r.nim, 5),
                    'loans_avg_ta': round(r.loans / r.avg_ta, 4)} for r in d3.itertuples()],
    }
    # 4. NIM giảm có đi cùng ROA giảm không (trong cùng ngân hàng)?
    d4 = df[['bank', 'd_nim', 'd_roa']].dropna()
    b4, r2_4 = ols(d4['d_nim'].values, d4['d_roa'].values)
    res['nim_roa'] = {'beta': round(b4[1], 3), 'r': round(float(np.corrcoef(d4['d_nim'], d4['d_roa'])[0, 1]), 3),
                      'n': len(d4), 'ci95': [round(v, 3) for v in cluster_boot(d4, 'd_nim', 'd_roa')]}

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('// Sinh tự động bởi scripts/analysis.py - không sửa tay\n')
        f.write('window.ANALYSIS = ' + json.dumps(res, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('saved', OUT)
    print('pass-through', {k: v for k, v in res['passthrough'].items() if k != 'points'})
    print('by year', res['by_year'])
    print('nim->roa', res['nim_roa'])
    print('sens drivers', res['sensitivity']['drivers'])
    c = pd.DataFrame(res['corr']['matrix'], index=res['corr']['labels'], columns=res['corr']['labels'])
    print(c.round(2).to_string())
