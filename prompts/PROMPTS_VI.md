# AI prompts — Rate Cut Lab (Team 1)

Các prompt nhóm dùng với trợ lý AI (Claude, qua Claude Code trong VS Code) để xây dựng sản phẩm, xếp theo thứ tự công việc. Trợ lý có quyền đọc/ghi thư mục dự án, chạy Python/Node, dùng FiinX MCP và GitHub CLI.

---

## 0. Bối cảnh chung (gửi đầu phiên)

```
Nhóm mình thi VietLeap Hackathon 2026 "From Data to Decision". Chấm: Sản phẩm 40, Thuyết trình 40, Làm việc nhóm 20.
Nộp: sản phẩm, tài liệu có lịch sử chỉnh sửa (vấn đề nghiên cứu, dữ liệu và hạn chế, kết quả, ghi nhận dùng AI,
phân công), mã nguồn mở, AI prompts, thuyết trình tiếng Anh kèm tóm tắt tiếng Việt.
Repo: https://github.com/w-nhannt/vietleap26 (chứa code, data, sản phẩm, tài liệu, prompts).

Đề tài: mô phỏng việc ngân hàng giảm lãi suất cho vay s điểm cơ bản (10 bp = 0,1%) ảnh hưởng thế nào đến
(1) % thay đổi lợi nhuận sau thuế, (2) số tiền người vay tiết kiệm, (3) khả năng trang trải dự phòng, (4) CAR.
Người dùng là ALCO/CFO ngân hàng; bám theo file Proposal_Giam_lai_suat_cho_vay_VCB.docx (kịch bản 25/50 bp,
mục tiêu giữ 90% LNST). Nhóm chọn đề tài và chốt các kết luận; bạn hỗ trợ dữ liệu, code, dashboard, phản biện.
```

---

## 1. Dữ liệu

### 1.1 Gộp báo cáo tài chính thành bảng panel

```
Trong thư mục Data/ là file FiinPro-X xuất cho từng ngân hàng (sheet Bảng cân đối kế toán, Kết quả kinh doanh,
Thuyết minh, Báo cáo an toàn vốn; đơn vị tỷ VND). Gộp thành một bảng theo đúng định dạng file mẫu
"Copy of DL_KLTN_...xlsx" (sheet "DỮ LIỆU TỪ 2013 kltn"): mỗi dòng là một ngân hàng - một năm, cột theo mẫu,
đơn vị triệu VND. Lưu ý nhãn trùng tên trong FiinPro (dùng nhãn + lần xuất hiện), chi phí/dự phòng lưu số dương
như mẫu, bỏ qua file khoá ~$ của Excel, hai file VBB thì gộp. Viết script scripts/build_dataset.py, xuất
Output/VietLeap26_Bank_Panel_with_ratios.xlsx, kèm script đối chiếu với các dòng trùng trong file mẫu.
```

### 1.2 Tỷ số tính bằng công thức Excel

```
Các cột tỷ số (log z, Z-Score, SIZE, độ lệch ROA, ROA, ROE, CAP, CAR, CIR, LDR, 1-HHI, NPL, LIQ, LEV, NM, NIM)
phải là công thức Excel tính từ ô số liệu, không ghi số cứng. Thêm cột nợ nhóm 1–5 (Thuyết minh), CAR công bố,
vốn tự có và tổng tài sản có rủi ro (Báo cáo an toàn vốn). CAR = vốn tự có / RWA: kiểm tra khớp với CAR công bố
ở các năm có số, rồi dùng công thức đó cho các ô trống. Thêm sheet GIAI_THICH ghi công thức từng biến.
```

### 1.3 Mẫu nghiên cứu

```
Dùng FiinX MCP lấy danh sách ngân hàng ngành ICB 8355 kèm sàn giao dịch. Chọn mẫu 25 ngân hàng thương mại niêm yết
hoặc đăng ký giao dịch (HOSE/HNX/UPCoM) có đủ BCTC 2016–2025; ghi danh sách và lý do loại vào Data/sample/banks.csv,
mọi script đọc mẫu từ file này.
```

### 1.4 Số liệu vĩ mô

```
Dùng FiinX MCP lấy 2015–2025: tăng trưởng GDP thực, CPI so cùng kỳ theo tháng (tính bình quân năm), lãi suất huy
động trên 12 tháng (trung điểm, tháng 12), tăng trưởng tín dụng toàn hệ thống (tháng 12). Lưu Data/macro/macro_vn.csv.
```

