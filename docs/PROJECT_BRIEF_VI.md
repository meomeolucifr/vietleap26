# Rate Cut Lab: toàn bộ thông tin đề tài

VietLeap Hackathon 2026 "From Data to Decision" · Team 1 (4MAN WARRIOR)
Thành viên: Đặng Đình Pháp, Phạm Huy Hoàng, Nguyễn Phạm Xuân Dương, Nguyễn Thiện Nhân

- Dashboard: https://w-nhannt.github.io/vietleap26/ (thêm `#en` để xem tiếng Anh)
- Mã nguồn, dữ liệu, tài liệu: https://github.com/w-nhannt/vietleap26
- Số liệu trong file này lấy từ dashboard bản mới nhất (21/11/2026).

---

## 1. Vấn đề nghiên cứu

**Người dùng:** ALCO (Hội đồng quản lý tài sản nợ – tài sản có) và CFO của một ngân hàng thương mại.

**Câu hỏi quyết định:** ngân hàng giảm lãi suất cho vay bao nhiêu điểm cơ bản (bp; 10 bp = 0,1%) thì người vay được lợi bao nhiêu, mà ngân hàng vẫn an toàn?

"An toàn" gồm ba ngưỡng:

| Chỉ số | Ngưỡng | Nguồn của ngưỡng |
|---|---|---|
| Lợi nhuận sau thuế (LNST) | Giữ ít nhất 90% so với năm nền | Lựa chọn của ban lãnh đạo, lấy từ đề xuất ALCO của VCB; dashboard cho chọn 85/90/95% |
| Tỷ lệ an toàn vốn (CAR) | ≥ 8% | Quy định NHNN (Thông tư 41/2016) |
| Khả năng trang trải dự phòng | ≥ 1 lần (LN trước dự phòng / chi phí dự phòng) | Dưới 1 lần là ngân hàng chuyển sang lỗ |

Chỉ số thứ tư là **tiền người vay tiết kiệm mỗi năm**, tức lợi ích của quyết định.

**Vì sao cần:** giảm lãi không tạo ra tiền mà chuyển tiền. Người vay được lợi; cổ đông (lợi nhuận giảm) và ngân sách (thuế TNDN giảm) gánh chi phí. Câu hỏi của ALCO không phải "có giảm không" mà là "giảm đến đâu thì vẫn an toàn".

---

## 2. Dữ liệu

**Mẫu:** 25 ngân hàng thương mại niêm yết hoặc đăng ký giao dịch (HOSE 22, HNX 1, UPCoM 2), đủ báo cáo tài chính hợp nhất **2016–2025**, tổng cộng 250 quan sát ngân hàng-năm.

- Danh sách: ACB, BID, BVB, CTG, EIB, HDB, KLB, LPB, MBB, MSB, NAB, OCB, SHB, SSB, STB, TCB, TPB, VAB, VBB, VCB, VIB, VPB (HOSE); NVB (HNX); PGB, SGB (UPCoM).
- Loại khỏi mẫu: Agribank, BaoViet Bank (chưa niêm yết); ABBank (thiếu năm 2016); Bac A Bank, PVcomBank (không có file dữ liệu).
- Danh sách và lý do loại nằm ở `Data/sample/banks.csv`.

**Nguồn:**

| Dữ liệu | Nguồn | Dùng để |
|---|---|---|
| BCĐKT, KQKD, thuyết minh, báo cáo an toàn vốn | FiinPro-X, BCTC hợp nhất năm đã kiểm toán (trích xuất 13/10/2026) | Mọi tính toán của mô phỏng |
| Bảng kỳ định lại lãi suất (sheet "Rủi ro lãi suất") | Thuyết minh BCTC qua FiinPro-X | Tính dư nợ thực sự hưởng lãi mới trong 12 tháng (E) |
| GDP thực, CPI bình quân, lãi suất huy động >12 tháng, tăng trưởng tín dụng | FiinX (gốc: Cục Thống kê, NHNN), 2015–2025 | Kịch bản vĩ mô |

