"""Gộp sheet Bảng cân đối kế toán + Kết quả kinh doanh của các file FiinPro-X
thành 1 bảng, mỗi dòng = 1 ngân hàng - 1 năm, cùng format với file mẫu KLTN."""
import openpyxl, glob, collections, os
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # thư mục gốc repo, chạy được cả Windows lẫn CI Linux
TEMPLATE = os.path.join(ROOT, 'Copy of DL_KLTN_D2_NH25-26_Nguyen_Thi_Tuyet_Tam_050610221298.xlsx')
OUT = os.path.join(ROOT, 'Output', 'VietLeap26_Bank_Panel_with_ratios.xlsx')
UNIT = 1000  # nguồn: tỷ VND -> mẫu: triệu VND
CODE = {'AGRB': 'AGR', 'BAOVIETBAN': 'BaoVietBank'}

# (nhãn nguồn, lần xuất hiện) -> chỉ số cột trong mẫu
BS = {
 ('Tiền mặt, vàng bạc, đá quý',1):2, ('Tiền gửi tại Ngân hàng nhà nước Việt Nam',1):3,
 ('Tiền gửi tại các TCTD khác và cho vay các TCTD khác',1):4, ('Tiền gửi tại các TCTD khác',1):5,
 ('Cho vay các TCTD khác',1):6, ('Dự phòng rủi ro',1):7,
 ('Chứng khoán kinh doanh',1):8, ('Chứng khoán kinh doanh',2):9,
 ('Dự phòng giảm giá chứng khoán kinh doanh',1):10,
 ('Các công cụ tài chính phái sinh và các tài sản tài chính khác',1):11,
 ('Cho vay khách hàng',1):12, ('Cho vay khách hàng',2):13, ('Dự phòng rủi ro cho vay khách hàng',1):14,
 ('Chứng khoán đầu tư',1):15, ('Chứng khoán đầu tư sẵn sàng để bán',1):16,
 ('Chứng khoán đầu tư giữ đến ngày đáo hạn',1):17, ('Dự phòng giảm giá chứng khoán đầu tư',1):18,
 ('Góp vốn, đầu tư dài hạn',1):19, ('Đầu tư vào công ty con',1):20,
 ('Đầu tư vào công ty liên doanh',1):21, ('Đầu tư dài hạn khác',1):22,
 ('Dự phòng giảm giá đầu tư dài hạn',1):23,
 ('Tài sản cố định',1):24, ('Tài sản cố định hữu hình',1):25,
 ('Nguyên giá TSCĐ',1):26, ('Hao mòn TSCĐ',1):27,
 ('Tài sản cố định thuê tài chính',1):28, ('Nguyên giá TSCĐ',2):29, ('Hao mòn TSCĐ',2):30,
 ('Tài sản cố định vô hình',1):31, ('Nguyên giá TSCĐ',3):32, ('Hao mòn TSCĐ',3):33,
 ('Bất động sản đầu tư',1):34, ('Nguyên giá bất động sản đầu tư',1):35, ('Hao mòn bất động sản đầu tư',1):36,
 ('Tài sản Có khác',1):37, ('Các khoản phải thu',1):38, ('Các khoản lãi và phí phải thu',1):39,
 ('Tài sản thuế TNDN hoãn lại',1):40, ('Tài sản Có khác',2):41, ('Trong đó: Lợi thế thương mại',1):42,
 ('TỔNG TÀI SẢN',1):43,
 ('Các khoản nợ chính phủ và NHNN Việt Nam',1):44, ('Tiền gửi và vay các Tổ chức tín dụng khác',1):45,
 ('Tiền gửi của các tổ chức tín dụng khác',1):46, ('Vay các tổ chức tín dụng khác',1):47,
 ('Tiền gửi của khách hàng',1):48,
 ('Các công cụ tài chính phái sinh và các khoản nợ tài chính khác',1):49,
 ('Vốn tài trợ, uỷ thác đầu tư của Chính phủ và các tổ chức tín dụng khác',1):50,
 ('Phát hành giấy tờ có giá',1):51, ('Các khoản nợ khác',1):52,
 ('Các khoản lãi, phí phải trả',1):53, ('Thuế TNDN hoãn lại phải trả',1):54,
 ('Các khoản phải trả và công nợ khác',1):55, ('Dự phòng rủi ro khác',1):56,
 ('Tổng nợ phải trả',1):57,
 ('Vốn của tổ chức tín dụng',1):58, ('Vốn điều lệ',1):59, ('Vốn đầu tư XDCB',1):60,
 ('Thặng dư vốn cổ phần',1):61, ('Cổ phiếu Quỹ',1):62, ('Cổ phiếu ưu đãi',1):63, ('Vốn khác',1):64,
 ('Quỹ của tổ chức tín dụng',1):65, ('Chênh lệch tỷ giá hối đoái',1):66,
 ('Chênh lệch đánh giá lại tài sản',1):67, ('Lợi nhuận chưa phân phối',1):68,
 ('Lợi ích của cổ đông thiểu số',1):69, ('Lợi ích của cổ đông thiểu số (trước 2015)',1):70,
 ('NỢ PHẢI TRẢ VÀ VỐN CHỦ SỞ HỮU',1):71, ('VỐN CHỦ SỞ HỮU',1):72,
}
# cột mẫu lưu dưới dạng số dương (dự phòng, hao mòn, cổ phiếu quỹ) -> đảo dấu nguồn
BS_NEG = {7, 10, 14, 18, 23, 27, 30, 33, 36, 62}
# KQKD: (chỉ số cột, hệ số dấu) — mẫu lưu chi phí là số dương
IS = {
 ('Thu nhập lãi và các khoản thu nhập tương tự',1):(74,1), ('Chi phí lãi và các chi phí tương tự',1):(75,-1),
 ('Thu nhập lãi thuần',1):(76,1), ('Thu nhập từ hoạt động dịch vụ',1):(77,1),
 ('Chi phí hoạt động dịch vụ',1):(78,-1), ('Lãi/Lỗ thuần từ hoạt động dịch vụ',1):(79,1),
 ('Lãi/(lỗ) thuần từ hoạt động kinh doanh ngoại hối và vàng',1):(80,1),
 ('Lãi/(lỗ) thuần từ mua bán chứng khoán kinh doanh',1):(81,1),
 ('Lãi/(lỗ) thuần từ mua bán chứng khoán đầu tư',1):(82,1),
 ('Thu nhập từ hoạt động khác',1):(83,1), ('Chi phí hoạt động khác',1):(84,-1),
 ('Lãi/(lỗ) thuần từ hoạt động khác',1):(85,1), ('Thu nhập từ góp vốn, mua cổ phần',1):(86,1),
 ('Tổng thu nhập hoạt động',1):(87,1), ('Chi phí hoạt động',1):(88,-1),
 ('LN thuần từ hoạt động kinh doanh trước CF dự phòng rủi ro tín dụng',1):(89,1),
 ('Chi phí dự phòng rủi ro tín dụng',1):(90,-1), ('Tổng lợi nhuận trước thuế',1):(91,1),
 ('Chi phí thuế TNDN hiện hành',1):(92,-1), ('Chi phí thuế TNDN hoãn lại',1):(93,1),
 ('Chi phí thuế thu nhập doanh nghiệp',1):(94,-1), ('Lợi nhuận sau thuế',1):(95,1),
 ('Lợi ích của cổ đông thiểu số',1):(96,-1),
}