### 1.5 Bảng kỳ định lại lãi suất

```
Sheet "Rủi ro lãi suất" trong file FiinPro có dư nợ cho vay khách hàng theo kỳ định lại. Xuất 4 nhóm đổi lãi trong
12 tháng (dưới 1, 1–3, 3–6, 6–12 tháng) và phần còn lại cho từng ngân hàng-năm; đánh dấu dùng được khi tổng các nhóm
khớp dư nợ gộp trên BCĐKT trong ±10%. Kiểm tra VCB 2025 phải ra 2.666 tỷ ở 25 bp như đề xuất ALCO.
```

---

## 2. Mô hình mô phỏng

```
Viết hàm mô phỏng cho một ngân hàng-năm, tính trên BCTC năm nền cho 12 tháng sau quyết định (tỷ VND):
- Dư nợ hiệu lực E = α × Σ dư nợ nhóm kỳ định lại × tháng hưởng lãi mới / 12, với 11,5 / 10 / 7,5 / 3 tháng cho
  nhóm dưới 1 / 1–3 / 3–6 / 6–12 tháng, trên 1 năm và quá hạn = 0. Thiếu bảng thì E = dư nợ × α × số tháng / 12
  (mặc định 12, cận trên).
- Người vay tiết kiệm T = E × s / 10.000; người gửi tiền gánh φ × T; LNTT giảm T(1 − φ); thuế 20%; LNST giảm phần còn lại.
- CAR mới = CAR nền − LNST giảm × k / RWA (k = 100%, RWA giữ nguyên). Nếu VTC/RWA lệch CAR công bố > 0,3 điểm %
  thì dùng CAR công bố và suy ra RWA, gắn nhãn ước tính.
- Trang trải dự phòng = (LN trước dự phòng − LNTT giảm) / chi phí dự phòng.
- Mức giảm tối đa giữ q% LNST và điểm hoà vốn tính bằng công thức đóng.
- Kịch bản vĩ mô: cộng Δ(chi phí dự phòng/dư nợ) × dư nợ vào chi phí dự phòng, tách riêng khỏi kênh giảm lãi.
Xử lý ngân hàng lỗ, thiếu dữ liệu vốn. Đối chiếu: đặt φ = 0 thì VCB 2025 phải ra 41 bp, LNST −6,1% ở 25 bp.
```

---

## 3. Kinh tế lượng

```
Viết scripts/econometrics.py dùng linearmodels PanelOLS trên 25 ngân hàng × 2016–2025, bỏ 1% đuôi mỗi phía.
Khai báo mô hình trong danh sách MODELS (id, tiêu đề VI/EN, y, x, FE ngân hàng, FE năm, loại SE, câu kết luận
sinh từ hệ số):
1. pass_mkt: Δ chi phí vốn ~ Δ lợi suất tài sản, FE ngân hàng, SE cụm.
2. pass_bank: như trên thêm FE năm (phản ứng riêng của một ngân hàng) → dùng làm φ mặc định của mô phỏng.
3. roa_det: ROA ~ NIM + CIR + nợ xấu + VCSH/TTS + quy mô + cho vay/TTS, FE hai chiều (so với giả định 0,8).
4. car_resp: ΔCAR (VTC/RWA) ~ ROA + tăng trưởng dư nợ, FE hai chiều (so với 1 / (RWA/TTS)).
5. loan_resp: tăng trưởng dư nợ ~ Δ lợi suất, FE hai chiều.
6. npl_resp: Δ nợ xấu năm sau ~ Δ lợi suất, FE hai chiều.
7. nim_macro: NIM ~ LS huy động + GDP + CPI + tăng trưởng dư nợ + nợ xấu + quy mô, FE ngân hàng, SE Driscoll-Kraay.
8. llp_macro: chi phí DP/dư nợ BQ ~ GDP + CPI + tăng trưởng dư nợ + nợ xấu năm trước + quy mô, FE ngân hàng, D-K.
Mô hình vĩ mô báo thêm p theo SE cụm; kiểm định Hausman (χ² âm thì ghi là không dùng được).
Kịch bản vĩ mô lấy chênh lệch giữa hai năm thật: Thuận lợi 2024→2025, Bất lợi 2019→2021, đi qua hệ số vĩ mô có
p < 0,10 của llp_macro. Xuất dashboard/econ.js và dashboard/panel.js (dữ liệu panel cho phần hồi quy trên trình duyệt).
```