**Kiểm tra chất lượng dữ liệu:**

- **Đẳng thức kế toán:** LN trước dự phòng − chi phí dự phòng = LNTT; LNTT − thuế = LNST. Pipeline dừng nếu sai.
- **Bảng kỳ định lại:** 231/250 ngân hàng-năm có tổng các nhóm khớp dư nợ gộp trong ±10%. 19 trường hợp còn lại dùng số tháng nhập tay (mặc định 12, cận trên) và có cảnh báo.
- **CAR:**
  - CAR tự tính (vốn tự có / RWA) khớp CAR công bố tới 0,05 điểm % ở 95/105 trường hợp.
  - Phần còn lại là lỗi dữ liệu nguồn. Ví dụ: RWA của VPB 2022–2023 bị thổi lên gần 3 lần; NAB 2022 ghi tỷ lệ vốn cấp 1 vào dòng CAR. Những năm đó dùng CAR công bố.
  - Năm thiếu báo cáo an toàn vốn, từ 2020 trở đi (khi mọi ngân hàng tính theo Thông tư 41), lấp bằng CAR công bố.

**Hạn chế dữ liệu:**

- Báo cáo an toàn vốn chỉ có từ 2019 và không đủ ở mọi ngân hàng. CAR trước 2020 tính theo Thông tư 36 nên không trộn vào.
- Dữ liệu năm, không có số theo tháng hay theo từng khoản vay.

---

## 3. Phương pháp: hai lớp

### Lớp 1: mô phỏng kế toán trên BCTC năm nền

```
E     = Σ dư nợ nhóm kỳ định lại × tháng hưởng lãi mới / 12
        (dưới 1 tháng: 11,5 · 1–3 tháng: 10 · 3–6 tháng: 7,5 · 6–12 tháng: 3 · trên 1 năm: 0)
T     = E × s / 10.000                 tiền người vay tiết kiệm = thu nhập lãi ngân hàng mất
ΔLNTT = T + ΔDP vĩ mô                  chi phí vốn giữ nguyên (trường hợp xấu nhất)
ΔLNST = ΔLNTT × (1 − 20%)
CAR mới = CAR nền − ΔLNST / RWA        RWA giữ nguyên
Trang trải DP = (LN trước DP − T) / (chi phí DP nền + ΔDP vĩ mô)
Mức giảm tối đa = [(1 − mục tiêu) × LNST nền − ΔDP × (1 − thuế)] / [E × (1 − thuế)] × 10.000
Mức an toàn khuyến nghị = mức lớn nhất đạt cả 3 ngưỡng trong cả 3 kịch bản vĩ mô
```

- **Chi phí vốn giữ nguyên:** giả định ngân hàng không hạ được lãi huy động, nên gánh toàn bộ khoản giảm. Đây là trường hợp xấu nhất và cũng là giả định của đề xuất ALCO. Nhóm không dùng hệ số truyền dẫn ước lượng từ dữ liệu, vì đó là tương quan lịch sử, chưa chứng minh được tác động nhân quả. Nếu ngân hàng hạ được cả lãi huy động thì thiệt hại thực tế nhỏ hơn.
- **Đối chiếu với đề xuất ALCO của VCB:** dashboard ra đúng 2.666 tỷ, −6,1% LNST ở 25 bp, −12,1% ở 50 bp, mức tối đa 41 bp.

### Lớp 2: kinh tế lượng (panel 25 ngân hàng, `linearmodels` PanelOLS)

Ba mô hình chính dùng chung giai đoạn **2020–2025**:

