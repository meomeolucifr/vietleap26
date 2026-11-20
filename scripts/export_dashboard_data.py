"""Xuất số liệu nền (tỷ VND) cho dashboard mô phỏng giảm lãi suất cho vay -> dashboard/data.js"""
import json, os, sys, datetime
sys.path.insert(0, os.path.dirname(__file__))
import build_dataset as b
from sample import keep, SAMPLE, YEARS

OUT = os.path.join(b.ROOT, 'dashboard', 'data.js')

# tên trường -> chỉ số cột trong bảng panel (triệu VND; chi phí đã là số dương)
FIELDS = {
    'loans': 13,      # Cho vay khách hàng (dư nợ gộp)
    'llr': 14,        # Dự phòng rủi ro cho vay khách hàng (số dư)
    'ta': 43,         # Tổng tài sản
    'deposits': 48,   # Tiền gửi khách hàng
    'equity': 72,     # Vốn chủ sở hữu
    'ii': 74,         # Thu nhập lãi và tương tự
    'ie': 75,         # Chi phí lãi và tương tự
    'nii': 76,        # Thu nhập lãi thuần
    'toi': 87,        # Tổng thu nhập hoạt động
    'opex': 88,       # Chi phí hoạt động
    'ppop': 89,       # LN thuần trước chi phí dự phòng
    'prov': 90,       # Chi phí dự phòng rủi ro tín dụng
    'pbt': 91,        # LN trước thuế
    'tax': 94,        # Chi phí thuế TNDN
    'pat': 95,        # LN sau thuế
    'vtc': 126,       # Vốn tự có
    'rwa': 127,       # Tổng tài sản có rủi ro
}

if __name__ == '__main__':
    out = b.load()
    rows = []
    for (code, year), r in sorted(out.items()):
        if not keep(code, year):
            continue
        rec = {'bank': code, 'year': year}
        for k, i in FIELDS.items():
            rec[k] = None if r[i] is None else round(r[i] / 1000, 3)  # triệu -> tỷ VND
        npl_groups = [r[i] for i in range(120, 125)]
        rec['npl_amt'] = round(sum(npl_groups[2:]) / 1000, 3) if None not in npl_groups else None
        rec['npl'] = (sum(npl_groups[2:]) / sum(npl_groups)) if None not in npl_groups and sum(npl_groups) else None
        rec['car_rep'] = r[125]
        rows.append(rec)
    meta = {
        'source': 'FiinPro-X, Báo cáo tài chính hợp nhất năm (BCĐKT, KQKD, Thuyết minh, Báo cáo an toàn vốn), trích xuất 13/10/2026',
        'source_en': 'FiinPro-X, consolidated annual financial statements (balance sheet, income statement, notes, capital adequacy report), extracted 13/10/2026',
        'unit': 'tỷ VND',
        'sample': {'banks': len(SAMPLE), 'years': [YEARS[0], YEARS[-1]],
                   'rule': 'Ngân hàng thương mại niêm yết/đăng ký giao dịch (HOSE, HNX, UPCoM), đủ báo cáo tài chính 2016–2025',
                   'rule_en': 'Commercial banks listed or traded on HOSE, HNX or UPCoM with full 2016–2025 financial statements'},
        'built': datetime.date.today().isoformat(),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('// Sinh tự động bởi scripts/export_dashboard_data.py - không sửa tay\n')
        f.write('window.BANK_META = ' + json.dumps(meta, ensure_ascii=False) + ';\n')
        f.write('window.BANK_DATA = ' + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('saved', OUT, len(rows), 'rows')
