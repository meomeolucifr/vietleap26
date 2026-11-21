# Rate Cut Lab: pitch script (Team 1 · 4MAN WARRIOR)

Lời nói bằng tiếng Anh. Ghi chú sân khấu và thao tác trong ngoặc vuông, bằng tiếng Việt.
Tổng thời lượng khoảng 7 phút: slide 1–6 khoảng 3,5 phút, demo khoảng 2,5 phút, slide 8–9 khoảng 1 phút.
Mọi số liệu khớp dashboard bản mới nhất (VCB, năm nền 2025, chi phí vốn giữ nguyên).

Người nói theo ngành: **NH** = Ngân hàng · **TH** = Thuế · **TK** = Toán thống kê · **KHMT** = Khoa học máy tính.

Chuẩn bị trước khi lên:
- Mở sẵn https://w-nhannt.github.io/vietleap26/#en, ngân hàng VCB, năm 2025, kịch bản Base, mục tiêu 90%, mức 25 bp.
- Phóng to trình duyệt 110–125% cho dễ nhìn trên máy chiếu.
- Mở sẵn video dự phòng.

---

## Slide 1: Rate Cut Lab (NH, khoảng 20 giây)

> Good afternoon. We are Team 1, 4MAN WARRIOR: a team from banking, tax, statistics and computer science.
>
> Our product is **Rate Cut Lab**, and it answers one question every bank's leadership faces: **how far can a Vietnamese bank cut its lending rates, safely?**

## Slide 2: Every rate cut has a cost (NH, khoảng 45 giây)

> Let's start with a borrower. Imagine you run a small business with a one-billion-dong loan. Your bank cuts the lending rate by 0.25 percentage points, that's 25 basis points. That's about **2.5 million dong a year** back in your business.
>
> [Chỉ vào 01] That's point one: **borrowers benefit**.
>
> [Chỉ vào 02] But that money doesn't appear from nowhere. Every dong the borrower saves is a dong of interest income the bank no longer earns. Profit falls, and so does the capital the bank builds from profit. So **the bank faces a trade-off**.
>
> [Chỉ vào 03] Which brings us to **the decision question**: how far can a bank cut lending rates without compromising its financial safety?

## Slide 3: One decision, four outcomes (NH, khoảng 40 giây)

> We turn "safe" into numbers. One decision, four outcomes.
>
> **One**, the benefit: how much borrowers save each year.
>
> Then three guardrails:
> - **Two**, profit retention: keep at least **90%** of last year's after-tax profit. That target comes from the bank's own ALCO proposal. It's a management choice, not a law, so our tool also lets you pick 85 or 95.
> - **Three**, capital adequacy: CAR must stay **at or above 8%**, the State Bank's minimum.
> - **Four**, provision coverage: this year's operating profit must still cover loan-loss provisions **at least once**. Below that, the bank makes a loss.

## Slide 4: Two layers, one decision (TK, khoảng 45 giây)

> How do we compute this? Two layers, built on **25 listed Vietnamese banks over 10 years, 250 bank-year observations** of audited statements.
>
> [Chỉ vào 01] **Layer one is an accounting simulator.** It works on one bank's own financial statements. A key detail: not every loan gets the new rate at once. We use the **repricing schedule** in the notes to the statements: a loan that reprices next month gets the cut for eleven and a half months, a loan that reprices in a year gets almost nothing. And we take the **worst case**: the bank does not lower deposit rates, so it bears the whole cut.
>
> [Chỉ vào 02] **Layer two is econometric validation.** Panel regressions on the 25 banks, 2020 to 2025, test the simulator's assumptions. Two findings matter:
> - In reality profit and capital fall *less* than our formulas assume, so our numbers are a **conservative upper bound** on the damage.
> - When GDP growth slows by one point, provisions rise by about **4 basis points of loans**. That drives our adverse economic scenario.

## Slide 5: What does a 25 bp cut really mean? (TH, khoảng 40 giây)