| Mô hình | Kiểm tra gì | Kết quả | Ý nghĩa |
|---|---|---|---|
| `roa_det`: ROA ~ NIM + CIR + nợ xấu + VCSH/TTS + quy mô + cho vay/TTS, FE ngân hàng + năm | Mô phỏng giả định NIM mất 1 điểm thì ROA mất 0,8 điểm | 0,33 (p < 0,001; n = 125) | Ngân hàng bù được một phần, nên thiệt hại LNST trên dashboard là **cận trên** |
| `car_resp`: ΔCAR ~ ROA + tăng trưởng dư nợ, FE ngân hàng + năm | Công thức CAR của mô phỏng ngầm định 1,21 | 0,65 (CI −0,04–1,34; p = 0,066; Driscoll-Kraay p < 0,001; n = 115) | 1,21 nằm trong khoảng tin cậy và cao hơn ước lượng: mức giảm CAR trên dashboard là thận trọng |
| `llp_macro`: chi phí DP / dư nợ ~ GDP + CPI + tăng trưởng dư nợ + nợ xấu năm trước + quy mô, FE ngân hàng, SE Driscoll-Kraay | Kinh tế xấu đi thì dự phòng tăng bao nhiêu | GDP −1 điểm % → dự phòng +4,0 bp dư nợ (p < 0,001) | Tạo kịch bản **Bất lợi** (như 2019→2021: dự phòng +17,8 bp) và **Thuận lợi** (−3,7 bp) |

Mô hình phụ:

- `loan_resp`: giảm lãi không làm tín dụng tăng nhanh hơn (p = 0,99), nên giữ RWA không đổi là hợp lý.
- `npl_resp`: giảm lãi không làm nợ xấu năm sau giảm, nên mô phỏng không cộng thêm lợi ích này.
- `nim_macro`: biến vĩ mô không làm đổi NIM, nên không thêm kênh này.

**Lựa chọn kỹ thuật:**

- Hiệu ứng cố định ngân hàng và năm.
- Sai số chuẩn theo cụm ngân hàng, hoặc Driscoll-Kraay cho mô hình có biến vĩ mô.
- Cắt 1% mỗi đuôi.
- Kiểm định Hausman.
- Bản hồi quy chạy trên trình duyệt (`regress.js`) khớp Python tới khoảng 1e-8, được kiểm tra tự động mỗi lần deploy.

**Phần "Tự chạy hồi quy" trên dashboard:**

- Kéo các chỉ số trên BCTC vào ô biến phụ thuộc và ô biến độc lập; hệ số tính lại ngay.
- Có cột **VIF** để kiểm tra đa cộng tuyến: trên 5 thì đánh dấu, trên 10 thì cảnh báo. Ví dụ: ROA, ROE và VCSH/TTS cùng lúc cho VIF > 10, vì ROA ≈ ROE × VCSH/TTS.

---

## 4. Kết quả

### Vietcombank, năm nền 2025, kịch bản cơ sở

| Chỉ tiêu | Trước | Giảm 25 bp |
|---|---|---|
| Người vay tiết kiệm | – | **2.666 tỷ đồng/năm** (2,5 triệu/năm cho mỗi 1 tỷ dư nợ được giảm lãi) |
| LNST | 35.198 tỷ | 33.065 tỷ (**−6,1%**, giữ 93,9%: đạt) |
| CAR | 11,56% | 11,45% (trên 8%: đạt) |
| Trang trải dự phòng | 14,8 lần | 14,0 lần (đạt) |
| Ai gánh 2.666 tỷ | | Cổ đông khoảng 2.133 tỷ (lợi nhuận giảm), ngân sách khoảng 533 tỷ (thuế) |

| Giới hạn | Kết quả |
|---|---|
| Mức giảm tối đa giữ 90% LNST (kịch bản cơ sở) | **41 bp** (bằng đề xuất ALCO) |
| Kịch bản Bất lợi | **13 bp**, cũng là **mức an toàn khuyến nghị** |
| Mục tiêu 95% / 85% | 20 bp / 61 bp |
| Chi phí biên | Mỗi 10 bp mất khoảng 2,4% LNST |
| 25 bp trong kịch bản Bất lợi | LNST −12,8% (giữ 87,2%): **trượt** mục tiêu 90% |

**Kết luận cho VCB:** giảm 13 bp an toàn dù kinh tế diễn biến thế nào. 25 bp chỉ an toàn nếu kinh tế không xấu đi. Trên 41 bp thì trượt ngay cả ở kịch bản cơ sở.