def read_sheet(ws):
    rows = list(ws.iter_rows(min_row=8, max_col=30, values_only=True))
    code = rows[0][1]
    years = [h for h in rows[3][1:] if h]
    data = collections.defaultdict(dict)  # năm -> {(nhãn, lần): giá trị}
    occ = collections.Counter()
    for r in rows[4:]:
        if r[0] == 'Contact':
            break
        if r[0] is None:
            continue
        lab = r[0].strip()
        occ[lab] += 1
        for y, v in zip(years, r[1:1 + len(years)]):
            data[int(y)][(lab, occ[lab])] = v
    return code, data


# đầu vào từ sheet Thuyết minh (nhóm nợ 1-5) -> cột 120-124; CAR báo cáo -> cột 125
NPL_GROUPS = [('Nợ đủ tiêu chuẩn', 120), ('Nợ cần chú ý', 121), ('Nợ dưới tiêu chuẩn', 122),
              ('Nợ nghi ngờ', 123), ('Nợ xấu có khả năng mất vốn', 124)]
CAR_COL = 125
VTC_COL, RWA_COL = 126, 127  # Báo cáo an toàn vốn: vốn tự có, tổng tài sản có rủi ro
CARC_COL, CARD_COL = 128, 129  # CAR tính = VTC/RWA; chênh lệch so với CAR báo cáo
CARS_COL = 130  # dòng "Tỷ lệ an toàn vốn" trong Báo cáo an toàn vốn
NCOL = 131


