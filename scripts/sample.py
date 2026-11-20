"""Mẫu nghiên cứu: ngân hàng và giai đoạn dùng cho mọi bước phân tích.

Tiêu chí: ngân hàng thương mại có cổ phiếu niêm yết/đăng ký giao dịch (HOSE, HNX, UPCoM) và có đủ
báo cáo tài chính hợp nhất năm 2016–2025. Danh sách và lý do loại nằm ở Data/sample/banks.csv
(sàn giao dịch tra từ FiinX, 20/11/2026). Sửa file đó để đổi mẫu, không sửa code.
"""
import csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YEARS = range(2016, 2026)  # 10 năm

with open(os.path.join(ROOT, 'Data', 'sample', 'banks.csv'), encoding='utf-8') as f:
    BANKS = {r['ticker']: r for r in csv.DictReader(f)}
SAMPLE = sorted(t for t, r in BANKS.items() if r['in_sample'] == '1')


def keep(code, year):
    return code in SAMPLE and year in YEARS