> Let's apply it to Vietcombank, 2025 base year, base scenario.
>
> - Borrowers save **2,666 billion dong a year**.
> - After-tax profit falls **6.1%**, from 35,198 to 33,065 billion. The bank keeps 94%, above the 90% target.
> - CAR moves from **11.56% to 11.45%**, far above 8%.
> - Provision coverage goes from **14.8 to 14.0 times**.
>
> Who pays the 2,666 billion? Shareholders, about **2,133 billion** in lower profit, and the state budget, about **533 billion** in lower corporate income tax.
>
> **The result: all three financial guardrails remain satisfied.** And these numbers reproduce the bank's own ALCO proposal exactly.

## Slide 6: The limits (TH, khoảng 40 giây)

> So 25 is safe. But how far can Vietcombank go?
>
> - **41 basis points**: the maximum cut that keeps 90% of profit in the base scenario. That's exactly the figure in the ALCO proposal.
> - **13 basis points**: the maximum if the economy turns like 2019–2021. Provisions rise, and the safe limit shrinks to a third. This is our **recommended safe cut**: it passes all three guardrails in every scenario.
> - The target matters too: aim to keep 95% of profit and the limit is **20**; accept 85% and it's **61**.
>
> Same bank, same data. **The assumptions, the economy and the target change the decision**, and that's exactly what the ALCO needs to see before it decides.

## Slide 7: Showing live dashboard (KHMT, khoảng 2 phút 30 giây)

[Chuyển sang trình duyệt. Dashboard đang ở VCB, 2025, 25 bp, Base, 90%.]

**Bước 1: đọc kết luận ở đầu trang (khoảng 25 giây)**

> This is Rate Cut Lab, live. The title is the conclusion: **"VCB can cut lending rates by up to 41 bp and keep 90% of profit."** Right under it, the **recommended safe cut: 13 bp**, safe in all three economic scenarios.
>
> [Chỉ lần lượt 4 thẻ] The four outcomes from our slides, at 25 bp: 2,666 billion saved; profit −6.1%, target met; coverage 14 times; CAR 11.45%.
>
> [Bấm "How it's computed" trên thẻ Profit after tax, rồi đóng] Every number opens to its formula with the real figures, traced back to the financial statements.

**Bước 2: kéo mức giảm (khoảng 35 giây)**

> [Bấm nút 50 trên khung điều chỉnh] At 50 basis points, profit falls about 12%. The badge turns red: **below the 90% target**.
>
> [Cuộn xuống biểu đồ "How far can rates be cut before missing the profit target?"] This chart shows why. Every 10 basis points costs Vietcombank about **2.4% of profit**. The green zone is everything that still meets the target, and it ends at **41**. The dashed lines are the other two economic scenarios.
>
> [Bấm lại nút 25]

**Bước 3: thử kịch bản xấu (khoảng 35 giây)**

> Now the question every risk committee asks: what if the economy turns?
>
> [Bấm "Adverse" ở mục Macro scenario] Adverse scenario: provisions rise like they did after 2019. At the same 25 basis points, profit now falls **12.8%**. We keep only 87%, **below the target**. The title updates: in this scenario the maximum is **13 basis points**.
>
> [Bấm "Base" để trở lại] That's why we recommend 13: it holds whatever happens. 25 holds only if the economy holds.

**Bước 4: so sánh 25 ngân hàng (khoảng 20 giây)**

> [Cuộn tới biểu đồ "Which banks lose the most profit?"] The same tool runs for every bank. At 25 basis points, **19 of 25 banks** keep 90% of profit. The red bars are those that don't. They aren't the smallest banks, they're the ones with **thin profit margins**: even BIDV misses.

**Bước 5: kết quả để mang vào phòng họp (khoảng 20 giây)**