### So sánh 25 ngân hàng (giảm 25 bp, năm 2025)

- **19/25 ngân hàng** vẫn giữ được 90% lợi nhuận.
- Sáu ngân hàng không đạt: NVB (lợi nhuận gần bằng 0), BVB, EIB, STB, BID, PGB.
- Độ nhạy lợi nhuận gắn rất chặt với ROA (Spearman ρ ≈ −0,95), không phụ thuộc quy mô. BIDV là ngân hàng lớn nhưng vẫn trượt vì biên lợi nhuận mỏng.
- **Hàm ý chính sách:** lời kêu gọi giảm lãi đồng loạt dồn gánh nặng lên ngân hàng có lợi nhuận mỏng. Mức giảm nên tính theo sức chịu đựng của từng ngân hàng.

---

## 5. Sản phẩm

**Dashboard (HTML tĩnh, GitHub Pages, song ngữ Việt/Anh, giao diện sáng/tối):**

- **Tab Mô phỏng:**
  - Tiêu đề là kết luận (mức giảm tối đa).
  - Dải "Mức an toàn khuyến nghị".
  - 4 thẻ chỉ số: tiết kiệm của người vay, LNST, trang trải dự phòng, CAR; mỗi thẻ có nút "Cách tính" ra công thức với số thật.
  - Khung điều chỉnh: ô bp, thanh trượt, mục tiêu 85/90/95%, kịch bản vĩ mô, giả định thời điểm đổi lãi.
  - Biểu đồ độ nhạy; so sánh 25 ngân hàng; ma trận kịch bản × mức giảm; bảng các mức thường xét.
  - Nút **"Tóm tắt cho ALCO"** ra bản tóm tắt một trang, sao chép được.
  - Chế độ "Tất cả các năm" (2016–2025).
- **Tab Phương pháp & dữ liệu:** tự chạy hồi quy (kéo-thả biến, VIF), bảng biến và nguồn, số liệu nền truy về từng dòng BCTC, công thức, giả định và hạn chế, thuật ngữ.

**Hạ tầng:** mỗi lần push lên `main`, GitHub Actions chạy lại pipeline Python (gộp dữ liệu, tính biến, hồi quy), kiểm tra đẳng thức kế toán, kiểm tra hồi quy trên trình duyệt khớp Python, rồi deploy.

**Tài liệu nộp:**

- `docs/Team1_Documentation.docx` (bản Anh) và `docs/Team1_Documentation_VI.docx` (bản Việt), có Track Changes.
- `docs/METHODOLOGY.md`.
- `prompts/PROMPTS.md`.
- Slide tiếng Anh, có tóm tắt tiếng Việt.

---

## 6. Giả định và hạn chế

- Kết quả là tác động tăng thêm trong 12 tháng so với năm nền, không phải dự báo.
- Chi phí vốn giữ nguyên (trường hợp xấu nhất), nên thiệt hại thực tế chỉ có thể nhỏ hơn.
- Tác động tuyến tính theo mức giảm. Thực tế có thể cong, vì lãi thấp hơn giúp người vay trả nợ tốt hơn.
- Trong mỗi nhóm kỳ định lại, thời điểm đổi lãi lấy trung điểm; khoản vay lãi cố định đến hạn giả định tái tục ở lãi mới.
- Hệ số hồi quy là tương quan có điều kiện, không phải nhân quả. Hệ số GDP nhạy với cách tính sai số; giai đoạn 2020–2021 có chính sách cơ cấu nợ (Thông tư 01/2020).

---

## 7. Phân công công việc theo ngành học

Điền tên từng thành viên vào cột "Thành viên" cho đúng ngành. Mỗi người phụ trách một phần chính và trình bày các slide tương ứng.

