"""Hồi quy dữ liệu bảng (panel) ngân hàng × năm -> dashboard/econ.js

Thêm hoặc sửa mô hình: chỉ cần sửa danh sách MODELS bên dưới, rồi chạy
    python scripts/econometrics.py
Dashboard tự hiển thị mọi mô hình trong danh sách (tab Phân tích dữ liệu).

Mỗi mô hình:
    id       mã ngắn, không dấu
    title    câu hỏi mô hình trả lời (hiện làm tiêu đề)
    y, x     biến phụ thuộc và danh sách biến giải thích (tên cột trong panel(), xem VARS)
    entity   True = hiệu ứng cố định ngân hàng (bank FE)
    time     True = hiệu ứng cố định năm (year FE), hấp thụ biến động chung của thị trường
    cov      'clustered' (cụm theo ngân hàng), 'kernel' (Driscoll-Kraay) hoặc 'robust'
    trim     bỏ bao nhiêu % đuôi mỗi phía của y và x trước khi ước lượng (0 = không bỏ)
    alt_cov  (tuỳ chọn) cách tính sai số thứ hai để báo thêm p, kiểm tra kết quả có nhạy với lựa chọn SE không
    sample   hàm lọc mẫu (tuỳ chọn), nhận DataFrame và trả về mask
    note     cách đọc kết quả / hạn chế (hiện dưới bảng)

Biến vĩ mô giống nhau cho mọi ngân hàng trong một năm, nên mô hình có biến vĩ mô phải đặt time=False
(nếu không, hiệu ứng năm hấp thụ hết) và nên dùng cov='kernel' (Driscoll-Kraay, chịu được tương quan chéo).
Dữ liệu năm 2016–2025 chỉ có khoảng 10 điểm thời gian, nên hệ số vĩ mô kém chính xác; xem p ở cả hai cách tính SE.

SCENARIOS: kịch bản vĩ mô cho mô phỏng. Cú sốc lấy từ lịch sử (chênh lệch giữa hai năm thật trong
Data/macro/macro_vn.csv), rồi đi qua mô hình SCENARIO_MODEL để ra thay đổi tỷ lệ chi phí dự phòng.
"""
import json, os, sys
import numpy as np, pandas as pd
from scipy import stats
from linearmodels.panel import PanelOLS, RandomEffects

sys.path.insert(0, os.path.dirname(__file__))
from analysis import panel, VARS, VARS_EN, MACRO
import build_dataset as b

OUT = os.path.join(b.ROOT, 'dashboard', 'econ.js')
PANEL_OUT = os.path.join(b.ROOT, 'dashboard', 'panel.js')
# biến thêm cho người dùng tự chọn trên dashboard, ngoài các biến đã dùng trong MODELS
PANEL_EXTRA = ['cost', 'yield', 'roe', 'ldr', 'nonii', 'd_nim', 'd_roa', 'credit_growth', 'car', 'cov', 'nim', 'roa']
RWA_TA = 0.82  # tỷ lệ RWA / tổng tài sản trung vị; cập nhật từ dữ liệu trong __main__
# 4 mô hình chính, mỗi mô hình kiểm chứng một chỉ số an toàn trên dashboard; dashboard vẽ biểu đồ cho từng cái
MAIN = ['pass_bank', 'roa_det', 'car_resp', 'llp_macro']

LABELS = {**VARS, 'd_yield': 'Δ Lợi suất tài sản', 'd_cost': 'Δ Chi phí vốn', 'd_nim': 'Δ NIM', 'd_roa': 'Δ ROA',
          'ldr': 'LDR', 'const': 'Hằng số', 'llp': 'Chi phí DP / dư nợ BQ', 'loang': 'Tăng trưởng dư nợ',
          'npl_lag': 'Nợ xấu năm trước', 'dep_share': 'Tiền gửi / nợ phải trả',
          'gdp_growth': 'Tăng trưởng GDP', 'cpi_avg': 'Lạm phát CPI BQ', 'deposit_rate_12m': 'LS huy động >12 tháng',
          'credit_growth': 'Tăng trưởng tín dụng toàn hệ thống', 'd_car': 'Δ CAR', 'car': 'CAR',
          'd_npl_lead': 'Δ Nợ xấu năm sau', 'rwa_ta': 'RWA / tổng tài sản'}