def load():
    out = {}  # (mã, năm) -> giá trị theo cột của mẫu (0-96) + cột đầu vào (120-125)
    files = glob.glob(os.path.join(ROOT, 'Data', '*.xlsx'))
    for f in sorted(p for p in files if not os.path.basename(p).startswith('~$')):  # bỏ file khoá của Excel
        wb = openpyxl.load_workbook(f, read_only=True)
        code, bs = read_sheet(wb['Bảng cân đối kế toán'])
        _, is_ = read_sheet(wb['Kết quả kinh doanh'])
        _, tm = read_sheet(wb['Thuyết minh'])
        _, cp = read_sheet(wb['Báo cáo an toàn vốn'])
        code = CODE.get(code, code)
        for y in sorted(set(bs) | set(is_)):
            row = out.setdefault((code, y), [None] * NCOL)
            row[0], row[1] = code, y
            for k, c in BS.items():
                v = bs.get(y, {}).get(k)
                if v is not None:
                    row[c] = v * UNIT * (-1 if c in BS_NEG else 1)
            for k, (c, s) in IS.items():
                v = is_.get(y, {}).get(k)
                if v is not None:
                    row[c] = v * UNIT * s
            for lab, c in NPL_GROUPS:
                v = tm.get(y, {}).get((lab, 1))
                if v is not None:
                    row[c] = v * UNIT
            v = tm.get(y, {}).get(('CAR', 1))
            if v:  # 0 = ngân hàng không công bố
                row[CAR_COL] = v
            for lab, c in (('Vốn tự có', VTC_COL), ('Tổng tài sản có rủi ro', RWA_COL), ('Tỷ lệ an toàn vốn', CARS_COL)):
                v = cp.get(y, {}).get((lab, 1))
                if v:
                    row[c] = v if c == CARS_COL else v * UNIT
    return out


def formulas(r, first, last):
    """Công thức các biến phân tích cho dòng r; first-last: khoảng dòng của cùng ngân hàng."""
    L = get_column_letter
    c = lambda i: f'{L(i + 1)}{r}'
    ta, loans, dep, eq, liab = c(43), c(13), c(48), c(72), c(57)
    ni, toi, opex, nii = c(95), c(87), c(88), c(76)
    g = [c(i) for i in range(120, 125)]
    roa_rng = f'${L(106)}${first}:${L(106)}${last}'
    f = {
        101: f'=IFERROR(LN({c(102)}),"")',
        102: f'=IFERROR(({c(105)}+{c(107)})/{c(104)},"")',
        103: f'=LN({ta})',
        104: f'=IFERROR(STDEV({roa_rng}),"")',
        105: f'={ni}/{ta}',
        106: f'={ni}/{eq}',
        107: f'={eq}/{ta}',
        108: f'=IF({c(CAR_COL)}<>"",{c(CAR_COL)},{c(CARC_COL)})',
        CARC_COL: f'=IFERROR({c(VTC_COL)}/{c(RWA_COL)},"")',
        CARD_COL: f'=IF(AND({c(CAR_COL)}<>"",{c(CARC_COL)}<>""),{c(CARC_COL)}-{c(CAR_COL)},"")',
        109: f'={opex}/{toi}',
        110: f'={loans}/{dep}',
        111: f'=1-(({nii}/{toi})^2+(({toi}-{nii})/{toi})^2)',
        112: f'=IF(COUNT({g[0]}:{g[4]})<5,"",({g[2]}+{g[3]}+{g[4]})/SUM({g[0]}:{g[4]}))',
        113: f'=({c(2)}+{c(3)}+{c(4)}+{c(8)}+{c(11)})/{ta}',
        114: f'={liab}/{ta}',
        115: f'=({toi}-{nii})/{toi}',
        118: f'={nii}/{ta}',
    }
    return {i: (x if x.startswith(('=IFERROR', '=IF(')) else f'=IFERROR({x[1:]},"")') for i, x in f.items()}


PCT = {105, 106, 107, 108, 109, 110, 112, 113, 114, 115, 118, 125, 128, 129, 130}

