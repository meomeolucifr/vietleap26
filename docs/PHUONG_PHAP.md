# Phương pháp: mô phỏng giảm lãi suất cho vay và các chỉ số an toàn ngân hàng

Tài liệu cho nhóm và hội đồng giám khảo. Số liệu cập nhật theo lần chạy `scripts/run_pipeline.py` ngày 20/11/2026; khi dữ liệu đổi, các con số trên dashboard tự cập nhật, còn số trong tài liệu này cần sửa tay.

## 1. Câu hỏi quyết định

Người dùng là ALCO/CFO của một ngân hàng thương mại. Câu hỏi: **giảm lãi suất cho vay s điểm cơ bản (10 bp = 0,1 điểm %) thì ngân hàng có còn đảm bảo các chỉ số an toàn không?** Bốn chỉ số trả lời câu hỏi đó:

| Chỉ số | Ngưỡng dùng trên dashboard | Vì sao quan trọng |
|---|---|---|
| Lợi nhuận sau thuế (LNST) giữ lại so với năm nền | Mục tiêu do ALCO đặt, mặc định 90% | Nguồn bổ sung vốn và cổ tức |
| Tỷ lệ an toàn vốn (CAR) | Tối thiểu 8% (Thông tư 41/2016/TT-NHNN) | Ràng buộc pháp lý |
| Khả năng trang trải dự phòng = LN trước dự phòng / chi phí dự phòng | ≥ 2 lần: dày; 1–2: mỏng; < 1: lỗ trước thuế | Đệm hấp thụ rủi ro tín dụng |
| Tiền người vay tiết kiệm | — | Lợi ích của chương trình |

Kết quả chính của dashboard là **mức giảm tối đa** vẫn đạt mục tiêu LNST, kèm CAR và trang trải dự phòng ở mức đó.

## 2. Mẫu nghiên cứu

- **25 ngân hàng thương mại** có cổ phiếu niêm yết hoặc đăng ký giao dịch (22 HOSE, 1 HNX, 2 UPCoM) và đủ báo cáo tài chính hợp nhất **10 năm 2016–2025** (250 quan sát ngân hàng-năm).
- Loại: Agribank, BaoViet Bank (chưa niêm yết); ABBank (thiếu năm 2016); Bac A Bank, PVcomBank (chưa có file dữ liệu).
- Danh sách, sàn giao dịch (tra từ FiinX) và lý do loại nằm ở [Data/sample/banks.csv](../Data/sample/banks.csv). Sửa file này để đổi mẫu; toàn bộ pipeline đọc từ đây.

## 3. Mô hình đề xuất: hai tầng

**Tầng 1, công thức kế toán.** Tác động của mức giảm s được tính trực tiếp trên báo cáo tài chính năm nền, không qua hồi quy. Lý do: ALCO cần con số cho chính ngân hàng mình và truy được về từng dòng báo cáo.

```
E    = Dư nợ cho vay × α × (số tháng hiệu lực / 12)        dư nợ chịu lãi mới trong 12 tháng
T    = E × s / 10.000                                       người vay tiết kiệm = thu nhập lãi mất
ΔLNTT = T × (1 − φ) + ΔDP                                   φ: phần bù từ trả lãi tiền gửi thấp hơn
ΔLNST = ΔLNTT × (1 − thuế)
CAR mới = CAR nền − ΔLNST × k / RWA                         k: tỷ lệ lợi nhuận giữ lại; RWA giữ nguyên
Trang trải DP = (LN trước DP − T × (1 − φ)) / (Chi phí DP nền + ΔDP)
Mức giảm tối đa = [(1 − mục tiêu) × LNST nền − ΔDP × (1 − thuế)] / [E × (1 − φ) × (1 − thuế)] × 10.000
```

**Tầng 2, kinh tế lượng.** Tầng 1 cần một số tham số mà báo cáo tài chính của một năm không cho biết. Tầng 2 ước lượng chúng bằng hồi quy dữ liệu bảng (panel) trên 25 ngân hàng × 10 năm, thư viện `linearmodels` (PanelOLS). Mỗi mô hình gắn với một mắt xích:

| Mắt xích | Câu hỏi | Mô hình | Kết quả | Ý nghĩa cho chỉ số an toàn |
|---|---|---|---|---|
| Phần bù chi phí vốn φ | Khi một ngân hàng tự giảm lợi suất, chi phí vốn của nó giảm bao nhiêu? | `pass_bank`: Δchi phí vốn ~ Δlợi suất + FE ngân hàng + FE năm, SE cụm | **0,39** (p < 0,001; n = 193). Nếu cả thị trường cùng đổi (`pass_mkt`, không FE năm): 0,98 | φ mặc định = 39%. Thiệt hại LNST, CAR và đệm dự phòng đều phụ thuộc trực tiếp vào φ |
| NIM mất → ROA mất | Mô phỏng giả định 1 bp NIM mất = 0,8 bp ROA mất. Thực tế? | `roa_det`: ROA ~ NIM + CIR + nợ xấu + VCSH/TTS + quy mô + cho vay/TTS + FE ngân hàng + FE năm | **0,30** (p < 0,001; n = 186) | Ngân hàng bù được một phần; số LNST giảm trên dashboard là **cận trên** |
| RWA có tăng không? | Ngân hàng giảm lãi thì tín dụng tăng nhanh hơn, làm RWA tăng và CAR giảm? | `loan_resp`: tăng trưởng dư nợ ~ Δlợi suất + FE ngân hàng + FE năm | 0,01 (**p = 0,99**; n = 192) | Không có bằng chứng; phù hợp cơ chế hạn mức tín dụng (room) của NHNN. Giữ RWA không đổi là hợp lý |
| Lợi nhuận → CAR | Lợi nhuận giảm thì CAR giảm bao nhiêu? Công thức mô phỏng có đúng không? | `car_resp`: ΔCAR ~ ROA + tăng trưởng dư nợ + FE ngân hàng + FE năm, SE cụm; CAR = vốn tự có / RWA (chỉ năm có đủ hai số) | ROA +1 điểm → CAR **+1,32** điểm (p = 0,012; n = 74; CI 0,30–2,35). Công thức ngầm định 1 / (RWA/tổng tài sản) = 1,21 | Nằm trong khoảng tin cậy: cách dashboard tính CAR khớp dữ liệu. Không trộn CAR công bố vì đổi phương pháp theo Thông tư 41 từ 2020 |
| Lãi thấp → nợ xấu giảm? | Giảm lãi có giúp người vay trả nợ tốt hơn, nợ xấu năm sau giảm? | `npl_resp`: Δ nợ xấu năm sau ~ Δ lợi suất + FE ngân hàng + FE năm | Không có ý nghĩa (p = 0,81) | Không cộng thêm lợi ích này; mô phỏng giữ thận trọng |
| Kinh tế xấu đi → dự phòng tăng | GDP chậm lại thì chi phí dự phòng tăng bao nhiêu? | `llp_macro`: chi phí DP/dư nợ BQ ~ GDP + CPI + tăng trưởng dư nợ + nợ xấu năm trước + quy mô + FE ngân hàng, SE Driscoll-Kraay | GDP −1 điểm % → DP **+2,2 bp** dư nợ (p < 0,001; nhưng p = 0,37 với SE cụm) | Tạo kịch bản Bất lợi (như 2019→2021, GDP −4,4 điểm %: DP +9,7 bp) và Thuận lợi (−2,0 bp) |
| Vĩ mô → NIM | Điều kiện vĩ mô có làm đổi NIM? | `nim_macro`: NIM ~ LS huy động + GDP + CPI + tăng trưởng dư nợ + nợ xấu + quy mô + FE ngân hàng, SE Driscoll-Kraay | Không hệ số vĩ mô nào có ý nghĩa ở 5% | Không thêm kênh này; tránh tính trùng với kênh giảm lãi |

Ví dụ VCB, năm nền 2025, giảm 25 bp, φ = 39%, kịch bản Cơ sở: người vay tiết kiệm khoảng 4.184 tỷ đồng, LNST giảm khoảng 5,8%, CAR 11,56% → 11,46%, trang trải dự phòng 14,8 → 14,0 lần. Xem số chính xác trên dashboard.