LABELS_EN = {**VARS_EN, 'd_yield': 'Δ Asset yield', 'd_cost': 'Δ Funding cost', 'd_nim': 'Δ NIM', 'd_roa': 'Δ ROA',
             'ldr': 'Loan/deposit', 'const': 'Constant', 'llp': 'Provisions / avg loans', 'loang': 'Loan growth',
             'npl_lag': 'NPL ratio, prior year', 'dep_share': 'Deposits / liabilities',
             'gdp_growth': 'Real GDP growth', 'cpi_avg': 'CPI inflation (avg)', 'deposit_rate_12m': 'Deposit rate >12m',
             'credit_growth': 'System credit growth', 'd_car': 'Δ CAR', 'car': 'CAR',
             'd_npl_lead': 'Δ NPL ratio next year', 'rwa_ta': 'RWA / total assets'}


def vn(x, d=2):
    """Số theo kiểu Việt Nam (dấu phẩy thập phân) cho câu chữ sinh tự động."""
    return f'{x:.{d}f}'.replace('.', ',')


# so_what(B, P): B = {biến: hệ số}, P = {biến: p}; trả về (câu tiếng Việt, câu tiếng Anh) nêu ý nghĩa cho quyết định.
# Số trong câu lấy từ kết quả hồi quy, nên tự cập nhật khi dữ liệu đổi.
MODELS = [
    dict(id='pass_mkt', title='Chi phí vốn đi theo lợi suất tài sản bao nhiêu (gồm biến động chung của thị trường)?',
         title_en='How much does funding cost follow asset yield, including market-wide rate moves?',
         y='d_cost', x=['d_yield'], entity=True, time=False, cov='clustered', trim=1,
         so_what=lambda B, P: (f'Khi cả hệ thống cùng đổi lãi suất, chi phí vốn đi theo gần 1:1 (β = {vn(B["d_yield"])}). Chỉ áp dụng khi NHNN và cả thị trường cùng giảm lãi.',
                            f'When the whole system moves rates, funding cost follows almost 1:1 (β = {B["d_yield"]:.2f}). Applies only to a market-wide easing.'),
         note='Không có hiệu ứng năm: hệ số gồm cả phần cả thị trường cùng đổi lãi suất. So sánh với mô hình kế tiếp.',
         note_en='No year effects: the coefficient includes market-wide rate moves. Compare with the next model.'),
    dict(id='pass_bank', title='Khi riêng một ngân hàng đổi lợi suất (so với mặt bằng năm đó), chi phí vốn của nó đổi bao nhiêu?',
         title_en='When one bank alone moves its yield (relative to that year\'s market), how much does its funding cost move?',
         y='d_cost', x=['d_yield'], entity=True, time=True, cov='clustered', trim=1,
         so_what=lambda B, P: (f'Nếu chỉ một ngân hàng tự giảm lãi cho vay, khoảng {B["d_yield"] * 100:.0f}% khoản giảm được bù bằng chi phí vốn thấp hơn. Đây là giá trị mặc định của ô "Chi phí vốn giảm theo" trong mô phỏng.',
                            f'If one bank cuts lending rates on its own, about {B["d_yield"] * 100:.0f}% of the cut is offset by lower funding cost. This is the default "funding cost offset" in the simulator.'),
         note='Hiệu ứng năm hấp thụ biến động chung, nên hệ số gần với tình huống một ngân hàng tự giảm lãi.',
         note_en='Year effects absorb market-wide moves, so the coefficient is close to the case of a single bank cutting on its own.'),
    dict(id='roa_det', title='Yếu tố nào đi cùng ROA của ngân hàng?',
         title_en='What moves with a bank\'s ROA?',
         y='roa', x=['nim', 'cir', 'npl', 'cap', 'size', 'loans_ta'], entity=True, time=True, cov='clustered', trim=1,
         sample=lambda d: d['pat'] > 0,
         so_what=lambda B, P: (f'Sau khi kiểm soát chu kỳ và các yếu tố khác, NIM giảm 1 điểm đi kèm ROA giảm {vn(B["nim"])} điểm, thấp hơn mức 0,8 mô phỏng giả định. Ngân hàng bù được một phần, nên thiệt hại LNST trong mô phỏng là cận trên.',
                            f'Controlling for the cycle and other factors, a 1-point fall in NIM goes with a {B["nim"]:.2f}-point fall in ROA, below the 0.8 the simulator assumes. Banks offset part of it, so the simulated profit loss is an upper bound.'),
         note='Tương quan có điều kiện, không phải nhân quả; các biến giải thích có thể cùng chịu tác động của chu kỳ.',
         note_en='Conditional correlation, not causation; regressors may share cyclical drivers.'),
    dict(id='loan_resp', title='Ngân hàng giảm lãi thì tín dụng có tăng nhanh hơn (làm RWA tăng, CAR giảm) không?',
         title_en='Does a bank that cuts rates grow its loan book faster (raising RWA and lowering CAR)?',
         y='loang', x=['d_yield'], entity=True, time=True, cov='clustered', trim=1,
         so_what=lambda B, P: (('Không thấy bằng chứng: khi một ngân hàng giảm lợi suất so với mặt bằng năm đó, tăng trưởng tín dụng của nó không nhanh hơn '
                                f'(p = {vn(P["d_yield"])}). Điều này khớp với cơ chế hạn mức tăng trưởng tín dụng (room) do NHNN phân bổ, nên mô phỏng giữ RWA không đổi.',
                                'No evidence: when a bank lowers its yield relative to the market, its loan growth is not faster '
                                f'(p = {P["d_yield"]:.2f}). This fits the SBV\'s bank-by-bank credit-growth quotas, so the simulator holds RWA constant.')
                               if P['d_yield'] >= 0.1 else
                               ('Có bằng chứng tín dụng phản ứng với mức lợi suất; mô phỏng nên cộng thêm phần RWA tăng khi tính CAR.',
                                'Loan growth does respond to yield; the simulator should add the RWA increase when computing CAR.')),
         note='Hiệu ứng năm hấp thụ room tín dụng chung và chu kỳ; hệ số đo phản ứng riêng của từng ngân hàng. Không loại trừ cầu tín dụng phản ứng khi cả thị trường giảm lãi.',
         note_en='Year effects absorb system-wide credit quotas and the cycle; the coefficient measures each bank\'s own response. Does not rule out a credit-demand response to a market-wide cut.'),
    dict(id='car_resp', title='Lợi nhuận và tăng trưởng tín dụng làm CAR thay đổi bao nhiêu?',
         title_en='How much do profit and loan growth move CAR?',
         y='d_car', x=['roa', 'loang'], entity=True, time=True, cov='clustered', trim=1,
         so_what=lambda B, P: (f'ROA tăng 1 điểm đi kèm CAR tăng {vn(B["roa"])} điểm. Công thức của mô phỏng (lợi nhuận giữ lại / RWA) ngầm định khoảng {vn(1 / RWA_TA, 2)}: trong thực tế CAR đổi ít hơn công thức, nên mức giảm CAR trên dashboard là thận trọng.' if B["roa"] < 1 / RWA_TA else f'ROA tăng 1 điểm đi kèm CAR tăng {vn(B["roa"])} điểm. Công thức của mô phỏng (lợi nhuận giữ lại / RWA) ngầm định khoảng {vn(1 / RWA_TA, 2)}.',
                               f'A 1-point rise in ROA goes with a {B["roa"]:.2f}-point rise in CAR. The simulator\'s formula (retained profit / RWA) implies about {1 / RWA_TA:.2f}: in practice CAR moves less than the formula, so the CAR fall shown on the dashboard is conservative.' if B["roa"] < 1 / RWA_TA else f'A 1-point rise in ROA goes with a {B["roa"]:.2f}-point rise in CAR. The simulator\'s formula (retained profit / RWA) implies about {1 / RWA_TA:.2f}.'),
         note='CAR = vốn tự có / RWA. Năm nào số này lệch quá 0,3 điểm % so với cả CAR thuyết minh lẫn dòng CAR trong Báo cáo an toàn vốn (lỗi dữ liệu nguồn, ví dụ VPB 2022–2023) thì thay bằng CAR công bố; năm thiếu Báo cáo an toàn vốn thì lấp bằng CAR công bố, chỉ từ 2020 khi mọi ngân hàng đã tính theo Thông tư 41.',
         note_en='CAR = regulatory capital / RWA. Where this differs by more than 0.3 pp from both the reported CAR in the notes and the CAR line in the capital adequacy report (a source data error, e.g. VPB 2022–2023), reported CAR is used; years without a capital adequacy report are filled with reported CAR, only from 2020 when all banks use Circular 41.'),
    dict(id='npl_resp', title='Giảm lãi có giúp nợ xấu năm sau giảm không?',
         title_en='Does a lower rate reduce next year\'s NPLs?',
         y='d_npl_lead', x=['d_yield'], entity=True, time=True, cov='clustered', trim=1,
         so_what=lambda B, P: (('Không thấy bằng chứng: lợi suất giảm không đi kèm nợ xấu năm sau giảm '
                                f'(p = {vn(P["d_yield"])}). Mô phỏng vì vậy không cộng thêm lợi ích này.',
                                'No evidence: a lower yield does not come with lower NPLs the following year '
                                f'(p = {P["d_yield"]:.2f}). The simulator therefore adds no such benefit.')
                               if P['d_yield'] >= 0.1 else
                               ('Có bằng chứng nợ xấu năm sau phản ứng với mức lợi suất; nên cân nhắc đưa vào mô phỏng.',
                                'Next-year NPLs do respond to yield; consider adding this to the simulator.')),
         note='Nợ xấu năm sau trừ nợ xấu năm nay, theo thay đổi lợi suất năm nay; có hiệu ứng năm.',
         note_en='Next year\'s NPL ratio minus this year\'s, on this year\'s change in yield; with year effects.'),
    dict(id='nim_macro', title='Điều kiện vĩ mô có giải thích được NIM của ngân hàng không?',
         title_en='Do macro conditions explain bank NIM?',
         y='nim', x=['deposit_rate_12m', 'gdp_growth', 'cpi_avg', 'loang', 'npl', 'size'],
         entity=True, time=False, cov='kernel', alt_cov='clustered', trim=1,
         so_what=lambda B, P: (('Không: không hệ số vĩ mô nào có ý nghĩa ở mức 5%. Vì vậy kịch bản vĩ mô không đổi NIM trong mô phỏng.',
                             'No: no macro coefficient is significant at 5%. The macro scenarios therefore do not change NIM in the simulator.')
                            if all(P[c] >= 0.05 for c in MACRO_COLS if c in P) else
                            ('Có ít nhất một hệ số vĩ mô có ý nghĩa ở mức 5%; xem bảng. Kịch bản vĩ mô hiện chưa đổi NIM trong mô phỏng.',
                             'At least one macro coefficient is significant at 5%; see the table. The macro scenarios do not yet change NIM in the simulator.')),
         note='Kênh lãi suất đã tính trực tiếp bằng công thức, hồi quy lại sẽ tính trùng. Với khoảng 10 năm dữ liệu, hệ số vĩ mô không đủ chính xác.',
         note_en='The rate channel is already computed directly; adding it again would double count. With ~10 years of data, macro coefficients are imprecise.'),
    dict(id='llp_macro', title='Kinh tế chậm lại thì chi phí dự phòng tăng bao nhiêu?',
         title_en='How much do provisions rise when the economy slows?',
         y='llp', x=['gdp_growth', 'cpi_avg', 'loang', 'npl_lag', 'size'],
         entity=True, time=False, cov='kernel', alt_cov='clustered', trim=1,
         so_what=lambda B, P: (f'GDP tăng chậm đi 1 điểm % thì chi phí dự phòng tăng khoảng {-B["gdp_growth"] * 100:.0f} bp trên dư nợ. Hệ số này tạo ra kịch bản Bất lợi và Thuận lợi trong mô phỏng.',
                            f'Each 1-point slowdown in GDP growth raises provisions by about {-B["gdp_growth"] * 100:.0f} bp of loans. This coefficient drives the Adverse and Favourable scenarios.'),
         note='Chỉ dùng hệ số vĩ mô có p < 0,10 theo SE Driscoll-Kraay. Hệ số GDP mất ý nghĩa với SE cụm theo ngân hàng, nên kịch bản có độ bất định lớn. '
              'Giai đoạn 2020–2021 có chính sách cơ cấu nợ (Thông tư 01/2020) nên dự phòng có thể phản ứng chậm hơn thực tế.',
         note_en='Only macro coefficients with p < 0.10 (Driscoll-Kraay SE) are used. The GDP coefficient is not significant with bank-clustered SE, so the scenarios are uncertain. '
                 'Loan-restructuring forbearance in 2020–2021 (Circular 01/2020) may have delayed provisioning.'),
]