> [Cuộn lên đầu trang, bấm "Summary for ALCO"] And this is what the CFO takes into the meeting: a one-page summary with the proposal, the benefit, who pays, all three guardrails in every scenario, and the key risks. One click to copy.
>
> [Đóng bản tóm tắt. Nếu còn thời gian, mở tab "Method & data" 10 giây] Behind it, the Method tab shows every variable, its source line in the statements, and a regression lab where you can test your own model, with a VIF check for multicollinearity.

[Quay lại slide]

## Slide 8: From insight to action (NH, khoảng 35 giây)

> So, from insight to action, in three steps:
> - **Select** the bank and the base year.
> - **Stress-test** the cut, the profit target and the economy.
> - **Decide** on a bank-specific limit, knowing exactly who bears the cost.
>
> Why it matters: at a 25 basis-point cut, **19 of 25 banks** keep 90% of their profits; six don't. A one-size-fits-all call to cut rates puts disproportionate pressure on banks with thin margins. Each bank needs its own number.

## Slide 9: Better data, safer decisions (NH hoặc cả nhóm, khoảng 20 giây)

> Our recommendation for Vietcombank: **cut 13 basis points now**, safe whatever the economy does. Go to 25 only if the economy holds, and never beyond 41.
>
> Rate Cut Lab turns banking data into actionable lending-rate decisions. **Better data. Safer decisions.** Thank you.

---

## Hỏi đáp: chuẩn bị sẵn (mỗi câu trả lời một câu)

| Câu hỏi | Người trả lời | Trả lời |
|---|---|---|
| Why assume deposit rates don't fall? | NH | We can't prove a single bank's cut causes lower funding costs, so we take the worst case, the same as the bank's own ALCO proposal; the real loss can only be smaller. |
| Is this a forecast? | TK | No. It's the extra effect over the next 12 months versus the base year, under three economic scenarios, so no forecasting is needed. |
| Why 90%? | NH | It's the bank's own target from the ALCO proposal, a management choice, not a regulation, and the tool lets you switch to 85 or 95. |
| Why only 2020–2025 for the regressions? | TK | That's when every bank reports CAR under the same rule, Circular 41, so all models measure it the same way. |
| How do you know the data is right? | TK | Accounting identities are checked on all 250 bank-years; computed CAR matches reported CAR in 95 of 105 cases, and the rest are source errors we corrected. |
| Who pays? | TH | At 25 bp for Vietcombank: shareholders about 2,133 billion and the state budget about 533 billion in tax. |
| Why did BIDV fail but not Vietcombank? | NH | Sensitivity follows profitability, not size: BIDV's thinner margin means each basis point costs a bigger share of its profit. |
| Can it be updated? | KHMT | Yes. Drop in new statements and push; the pipeline re-runs, re-checks the data and redeploys automatically. |
| Multicollinearity? | TK | The regression lab shows a VIF for every regressor and warns above 10; ROA, ROE and equity/assets together trigger it, as expected. |

## Tóm tắt tiếng Việt (slide cuối hoặc nói ngắn)

Giảm lãi 25 bp giúp người vay của Vietcombank tiết kiệm 2.666 tỷ đồng/năm. Chi phí do cổ đông (khoảng 2.133 tỷ) và ngân sách (khoảng 533 tỷ) gánh. Rate Cut Lab kiểm tra ba ngưỡng an toàn: giữ 90% lợi nhuận, CAR ≥ 8%, khả năng trang trải dự phòng ≥ 1 lần. Kết quả:
- Ở kịch bản cơ sở, VCB giảm được tối đa 41 bp, khớp đề xuất ALCO.
- Nếu kinh tế xấu đi, giới hạn còn 13 bp. Đây là mức an toàn khuyến nghị.
- 19/25 ngân hàng chịu được mức giảm 25 bp; ngân hàng có lợi nhuận mỏng chịu áp lực lớn nhất.

Mô hình dùng dữ liệu BCTC đã kiểm toán của 25 ngân hàng niêm yết giai đoạn 2016–2025, giả định trường hợp xấu nhất cho chi phí vốn, và được kiểm chứng bằng hồi quy panel.