---

## 4. Dashboard

```
Dựng dashboard HTML tĩnh (dashboard/index.html, đọc data.js, econ.js, panel.js, regress.js) cho ALCO/CFO, nhìn như
dashboard dữ liệu chuyên nghiệp: font Be Vietnam Pro, thẻ bo góc xanh dương/navy, chế độ sáng/tối (nhớ lựa chọn,
mặc định theo hệ điều hành), song ngữ VI/EN (nút chuyển, link #en/#vi), tận dụng bề ngang màn hình. Bảng màu
phân loại đã kiểm tra mù màu, không dùng hai trục y, mọi biểu đồ có tooltip, trạng thái có icon kèm chữ.

Đầu trang: một dòng nêu người dùng và câu hỏi quyết định; tiêu đề là kết luận tự tính ("VCB giảm được tối đa X bp
mà vẫn giữ 90% lợi nhuận"); dòng phụ một câu; chọn ngân hàng và năm nền (có tuỳ chọn "Tất cả các năm").

Tab Mô phỏng:
- Khung điều chỉnh: ô số bp lớn + thanh trượt + nút 0/10/25/50/100; ô dư nợ được giảm lãi; ô thời điểm đổi lãi
  với nút "Theo BCTC" / "12 tháng (cận trên)"; ô chi phí vốn giảm theo với nút "Dữ liệu (φ từ pass_bank)" /
  "Xấu nhất 0%"; nút mục tiêu giữ LNST 85/90/95% kèm ghi chú "lựa chọn của ban lãnh đạo"; nút kịch bản vĩ mô.
  Khi cuộn qua khung này thì hiện thanh điều chỉnh gọn ghim đầu trang, đồng bộ hai chiều.
- Bốn thẻ KPI: người vay tiết kiệm (thẻ nổi bật), LNST (thanh đo so mục tiêu), trang trải dự phòng, CAR (đồng hồ
  0–20% có vạch 8%). Mỗi thẻ có nhãn trạng thái và nút "Cách tính" hiện công thức với số thật (thẻ tiết kiệm hiện
  bảng kỳ định lại).
- Biểu đồ "Giảm bao nhiêu thì còn giữ được mục tiêu lợi nhuận?": đường % LNST giữ lại theo bp, vùng xanh đạt mục
  tiêu, vạch mục tiêu, dải mờ theo khoảng tin cậy 95% của φ, nét đứt cho hai kịch bản vĩ mô còn lại; mô tả ghi độ
  dốc mỗi 10 bp và khoảng của mức giảm tối đa; rê chuột xem từng mức, bấm để chọn.
- So sánh 25 ngân hàng (Δ LNST / giảm tối đa / trang trải DP / CAR sau): thanh ngang, vạch ngưỡng theo chỉ tiêu
  (mất 10%, mức bp đang xét, 1 và 2 lần, 8%), vạch trung vị, thanh không đạt tô đỏ, mỏng tô vàng; câu kết luận
  "x/25 ngân hàng…" và so ngân hàng đang chọn với trung vị kèm lý do ROA; ngân hàng lãi quá mỏng ghi riêng.
- Ma trận kịch bản vĩ mô × 0/25/50 bp (ô: % LNST giữ lại ✓/!, CAR, trang trải DP; bấm ô để chọn) và bảng các
  mức giảm thường cân nhắc.
- Chế độ "Tất cả các năm": thẻ KPI có biểu đồ cột nhỏ theo năm, đường độ nhạy mỗi năm một đường, bảng nhiệt
  ngân hàng × năm tô theo thứ hạng, bảng theo năm bấm để xem năm đó.

Tab Phương pháp & dữ liệu:
- Bảng "Mô hình đề xuất": mắt xích từ mức giảm đến chỉ số an toàn, mô hình kiểm chứng, ý nghĩa.
- Bốn thẻ mô hình kiểm chứng (pass_bank, roa_det, car_resp, llp_macro): biểu đồ added-variable (độ dốc = hệ số),
  đường giả định của mô phỏng, câu kết luận tự tính, nhãn ý nghĩa thống kê; cả bốn cố định giai đoạn
  2020–2025, không có nút tuỳ chọn. Thẻ dự phòng vẽ GDP và chi phí dự phòng theo năm (hai biểu đồ nhỏ, không trục kép).
- Dưới mỗi thẻ mô hình có một câu "Cách đọc" bằng lời thường.
- "Tự chạy hồi quy": biến phụ thuộc là một chỉ số an toàn (ROA, CAR, NIM, khả năng trang trải dự phòng), biến giải
  thích là các chỉ số tài chính trên BCTC (ROA, ROE, NIM, CAR, khả năng trang trải dự phòng, CIR, nợ xấu, VCSH/TTS, quy
  mô, cho vay/TTS, LDR, tăng trưởng dư nợ, tỷ trọng thu nhập ngoài lãi) khác biến phụ thuộc, không dùng biến vĩ mô; cố
  định FE ngân hàng và bỏ 1% đuôi, SE Driscoll-Kraay hoặc robust; bảng hệ số có cột VIF (trên biến đã khử hiệu ứng
  ngân hàng; đánh dấu trên 5, cảnh báo trên 10), thanh CI, mỗi hệ số một câu diễn giải, và biểu đồ.
- Bảng biến (công thức, dòng BCTC, nguồn Cục Thống kê/NHNN), số liệu nền truy về dòng nguồn, công thức, giả định và hạn chế, thuật ngữ (rê chuột chữ gạch chấm để xem giải thích).
Chữ viết thành câu tự nhiên, gọn; giải thích kỹ thuật để trong tooltip. Chạy thử trên trình duyệt, chụp màn hình
kiểm tra nhãn đè, tràn, lỗi console.
```