SCENARIO_MODEL = 'llp_macro'
SCENARIO_P = 0.10
SCENARIOS = [  # (mã, nhãn, nhãn EN, năm gốc, năm đích, mô tả, mô tả EN); cú sốc = giá trị năm đích − năm gốc
    ('good', 'Thuận lợi', 'Favourable', 2024, 2025, 'Như 2024 → 2025: GDP tăng tốc', 'Like 2024 → 2025: growth accelerates'),
    ('base', 'Cơ sở', 'Base', None, None, 'Giữ điều kiện vĩ mô của năm nền', 'Macro conditions of the base year'),
    ('bad', 'Bất lợi', 'Adverse', 2019, 2021, 'Như 2019 → 2021 (Covid): GDP giảm tốc mạnh', 'Like 2019 → 2021 (Covid): sharp slowdown'),
]


def scenarios(fitted):
    m = next(x for x in fitted if x['id'] == SCENARIO_MODEL)
    beta = {c['var']: c['b'] for c in m['coefs'] if c['var'] in MACRO_COLS and c['p'] < SCENARIO_P}
    mac = pd.read_csv(MACRO).set_index('year')
    out = []
    for sid, label, label_en, y0, y1, desc, desc_en in SCENARIOS:
        shocks = {} if y0 is None else {c: float(mac.loc[y1, c] - mac.loc[y0, c]) / 100 for c in MACRO_COLS}
        dllp = sum(beta.get(c, 0) * v for c, v in shocks.items())
        out.append({'id': sid, 'label': label, 'label_en': label_en, 'desc': desc, 'desc_en': desc_en,
                    'shocks': shocks, 'dllp': dllp, 'used': {c: LABELS[c] for c in beta}})
    return out