### Ngân hàng: [Thành viên]
**Vai trò:** chủ đề và nghiệp vụ; bảo đảm bài toán đúng với cách ALCO làm việc.
- Chọn đề tài và câu hỏi quyết định; viết đề xuất ALCO cho VCB (25/50 bp, mục tiêu giữ 90% LNST).
- Xác định ba ngưỡng an toàn và căn cứ: CAR 8% theo Thông tư 41, ý nghĩa của mục tiêu 90% và của khả năng trang trải dự phòng.
- Đọc thuyết minh BCTC; xây cách tính E từ bảng kỳ định lại lãi suất (mô hình repricing gap, trung điểm từng nhóm).
- Đối chiếu kết quả dashboard với đề xuất ALCO (2.666 tỷ, −6,1%, 41 bp); xác nhận giả định chi phí vốn giữ nguyên.
- Diễn giải kết quả so sánh 25 ngân hàng (vì sao BID, STB, EIB trượt) và hàm ý chính sách.
- **Trình bày:** slide 1–3 (mở đầu, tình huống, bốn chỉ số an toàn) và slide 8.

### Thuế: [Thành viên]
**Vai trò:** dòng tiền sau thuế và câu hỏi "ai gánh".
- Xây chuỗi LNTT → thuế TNDN 20% → LNST; kiểm tra thuế suất hiệu dụng của từng ngân hàng so với 20%.
- Tính phân bổ chi phí của khoản giảm lãi: cổ đông khoảng 2.133 tỷ, ngân sách khoảng 533 tỷ (VCB, 25 bp).
- Kiểm tra đẳng thức kế toán (LN trước DP − DP = LNTT; LNTT − thuế = LNST) trên 250 ngân hàng-năm.
- Phân tích tác động đến lợi nhuận giữ lại và vốn tự có (kênh từ LNST sang CAR).
- Phụ trách tài liệu Word: các phần Kết quả và Giả định, hạn chế; theo dõi lịch sử chỉnh sửa.
- **Trình bày:** slide 5 (25 bp nghĩa là gì) và slide 6 (các giới hạn).

### Toán thống kê: [Thành viên]
**Vai trò:** dữ liệu và kinh tế lượng; bảo đảm con số đáng tin.
- Thiết kế mẫu (25 ngân hàng × 10 năm) và quy tắc loại; xử lý ngoại lai (cắt 1% mỗi đuôi).
- Đối chiếu CAR tự tính với CAR công bố; quy tắc thay thế lỗi nguồn và lấp năm thiếu từ 2020.
- Ước lượng các mô hình panel (FE ngân hàng và năm, SE cụm hoặc Driscoll-Kraay, Hausman); chọn giai đoạn 2020–2025.
- Dựng kịch bản vĩ mô Thuận lợi và Bất lợi từ hệ số `llp_macro`.
- Kiểm định VIF; kiểm định các giả thuyết bổ sung (tín dụng, nợ xấu, NIM theo vĩ mô).
- **Trình bày:** slide 4 (hai lớp mô hình); trả lời câu hỏi về phương pháp.

### Khoa học máy tính: [Thành viên]
**Vai trò:** sản phẩm và hạ tầng.
- Viết pipeline Python: gộp file FiinPro-X thành panel, tính biến, xuất dữ liệu cho dashboard, chạy hồi quy.
- Xây dashboard HTML/JS: mô phỏng, biểu đồ, so sánh 25 ngân hàng, bản tóm tắt ALCO, song ngữ, phần tự chạy hồi quy kéo-thả.
- Viết `regress.js` (hồi quy panel trên trình duyệt) và bài kiểm tra tự động khớp Python.
- Thiết lập GitHub Actions và GitHub Pages; quản lý repo và ghi nhận sử dụng AI (`prompts/PROMPTS.md`).
- Chuẩn bị phương án dự phòng: ảnh chụp và video demo, phòng khi mất mạng.
- **Trình bày:** slide 7 (demo trực tiếp dashboard); trả lời câu hỏi về sản phẩm và triển khai.

**Việc chung:** cả nhóm duyệt kết luận, kịch bản thuyết trình và phần hỏi đáp.