Trên dashboard (tab Phương pháp), bốn mô hình chính, mỗi mô hình gắn với một chỉ số an toàn (`pass_bank`, `roa_det`, `car_resp`, `llp_macro`), được vẽ thành biểu đồ added-variable. Mỗi chấm là một ngân hàng-năm sau khi đã loại hiệu ứng cố định và các biến kiểm soát; độ dốc đường hồi quy bằng đúng hệ số, kèm đường giả định mà mô phỏng đang dùng. Người xem có thể bật/tắt hiệu ứng năm, đổi mức bỏ đuôi và cách tính sai số; hồi quy chạy lại ngay trên trình duyệt (`dashboard/regress.js`, khớp linearmodels đến khoảng 1e-8, kiểm tra bằng `node scripts/test_regress.js`). Phần "Tự chạy hồi quy" cho chọn biến tuỳ ý.

### Vì sao dùng các lựa chọn này

- **Hiệu ứng cố định năm (FE năm)** hấp thụ mọi thay đổi chung của cả hệ thống trong năm (lãi suất điều hành, room tín dụng, chu kỳ). Hệ số còn lại đo phản ứng riêng của một ngân hàng, đúng với tình huống ALCO tự quyết định giảm lãi. Khác biệt 0,98 → 0,39 cho thấy lựa chọn này quan trọng.
- **Biến vĩ mô** giống nhau cho mọi ngân hàng trong năm, nên mô hình có biến vĩ mô không thể dùng FE năm và chỉ có khoảng 10 điểm thời gian. Dùng sai số Driscoll-Kraay (chịu được tương quan giữa các ngân hàng trong cùng năm) và báo kèm p theo sai số cụm để thấy độ bất định.
- **Bỏ 1% đuôi mỗi phía** của các biến để giảm ảnh hưởng của vài ngân hàng-năm bất thường (ví dụ ngân hàng lãi rất mỏng).
- Kiểm định Hausman FE/RE được báo trên dashboard; với hai mô hình vĩ mô, thống kê âm nên không dùng được, và FE được giữ vì luôn nhất quán.

### Hạn chế

- Kết quả là tác động tăng thêm trong 12 tháng so với năm nền, không phải dự báo.
- Tác động là tuyến tính theo mức giảm (VCB 2025: mỗi 10 bp mất khoảng 2,3% LNST). Thực tế có thể cong: phần bù chi phí vốn có thể đổi theo mức giảm, lãi thấp hơn giúp người vay trả nợ tốt hơn và dự phòng giảm. Dữ liệu năm không đủ để ước lượng độ cong; dashboard thay vào đó vẽ dải bất định theo khoảng tin cậy 95% của φ (26–52%), cho VCB 2025 mức giảm tối đa trong khoảng 35–55 bp.
- Thiếu bảng kỳ định lại lãi suất, nên thời điểm áp lãi mới là giả định (mặc định 12 tháng, cận trên). Vì vậy số tiết kiệm của VCB ở 25 bp (khoảng 4.200 tỷ) cao hơn ước tính 2.666 tỷ của đề xuất ALCO.
- Các hệ số là tương quan có điều kiện, không phải nhân quả. φ là quan hệ lịch sử, không phải cam kết của người gửi tiền.
- Hệ số GDP trong `llp_macro` nhạy với cách tính sai số; giai đoạn 2020–2021 có chính sách cơ cấu nợ (Thông tư 01/2020) có thể làm dự phòng phản ứng chậm.

## 4. Biến, công thức và nguồn dữ liệu

Số liệu ngân hàng: báo cáo tài chính hợp nhất năm đã kiểm toán. Lấy miễn phí trên trang quan hệ nhà đầu tư của từng ngân hàng hoặc mục công bố thông tin của HOSE/HNX; bản chuẩn hoá có trên FiinPro-X (nhóm dùng file xuất ngày 13/10/2026, thư mục `Data/`). Đơn vị: tỷ đồng.

### 4.1 Số liệu gốc

