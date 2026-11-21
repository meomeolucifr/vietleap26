# Rate Cut Lab: mô phỏng giảm lãi suất cho vay

VietLeap Hackathon 2026, From Data to Decision.

Dashboard giúp ALCO/CFO ngân hàng đánh giá: giảm lãi suất cho vay s điểm cơ bản (10 bp = 0,1%) thì lợi nhuận sau thuế, CAR và khả năng trang trải chi phí dự phòng có còn đảm bảo không, và người vay tiết kiệm được bao nhiêu. Mẫu: 25 ngân hàng thương mại niêm yết, báo cáo tài chính hợp nhất năm 2016–2025 (FiinPro-X), cùng số liệu vĩ mô từ FiinX. Song ngữ Việt/Anh (thêm `?lang=en` vào link để mở bản tiếng Anh).

Phương pháp, mô hình, biến và nguồn dữ liệu: [docs/PHUONG_PHAP.md](docs/PHUONG_PHAP.md). Tài liệu nộp bài (Word, bật theo dõi thay đổi): [docs/TeamName_Documentation.docx](docs/TeamName_Documentation.docx).

## Cấu trúc

```
Data/                    Báo cáo tài chính thô xuất từ FiinPro-X, mỗi ngân hàng một file
Data/sample/banks.csv    Mẫu nghiên cứu: 25 ngân hàng, sàn giao dịch, lý do loại các ngân hàng khác
Data/macro/macro_vn.csv  Vĩ mô năm 2015–2025 lấy từ FiinX (GDP, CPI bình quân, lãi suất huy động, tăng trưởng tín dụng), đơn vị %
scripts/
  build_dataset.py       Đọc Data/*.xlsx, gộp thành bảng ngân hàng × năm; --xlsx xuất bảng Excel có công thức
  export_dashboard_data.py  -> dashboard/data.js      (số liệu nền, tỷ VND)
  analysis.py            Dựng panel biến (dùng cho econometrics.py); -> dashboard/analysis.js (tương quan, truyền dẫn; dashboard hiện không hiển thị)
  econometrics.py        -> dashboard/econ.js      (hồi quy panel FE/RE, khai báo trong danh sách MODELS)
  run_pipeline.py        Chạy tất cả các bước trên rồi kiểm tra đồng nhất thức kế toán
  test_regress.js        Kiểm tra dashboard/regress.js (hồi quy trên trình duyệt) khớp kết quả Python: node scripts/test_regress.js
  validate_dataset.py    Đối chiếu bảng gộp với file mẫu (chỉ chạy ở máy local)
dashboard/               Trang web tĩnh (index.html + 3 file .js sinh tự động). Đây là thứ được deploy
Output/                  Bảng panel Excel có công thức
.github/workflows/       Tự chạy pipeline và deploy lên GitHub Pages khi push lên main
```

## Chạy ở máy

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py            # sinh lại dashboard/*.js và kiểm tra dữ liệu
python -m http.server 8000 -d dashboard   # mở http://localhost:8000
```

Mở thẳng `dashboard/index.html` bằng trình duyệt cũng chạy được.

## Thêm hoặc sửa mô hình kinh tế lượng

Sửa danh sách `MODELS` ở đầu [scripts/econometrics.py](scripts/econometrics.py): chọn biến phụ thuộc, biến giải thích, hiệu ứng cố định ngân hàng/năm, loại sai số chuẩn. Chạy lại `python scripts/econometrics.py`; kết quả ghi vào dashboard/econ.js; bảng "Mô hình đề xuất" ở tab Phương pháp đọc các hệ số từ đó (mô hình mới cần thêm một dòng vào hàm `drawModelTable` trong dashboard/index.html). Biến có sẵn nằm trong hàm `panel()` của [scripts/analysis.py](scripts/analysis.py).

Kịch bản vĩ mô (Thuận lợi / Cơ sở / Bất lợi) khai báo trong `SCENARIOS` của cùng file: mỗi kịch bản là chênh lệch vĩ mô giữa hai năm thật, đi qua mô hình `llp_macro` để ra thay đổi tỷ lệ chi phí dự phòng, rồi dashboard đưa vào mô phỏng.

Lưu ý: biến vĩ mô (GDP, CPI…) giống nhau cho mọi ngân hàng trong cùng năm, nên bị hiệu ứng cố định năm hấp thụ. Mô hình có biến vĩ mô phải đặt `time=False` và nên dùng `cov='kernel'` (Driscoll-Kraay).

## Deploy

Mỗi lần push lên nhánh `main`, GitHub Actions cài thư viện, chạy `run_pipeline.py` (dừng nếu kiểm tra dữ liệu không đạt), kiểm tra hồi quy trên trình duyệt khớp Python, rồi đưa thư mục `dashboard/` lên https://meomeolucifr.github.io/vietleap26/. Thêm hoặc sửa dữ liệu rồi push là hồi quy và dashboard tự cập nhật.