### 4.1 Hồi quy trên trình duyệt

```
Viết dashboard/regress.js tái tạo PanelOLS của linearmodels: bỏ đuôi theo phân vị kiểu pandas, khử FE một/hai chiều,
SE cụm theo ngân hàng, Driscoll-Kraay (Bartlett, độ trễ ⌊4(T/100)^(2/9)⌋), robust, điều chỉnh n/(n − d − k) như
auto_df, p theo phân phối t, R² within; trả thêm dữ liệu added-variable. Viết scripts/test_regress.js đối chiếu với
econ.js cho mọi mô hình (lệch hệ số < 1e-6, SE < 1e-4).
```

---

## 5. Hạ tầng

```
Viết scripts/run_pipeline.py chạy tuần tự: gộp dữ liệu → data.js → phân tích → kinh tế lượng, rồi kiểm tra đồng nhất
thức kế toán (LN trước DP − DP = LNTT; LNTT − thuế = LNST), dừng nếu sai. Thêm requirements.txt, README, .gitignore.
GitHub Actions: mỗi lần push lên main thì chạy pipeline, chạy test_regress.js, rồi deploy thư mục dashboard lên
GitHub Pages. Chuyển repo sang public, bật Pages.
```

---

## 6. Tài liệu và thuyết trình

```
Soạn docs/METHODOLOGY.md: câu hỏi quyết định, mẫu, mô hình hai tầng, bảng mô hình hồi quy, lý do chọn FE/SE,
hạn chế, bảng biến kèm dòng BCTC và nguồn.
```

```
Soạn file Word Team1_Documentation.docx (tiếng Anh, kèm bản tiếng Việt), bật Track Changes: vấn đề nghiên cứu,
dữ liệu và hạn chế, phương pháp, kết quả (VCB 2025, 25 ngân hàng, hồi quy, đối chiếu đề xuất ALCO), ghi nhận dùng AI,
phân công, nhật ký phiên bản.
```

```
Viết kịch bản thuyết trình tiếng Anh khoảng 6 phút cho giám khảo (học thuật quốc tế, FiinGroup) và sinh viên.
Đi theo 5 câu hỏi: vì sao ngân hàng giảm lãi, ai trả tiền, thế nào là an toàn và vì sao 90%, vì sao tin được con số
(ví dụ quán cà phê cho φ 36% so với 98%), nên giảm bao nhiêu. Có demo 3 thao tác, slide tiêu đề là câu kết luận,
ngân hàng câu hỏi Q&A kèm câu trả lời một câu, tóm tắt tiếng Việt.
```
