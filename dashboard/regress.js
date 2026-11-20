// Hồi quy panel hiệu ứng cố định trên trình duyệt, tái tạo PanelOLS của linearmodels (scripts/econometrics.py):
// cùng cách bỏ đuôi, khử hiệu ứng cố định, sai số chuẩn cụm theo ngân hàng / Driscoll-Kraay / robust,
// cùng hệ số điều chỉnh bậc tự do n / (n − d − k) và phân phối t. scripts/test_regress.js đối chiếu với econ.js.
(function (root) {
  'use strict';

  // phân vị kiểu pandas (nội suy tuyến tính)
  function quantile(sorted, q) {
    const pos = (sorted.length - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
  }

  // trung bình theo nhóm rồi trừ đi; trả về true nếu có thay đổi đáng kể
  function demeanBy(v, g) {
    const sum = new Map(), cnt = new Map();
    g.forEach((k, i) => { sum.set(k, (sum.get(k) || 0) + v[i]); cnt.set(k, (cnt.get(k) || 0) + 1); });
    let maxd = 0;
    for (let i = 0; i < v.length; i++) { const d = sum.get(g[i]) / cnt.get(g[i]); v[i] -= d; maxd = Math.max(maxd, Math.abs(d)); }
    return maxd;
  }
  // khử hiệu ứng cố định: một chiều thì trừ trung bình nhóm; hai chiều (bảng không cân) thì lặp xen kẽ đến hội tụ
  function within(v, ent, tim, useE, useT) {
    v = v.slice();
    if (useE && useT) { for (let it = 0; it < 5000; it++) { const a = demeanBy(v, ent), b = demeanBy(v, tim); if (Math.max(a, b) < 1e-15) break; } }
    else if (useE) demeanBy(v, ent);
    else if (useT) demeanBy(v, tim);
    else { const m = v.reduce((a, b) => a + b, 0) / v.length; for (let i = 0; i < v.length; i++) v[i] -= m; }
    return v;
  }

  function inv(A) {
    const n = A.length, M = A.map((r, i) => [...r, ...Array.from({ length: n }, (_, j) => +(i === j))]);
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      [M[c], M[p]] = [M[p], M[c]];
      const d = M[c][c]; if (Math.abs(d) < 1e-300) throw new Error('singular');
      for (let j = 0; j < 2 * n; j++) M[c][j] /= d;
      for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c]; if (f) for (let j = 0; j < 2 * n; j++) M[r][j] -= f * M[c][j]; }
    }
    return M.map(r => r.slice(n));
  }
  const mul = (A, B) => A.map(r => B[0].map((_, j) => r.reduce((s, v, k) => s + v * B[k][j], 0)));
  const outerAdd = (S, z, w = 1) => { for (let i = 0; i < z.length; i++) for (let j = 0; j < z.length; j++) S[i][j] += w * z[i] * z[j]; };
  const crossAdd = (S, a, b, w) => { for (let i = 0; i < a.length; i++) for (let j = 0; j < a.length; j++) S[i][j] += w * (a[i] * b[j] + b[i] * a[j]); };

  // phân phối t: hàm beta không đầy đủ chuẩn hoá (Numerical Recipes, phân số liên tục)
  function lgamma(x) {
    const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    let y = x, t = x + 5.5; t -= (x + 0.5) * Math.log(t); let s = 1.000000000190015;
    for (const v of c) s += v / ++y;
    return -t + Math.log(2.5066282746310005 * s / x);
  }
  function betacf(a, b, x) {
    let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < 1e-300) d = 1e-300; d = 1 / d; let h = d;
    for (let m = 1; m <= 300; m++) {
      const m2 = 2 * m; let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < 1e-300) d = 1e-300; c = 1 + aa / c; if (Math.abs(c) < 1e-300) c = 1e-300; d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < 1e-300) d = 1e-300; c = 1 + aa / c; if (Math.abs(c) < 1e-300) c = 1e-300; d = 1 / d;
      const del = d * c; h *= del; if (Math.abs(del - 1) < 3e-16) break;
    }
    return h;
  }
  function ibeta(x, a, b) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
  }
  const tTwoSided = (t, df) => ibeta(df / (df + t * t), df / 2, 0.5);           // P(|T| > |t|)
  function tCrit(df, alpha = 0.05) {                                             // nghịch đảo bằng chia đôi
    let lo = 0, hi = 50; for (let i = 0; i < 200; i++) { const m = (lo + hi) / 2; if (tTwoSided(m, df) > alpha) lo = m; else hi = m; } return (lo + hi) / 2;
  }

  /**
   * spec: { y, x: [...], entity, time, cov: 'clustered'|'kernel'|'robust', trim (%), pat_pos }
   * panel: window.PANEL từ econometrics.py
   */
  function fit(panel, spec, covType = spec.cov) {
    const ci = Object.fromEntries(panel.cols.map((c, i) => [c, i]));
    const cols = [spec.y, ...spec.x];
    if (!spec.x.length) throw new Error('no regressors');
    let rows = panel.rows.filter(r => (!spec.pat_pos || r[ci.pat_pos] === 1) && cols.every(c => r[ci[c]] != null && isFinite(r[ci[c]])));
    if (spec.trim) {   // như trim_tails của Python: phân vị tính trên mẫu sau khi bỏ dòng thiếu, giữ dòng nằm trong khoảng ở mọi biến
      const p = spec.trim / 100, bounds = cols.map(c => { const s = rows.map(r => r[ci[c]]).sort((a, b) => a - b); return [quantile(s, p), quantile(s, 1 - p)]; });
      rows = rows.filter(r => cols.every((c, j) => r[ci[c]] >= bounds[j][0] && r[ci[c]] <= bounds[j][1]));
    }
    const n = rows.length, k = spec.x.length;
    const ent = rows.map(r => r[ci.bank]), tim = rows.map(r => r[ci.year]);
    const nE = new Set(ent).size, nT = new Set(tim).size;
    const y = within(rows.map(r => r[ci[spec.y]]), ent, tim, spec.entity, spec.time);
    const X = spec.x.map(c => within(rows.map(r => r[ci[c]]), ent, tim, spec.entity, spec.time));   // theo cột
    const Xr = Array.from({ length: n }, (_, i) => X.map(col => col[i]));                          // theo dòng
    const XtX = X.map(a => X.map(b => a.reduce((s, v, i) => s + v * b[i], 0)));
    const Xty = X.map(a => a.reduce((s, v, i) => s + v * y[i], 0));
    const A = inv(XtX), beta = A.map(r => r.reduce((s, v, j) => s + v * Xty[j], 0));
    const e = y.map((v, i) => v - Xr[i].reduce((s, x, j) => s + x * beta[j], 0));

    // bậc tự do của hiệu ứng: PanelOLS (auto_df) bỏ qua khi chỉ có một hiệu ứng lồng trong cụm (FE ngân hàng + cụm ngân hàng)
    let d = (spec.entity ? nE - 1 : 0) + (spec.time ? nT - 1 : 0);
    if (covType === 'clustered' && spec.entity && !spec.time) d = 0;
    const kk = k + 1, dfRes = n - d - kk, scale = n / dfRes;   // k + 1: có hằng số

    const S = Array.from({ length: k }, () => Array(k).fill(0));
    const score = i => Xr[i].map(v => v * e[i]);
    if (covType === 'clustered' || covType === 'kernel') {
      const key = covType === 'clustered' ? ent : tim, sums = new Map();
      key.forEach((g, i) => { const z = sums.get(g) || Array(k).fill(0); score(i).forEach((v, j) => z[j] += v); sums.set(g, z); });
      if (covType === 'clustered') sums.forEach(z => outerAdd(S, z));
      else {
        const Z = [...sums.keys()].sort((a, b) => a - b).map(t => sums.get(t));
        const bw = Math.floor(4 * Math.pow(nT / 100, 2 / 9));
        Z.forEach(z => outerAdd(S, z));
        for (let j = 1; j <= bw; j++) { const w = 1 - j / (bw + 1); for (let t = j; t < Z.length; t++) crossAdd(S, Z[t], Z[t - j], w); }
      }
    } else for (let i = 0; i < n; i++) outerAdd(S, score(i));
    const V = mul(mul(A, S), A).map(r => r.map(v => v * scale));
    const tc = tCrit(dfRes);

    // R² within như linearmodels: khử trung bình theo ngân hàng, dùng hệ số đã ước lượng
    const yw = within(rows.map(r => r[ci[spec.y]]), ent, tim, true, false);
    const Xw = spec.x.map(c => within(rows.map(r => r[ci[c]]), ent, tim, true, false));
    let ssr = 0, sst = 0;
    yw.forEach((v, i) => { const r = v - Xw.reduce((s, col, j) => s + col[i] * beta[j], 0); ssr += r * r; sst += v * v; });

    return {
      n, banks: nE, years: [Math.min(...tim), Math.max(...tim)], r2_within: 1 - ssr / sst, df: dfRes,
      coefs: spec.x.map((c, j) => { const se = Math.sqrt(V[j][j]), t = beta[j] / se;
        return { var: c, b: beta[j], se, t, p: tTwoSided(t, dfRes), lo: beta[j] - tc * se, hi: beta[j] + tc * se }; }),
    };
  }

  root.Regress = { fit };
})(typeof window !== 'undefined' ? window : globalThis);