| Biến | Ký hiệu | Dòng trong báo cáo tài chính |
|---|---|---|
| Cho vay khách hàng (gộp, trước dự phòng) | `loans` | Bảng cân đối kế toán · "Cho vay khách hàng" |
| Thu nhập lãi | `ii` | Kết quả kinh doanh · "Thu nhập lãi và các khoản thu nhập tương tự" |
| Chi phí lãi | `ie` | Kết quả kinh doanh · "Chi phí lãi và các chi phí tương tự" |
| Thu nhập lãi thuần | `nii` | Kết quả kinh doanh · "Thu nhập lãi thuần" |
| Tổng thu nhập hoạt động; chi phí hoạt động | `toi`, `opex` | Kết quả kinh doanh |
| LN trước chi phí dự phòng | `ppop` | Kết quả kinh doanh · "Lợi nhuận thuần từ hoạt động kinh doanh trước chi phí dự phòng rủi ro tín dụng" |
| Chi phí dự phòng rủi ro tín dụng | `prov` | Kết quả kinh doanh |
| LN trước thuế; thuế TNDN; LN sau thuế | `pbt`, `tax`, `pat` | Kết quả kinh doanh |
| Tổng tài sản; nợ phải trả; vốn chủ sở hữu; tiền gửi khách hàng | `ta`, `liab`, `equity`, `deposits` | Bảng cân đối kế toán |
| Vốn tự có; tổng tài sản có rủi ro; CAR | `vtc`, `rwa`, `car` | Thuyết minh "Tỷ lệ an toàn vốn"; báo cáo công bố thông tin về rủi ro (Thông tư 41) trên website ngân hàng |
| Dư nợ nhóm 1–5 | `N1..N5` | Thuyết minh "Phân tích chất lượng nợ cho vay" |

### 4.2 Biến tính toán

"Bình quân" = (đầu kỳ + cuối kỳ) / 2.

| Biến | Ký hiệu | Công thức |
|---|---|---|
| Lợi suất tài sản | `yield` | ii / tổng tài sản bình quân |
| Chi phí vốn | `cost` | ie / nợ phải trả bình quân |
| NIM | `nim` | nii / tổng tài sản bình quân |
| ROA | `roa` | pat / tổng tài sản bình quân |
| Chi phí / thu nhập | `cir` | opex / toi |
| Tỷ lệ nợ xấu | `npl` | (N3 + N4 + N5) / (N1 + … + N5) |
| Tỷ lệ chi phí dự phòng | `llp` | prov / dư nợ bình quân |
| Tăng trưởng dư nợ | `loang` | loans<sub>t</sub> / loans<sub>t−1</sub> − 1 |
| Vốn chủ / tài sản; quy mô | `cap`, `size` | equity / ta; ln(ta) |
| Cho vay / tài sản | `loans_ta` | loans / ta |
| Trang trải dự phòng | `cov` | ppop / prov |
| CAR | `car` | vtc / rwa (đối chiếu CAR công bố; lệch quá 0,3 điểm % thì dùng CAR công bố và suy ra RWA) |
| Thay đổi so với năm trước | `Δx` | x<sub>t</sub> − x<sub>t−1</sub> |

### 4.3 Vĩ mô

File [Data/macro/macro_vn.csv](../Data/macro/macro_vn.csv), đơn vị %/năm, lấy qua FiinX (nguồn gốc GSO và NHNN).

| Biến | Ký hiệu | Định nghĩa | Nguồn gốc, lấy thủ công ở đâu |
|---|---|---|---|
| Tăng trưởng GDP thực | `gdp_growth` | Giá so sánh, so với năm trước | Cục Thống kê (nso.gov.vn), thông cáo kinh tế – xã hội quý IV |
| Lạm phát CPI bình quân | `cpi_avg` | Bình quân 12 tháng của CPI so cùng kỳ | Cục Thống kê, cùng thông cáo (công bố sẵn số bình quân năm) |
| Lãi suất huy động trên 12 tháng | `deposit_rate_12m` | Trung điểm khoảng lãi suất NHNN công bố, tháng 12 | Ngân hàng Nhà nước (sbv.gov.vn), thống kê lãi suất |
| Tăng trưởng tín dụng toàn hệ thống | `credit_growth` | Dư nợ tháng 12 so cùng kỳ | Ngân hàng Nhà nước, thống kê tiền tệ |

## 5. Tái lập kết quả

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py --xlsx     # dữ liệu -> bảng Excel -> dashboard/*.js -> kiểm tra
python -m http.server 8000 -d dashboard
```

Đặc tả mô hình nằm trong danh sách `MODELS` của [scripts/econometrics.py](../scripts/econometrics.py); câu kết luận trên dashboard được sinh từ kết quả hồi quy.
