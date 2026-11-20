// Kiểm tra dashboard/regress.js tái tạo đúng kết quả Python (linearmodels) trong dashboard/econ.js.
// Chạy: node scripts/test_regress.js  (thoát mã 1 nếu lệch quá ngưỡng)
const fs = require('fs'), path = require('path'), vm = require('vm');
const dash = path.join(__dirname, '..', 'dashboard');
const ctx = { window: {} };
vm.createContext(ctx);
for (const f of ['panel.js', 'econ.js', 'regress.js']) vm.runInContext(fs.readFileSync(path.join(dash, f), 'utf8'), ctx);
const { PANEL, ECON, Regress } = ctx.window;

const rel = (a, b) => Math.abs(a - b) / Math.max(Math.abs(b), 1e-12);
let worst = 0, fails = 0;
for (const m of ECON.models) {
  const spec = PANEL.presets.find(p => p.id === m.id);
  const covs = [[m.cov, 'p'], ...(m.alt_cov ? [[m.alt_cov, 'p_alt']] : [])];
  for (const [cov, pkey] of covs) {
    const r = Regress.fit(PANEL, spec, cov);
    const line = [`${m.id.padEnd(10)} ${cov.padEnd(9)} n=${r.n}/${m.n}`];
    if (r.n !== m.n) { fails++; line.push('N LỆCH'); }
    m.coefs.forEach(c => {
      const j = r.coefs.find(x => x.var === c.var);
      const eb = rel(j.b, c.b), ep = Math.abs(j.p - c[pkey]);
      const es = cov === m.cov ? rel(j.se, c.se) : 0;
      worst = Math.max(worst, eb, es);
      if (eb > 1e-6 || es > 1e-4 || ep > 1e-3) { fails++; line.push(`\n   ${c.var}: b ${j.b.toPrecision(6)} vs ${c.b.toPrecision(6)}, se ${j.se.toPrecision(6)} vs ${c.se.toPrecision(6)}, p ${j.p.toFixed(4)} vs ${c[pkey].toFixed(4)}`); }
    });
    if (cov === m.cov && Math.abs(r.r2_within - m.r2_within) > 1e-6) { fails++; line.push(` R2w ${r.r2_within.toFixed(5)} vs ${m.r2_within.toFixed(5)}`); }
    console.log(line.join(' '));
  }
}
console.log(`\nsai lệch tương đối lớn nhất (hệ số, SE): ${worst.toExponential(2)}; số lỗi: ${fails}`);
process.exit(fails ? 1 : 0);