if __name__ == '__main__':
    from sample import keep
    out = {k: v for k, v in load().items() if keep(*k)}  # chỉ ngân hàng và năm trong mẫu (Data/sample/banks.csv)
    tw = openpyxl.load_workbook(TEMPLATE, read_only=True)
    th = list(next(tw['DỮ LIỆU TỪ 2013 kltn'].iter_rows(max_row=1, values_only=True)))
    header = th[:97] + [None] * (NCOL - 97)
    for i in range(101, 119):
        header[i] = th[i]
    header[117] = 'INF'
    for (lab, c) in NPL_GROUPS:
        header[c] = f'Dư nợ {lab} (Thuyết minh, triệu VND)'
    header[CAR_COL] = 'CAR báo cáo (Thuyết minh)'
    header[VTC_COL] = 'Vốn tự có (Báo cáo an toàn vốn, triệu VND)'
    header[RWA_COL] = 'Tổng tài sản có rủi ro (Báo cáo an toàn vốn, triệu VND)'
    header[CARC_COL] = 'CAR tính = Vốn tự có / Tổng TS có rủi ro'
    header[CARD_COL] = 'Chênh lệch CAR tính - CAR báo cáo'
    header[CARS_COL] = 'CAR (Báo cáo an toàn vốn)'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'DU_LIEU_NH_NAM'
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    keys = sorted(out)
    span = {}
    for n, k in enumerate(keys, start=2):
        a, b_ = span.get(k[0], (n, n))
        span[k[0]] = (a, n)
    blue = Font(color='0000FF')
    for n, k in enumerate(keys, start=2):
        row = [round(v) if isinstance(v, float) and 2 <= i < 120 else v for i, v in enumerate(out[k])]
        ws.append(row)
        first, last = span[k[0]]
        for i, f in formulas(n, first, last).items():
            ws.cell(row=n, column=i + 1, value=f)
        for i in list(range(120, 128)) + [CARS_COL]:
            ws.cell(row=n, column=i + 1).font = blue
        for i in PCT:
            ws.cell(row=n, column=i + 1).number_format = '0.00%'
        for i in (101, 102, 103, 104, 111):
            ws.cell(row=n, column=i + 1).number_format = '0.0000'
    ws.freeze_panes = 'C2'
    ws.row_dimensions[1].height = 75
    notes = wb.create_sheet('GIAI_THICH')
    for line in [
        ['Biến', 'Công thức (theo cột của bảng)', 'Ghi chú'],
        ['ROA', 'Lợi nhuận sau thuế / Tổng tài sản', 'Cuối kỳ, không bình quân'],
        ['ROE', 'Lợi nhuận sau thuế / Vốn chủ sở hữu', 'Cuối kỳ'],
        ['CAP', 'Vốn chủ sở hữu / Tổng tài sản', ''],
        ['CAR', 'Lấy CAR báo cáo (Thuyết minh) nếu có; nếu trống thì = Vốn tự có (DW) / Tổng TS có rủi ro (DX)', 'Công thức khớp CAR báo cáo trong ±0,05 điểm % ở phần lớn các dòng; cột DY = CAR tính, DZ = chênh lệch'],
        ['CIR', 'Chi phí hoạt động / Tổng thu nhập hoạt động', 'Khác file mẫu (mẫu dùng LNTT/TNHĐ)'],
        ['LDR', 'Cho vay khách hàng (gộp) / Tiền gửi khách hàng', ''],
        ['1-HHI', '1 - [(TNLT/TNHĐ)^2 + (TN ngoài lãi/TNHĐ)^2]', 'Đa dạng hóa thu nhập; TN ngoài lãi = TNHĐ - TNLT'],
        ['NPL', '(Nhóm 3+4+5) / (Nhóm 1..5)', 'Từ dư nợ phân loại ở Thuyết minh (cột DQ-DU)'],
        ['LIQ', '(Tiền mặt + TG NHNN + TG/cho vay TCTD + CKKD + phái sinh) / Tổng tài sản', 'Như file mẫu'],
        ['LEV', 'Tổng nợ phải trả / Tổng tài sản', ''],
        ['NM', '(TNHĐ - TNLT thuần) / TNHĐ', 'Tỷ trọng thu nhập ngoài lãi'],
        ['NIM', 'Thu nhập lãi thuần / Tổng tài sản', 'Như file mẫu (không dùng TS sinh lời bình quân)'],
        ['SIZE', 'LN(Tổng tài sản)', 'Mẫu dùng LOG10'],
        ['dlc(ROA)', 'STDEV của ROA theo từng ngân hàng, toàn kỳ', ''],
        ['Z-Score', '(ROA + CAP) / dlc(ROA)', 'log z score = LN(Z-Score)'],
        ['GDP, INF', 'Để trống', 'Chưa có dữ liệu vĩ mô trong thư mục Data'],
    ]:
        notes.append(line)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print('saved', OUT, len(out), 'rows')