MACRO_COLS = ['gdp_growth', 'cpi_avg', 'deposit_rate_12m', 'credit_growth']


def trim_tails(d, cols, pct):
    if not pct:
        return d
    q = d[cols].quantile([pct / 100, 1 - pct / 100])
    keep = np.ones(len(d), bool)
    for c in cols:
        keep &= d[c].between(q.loc[pct / 100, c], q.loc[1 - pct / 100, c]).values
    return d[keep]


def fit(df, m):
    cols = [m['y']] + m['x']
    d = df[m['sample'](df)] if 'sample' in m else df
    d = d[['bank', 'year'] + cols].replace([np.inf, -np.inf], np.nan).dropna()
    d = trim_tails(d, cols, m.get('trim', 0)).set_index(['bank', 'year'])
    rhs = ' + '.join(['1'] + m['x'] + (['EntityEffects'] if m['entity'] else []) + (['TimeEffects'] if m['time'] else []))
    mod = PanelOLS.from_formula(f"{m['y']} ~ {rhs}", data=d, drop_absorbed=True)
    COV = {'clustered': dict(cov_type='clustered', cluster_entity=True),
           'kernel': dict(cov_type='kernel'), 'robust': dict(cov_type='robust')}
    r = mod.fit(**COV[m['cov']])
    alt = mod.fit(**COV[m['alt_cov']]) if m.get('alt_cov') else None
    ci = r.conf_int()
    coefs = [{'var': v, 'label': LABELS.get(v, v), 'label_en': LABELS_EN.get(v, v), 'b': float(r.params[v]), 'se': float(r.std_errors[v]),
              't': float(r.tstats[v]), 'p': float(r.pvalues[v]), 'lo': float(ci.loc[v, 'lower']), 'hi': float(ci.loc[v, 'upper']),
              **({'p_alt': float(alt.pvalues[v])} if alt is not None else {}), 'macro': v in MACRO_COLS}
             for v in r.params.index if v != 'Intercept']
    out = {k: m[k] for k in ('id', 'title', 'title_en', 'y', 'x', 'entity', 'time', 'cov', 'note', 'note_en')}
    out['alt_cov'] = m.get('alt_cov')
    if 'so_what' in m:
        out['so_what'], out['so_what_en'] = m['so_what']({c['var']: c['b'] for c in coefs}, {c['var']: c['p'] for c in coefs})
    out.update({
        'y_label': LABELS.get(m['y'], m['y']), 'y_label_en': LABELS_EN.get(m['y'], m['y']), 'trim': m.get('trim', 0),
        'spec': f"{m['y']} ~ {' + '.join(m['x'])}" + (' + bank FE' if m['entity'] else '') + (' + year FE' if m['time'] else ''),
        'n': int(r.nobs), 'banks': int(r.entity_info['total']), 'years': [int(d.index.get_level_values(1).min()), int(d.index.get_level_values(1).max())],
        'r2_within': float(r.rsquared_within), 'r2_overall': float(r.rsquared_overall),
        'f_robust': {'stat': float(r.f_statistic_robust.stat), 'p': float(r.f_statistic_robust.pval)},
        'coefs': coefs,
    })
    if m['entity'] and len(m['x']) > 0:
        out['hausman'] = hausman(d, m)
    return out, r


def hausman(d, m):
    """FE hay RE? H0: hiệu ứng ngân hàng không tương quan với biến giải thích (RE nhất quán).
    Dùng sai số không hiệu chỉnh theo đúng định nghĩa kiểm định; chỉ xét hiệu ứng ngân hàng."""
    f = f"{m['y']} ~ 1 + {' + '.join(m['x'])}"
    fe = PanelOLS.from_formula(f + ' + EntityEffects', data=d).fit()
    re = RandomEffects.from_formula(f, data=d).fit()
    xs = m['x']
    diff = (fe.params[xs] - re.params[xs]).values
    V = (fe.cov.loc[xs, xs] - re.cov.loc[xs, xs]).values
    stat = float(diff @ np.linalg.pinv(V) @ diff)
    # χ² âm: V_FE − V_RE không xác định dương ở mẫu hữu hạn, kiểm định không dùng được (không lấy trị tuyệt đối)
    return {'stat': stat, 'df': len(xs), 'p': float(stats.chi2.sf(stat, len(xs))) if stat >= 0 else None}


if __name__ == '__main__':
    df = panel()
    RWA_TA = float(df['rwa_ta'].median())
    res = []
    for m in MODELS:
        out, r = fit(df, m)
        res.append(out)
        print(f"\n=== {m['id']}: {out['spec']}  (n={out['n']}, banks={out['banks']}, R2 within={out['r2_within']:.3f})")
        print(r.summary.tables[1])
        if 'hausman' in out:
            h = out['hausman']
            print(f"Hausman chi2({h['df']}) = {h['stat']:.2f}, p = {h['p'] if h['p'] is None else round(h['p'], 3)}")
    scen = scenarios(res)
    for s in scen:
        print(f"kịch bản {s['label']}: ΔLLP = {s['dllp'] * 1e4:+.1f} bp dư nợ", {k: round(v * 100, 2) for k, v in s['shocks'].items()})
    mac = pd.read_csv(MACRO)
    macro = {'years': mac['year'].tolist(),
             'series': [{'id': c, 'label': LABELS[c], 'label_en': LABELS_EN[c], 'values': mac[c].tolist()} for c in MACRO_COLS],
             'source': 'FiinX: GDP thực (GSO), CPI so cùng kỳ bình quân 12 tháng (GSO), lãi suất huy động >12 tháng (trung điểm, NHNN, tháng 12), tăng trưởng tín dụng (NHNN, tháng 12)',
             'source_en': 'FiinX: real GDP (GSO), CPI year-on-year averaged over 12 months (GSO), >12-month deposit rate (midpoint, SBV, December), credit growth (SBV, December)'}
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('// Sinh tự động bởi scripts/econometrics.py - không sửa tay\n')
        f.write('window.ECON = ' + json.dumps({'models': res, 'scenarios': scen, 'scenario_model': SCENARIO_MODEL, 'macro': macro, 'main': MAIN, 'rwa_ta': RWA_TA},
                                              ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('\nsaved', OUT)

    # dữ liệu panel cho phần "Tự chạy hồi quy" trên dashboard (dashboard/regress.js ước lượng lại trên trình duyệt)
    cols = sorted({c for m in MODELS for c in [m['y']] + m['x']} | set(PANEL_EXTRA))
    num = lambda v: None if pd.isna(v) or np.isinf(v) else float(f'{v:.10g}')
    rows = [[bank, int(year), int(pat > 0)] + [num(v) for v in vals]
            for bank, year, pat, vals in zip(df['bank'], df['year'], df['pat'], df[cols].to_numpy(dtype=float))]
    panel_out = {'cols': ['bank', 'year', 'pat_pos'] + cols, 'rows': rows,
                 'labels': {c: LABELS.get(c, c) for c in cols}, 'labels_en': {c: LABELS_EN.get(c, c) for c in cols},
                 'macro': [c for c in cols if c in MACRO_COLS],
                 'presets': [{k: m.get(k) for k in ('id', 'title', 'title_en', 'y', 'x', 'entity', 'time', 'cov', 'alt_cov', 'trim')}
                             | {'pat_pos': 'sample' in m} for m in MODELS]}
    with open(PANEL_OUT, 'w', encoding='utf-8') as f:
        f.write('// Sinh tự động bởi scripts/econometrics.py - không sửa tay\n')
        f.write('window.PANEL = ' + json.dumps(panel_out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('saved', PANEL_OUT, len(rows), 'rows')
