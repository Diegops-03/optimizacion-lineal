from fractions import Fraction as F
import html

def fr(x, plus=False):
    """Format a Fraction (or int) for display."""
    x = F(x)
    s = ''
    if x.denominator == 1:
        s = str(abs(x.numerator))
    else:
        s = f"{abs(x.numerator)}/{x.denominator}"
    if x < 0:
        return '−' + s
    return ('+' + s) if plus else s

def fp(x):
    """fraction wrapped in parentheses if not a plain non-negative integer"""
    x = F(x)
    return fr(x) if (x.denominator == 1 and x >= 0) else f'({fr(x)})'

def frm(x):
    """Fraction with M support: x may be tuple (a, b) meaning a*M + b."""
    return fr(x)

def esc(s):
    return html.escape(str(s))

def table(headers, rows, cls='t', highlight=None, caption=None):
    """rows: list of lists of str (already html). highlight: dict (r,c)->class"""
    highlight = highlight or {}
    h = [f'<div class="tw"><table class="{cls}">']
    if caption:
        h.append(f'<caption>{caption}</caption>')
    h.append('<thead><tr>' + ''.join(f'<th>{x}</th>' for x in headers) + '</tr></thead><tbody>')
    for i, r in enumerate(rows):
        cells = []
        for j, x in enumerate(r):
            c = highlight.get((i, j))
            tag = 'th' if j == 0 else 'td'
            cells.append(f'<{tag}{" class=%s" % chr(34)+c+chr(34) if c else ""}>{x}</{tag}>')
        h.append('<tr>' + ''.join(cells) + '</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)


class Tableau:
    """Max problem tableau. rows[0] is Z row (reduced costs z_j - c_j, rhs = z)."""
    def __init__(self, names, zrow, rows, basis):
        self.names = list(names)
        self.z = [F(v) for v in zrow]          # len n+1 (last = rhs)
        self.rows = [[F(v) for v in r] for r in rows]
        self.basis = list(basis)               # indices of basic var per row

    def copy(self):
        return Tableau(self.names, self.z, self.rows, self.basis)

    @property
    def n(self):
        return len(self.names)

    def html(self, pivot=None, ops=None, enter=None, leave=None, caption=None):
        headers = ['VB'] + [f'{nm}{" ↓" if enter == j else ""}' for j, nm in enumerate(self.names)] + ['RHS']
        if ops:
            headers.append('Operación')
        rows = []
        zr = ['Z'] + [fr(v) for v in self.z]
        if ops:
            zr.append(ops[0])
        rows.append(zr)
        for i, r in enumerate(self.rows):
            nm = self.names[self.basis[i]]
            if leave == i:
                nm += ' ←'
            rr = [nm] + [fr(v) for v in r]
            if ops:
                rr.append(ops[i + 1])
            rows.append(rr)
        hl = {}
        if pivot is not None:
            hl[(pivot[0] + 1, pivot[1] + 1)] = 'piv'
        return table(headers, rows, highlight=hl, caption=caption)

    def pivot(self, r, c):
        """Return (new tableau, ops list) using professor's notation: operations use ORIGINAL pivot row."""
        t = self.copy()
        p = self.rows[r][c]
        prow = [v / p for v in self.rows[r]]
        ops = [None] * (len(self.rows) + 1)
        # Z row
        k = self.z[c]
        t.z = [a - k * b for a, b in zip(self.z, prow)]
        ops[0] = opdesc('Z', k, p, r)
        for i, row in enumerate(self.rows):
            if i == r:
                t.rows[i] = prow
                ops[i + 1] = (f'F{r+1}·({fr(1/p)})' if p != 1 else f'F{r+1}·1')
            else:
                k = row[c]
                t.rows[i] = [a - k * b for a, b in zip(row, prow)]
                ops[i + 1] = opdesc(f'F{i+1}', k, p, r)
        t.basis[r] = c
        return t, ops

    def is_opt(self):
        return all(v >= 0 for v in self.z[:-1])

    def is_feas(self):
        return all(r[-1] >= 0 for r in self.rows)

    def values(self):
        x = [F(0)] * self.n
        for i, b in enumerate(self.basis):
            x[b] = self.rows[i][-1]
        return x


def opdesc(name, k, p, r):
    # new_row = row - (k/p) * (original pivot row Fp)
    if k == 0:
        return '—'
    m = k / p
    sign = '−' if m > 0 else '+'
    m = abs(m)
    mm = '' if m == 1 else fr(m) + '·'
    return f'{name} {sign} {mm}F{r+1}'


def primal_steps(t, maxit=10):
    """Run primal simplex from t; returns list of html strings and final tableau."""
    out = []
    it = 0
    while not t.is_opt() and it < maxit:
        c = min(range(t.n), key=lambda j: (t.z[j], j))
        ratios = [(r[-1] / r[c], i) for i, r in enumerate(t.rows) if r[c] > 0]
        if not ratios:
            out.append('<p>Problema no acotado.</p>')
            return out, t, 'unbounded'
        rmin = min(ratios)[1]
        rat_txt = ', '.join(f'{t.names[t.basis[i]]}: {fp(t.rows[i][-1])}/{fp(t.rows[i][c])} = {fr(t.rows[i][-1]/t.rows[i][c])}' for _, i in sorted(ratios, key=lambda x: x[1]))
        out.append(f'<p>Entra <b>{t.names[c]}</b> (costo reducido más negativo = {fr(t.z[c])}). Razones: {rat_txt}. Sale <b>{t.names[t.basis[rmin]]}</b>.</p>')
        t2, ops = t.pivot(rmin, c)
        out.append(t.html(pivot=(rmin, c), enter=c, leave=rmin))
        out.append(t2.html(ops=ops))
        t = t2
        it += 1
    return out, t, 'opt'


def dual_steps(t, maxit=10):
    out = []
    it = 0
    while not t.is_feas() and it < maxit:
        r = min(range(len(t.rows)), key=lambda i: (t.rows[i][-1], i))
        cand = [(abs(t.z[j] / t.rows[r][j]), j) for j in range(t.n) if t.rows[r][j] < 0]
        if not cand:
            out.append(f'<p>La fila de {t.names[t.basis[r]]} no tiene coeficientes negativos: el problema queda <b>infactible</b>.</p>')
            return out, t, 'infeasible'
        c = min(cand)[1]
        cand_txt = ', '.join(f'{t.names[j]}: |{fp(t.z[j])}/{fp(t.rows[r][j])}| = {fr(abs(t.z[j]/t.rows[r][j]))}' for _, j in sorted(cand, key=lambda x: x[1]))
        out.append(f'<p>Simplex dual: sale <b>{t.names[t.basis[r]]}</b> (RHS más negativo = {fr(t.rows[r][-1])}). Cocientes: {cand_txt}. Entra <b>{t.names[c]}</b>.</p>')
        t2, ops = t.pivot(r, c)
        out.append(t.html(pivot=(r, c), enter=c, leave=r))
        out.append(t2.html(ops=ops))
        t = t2
        it += 1
    return out, t, 'feas'


def build_initial(c, A, b, names=None):
    m, n = len(A), len(c)
    names = names or [f'x<sub>{j+1}</sub>' for j in range(n + m)]
    z = [-F(v) for v in c] + [F(0)] * m + [F(0)]
    rows = []
    for i in range(m):
        rows.append([F(v) for v in A[i]] + [F(1) if k == i else F(0) for k in range(m)] + [F(b[i])])
    return Tableau(names, z, rows, list(range(n, n + m)))


def solve_max(c, A, b):
    t = build_initial(c, A, b)
    steps, t, st = primal_steps(t, maxit=20)
    return t, st, steps


def lin(coefs, names, rhs=None, op=None):
    parts = []
    for k, nm in zip(coefs, names):
        k = F(k)
        if k == 0:
            continue
        s = ('' if abs(k) == 1 else fr(abs(k))) + nm
        if not parts:
            parts.append(('−' if k < 0 else '') + s)
        else:
            parts.append((' − ' if k < 0 else ' + ') + s)
    out = ''.join(parts) or '0'
    if op:
        out += f' {op} {fr(rhs)}'
    return out


def model_html(c, A, b, ops=None, sense='Max', names=None, integer=False):
    n = len(c)
    names = names or [f'x<sub>{j+1}</sub>' for j in range(n)]
    ops = ops or ['≤'] * len(A)
    lines = [f'{sense} Z = {lin(c, names)}', 's.a.']
    for i in range(len(A)):
        lines.append('&nbsp;&nbsp;' + lin(A[i], names, b[i], ops[i]))
    lines.append('&nbsp;&nbsp;' + ', '.join(names) + ' ≥ 0' + (', enteros' if integer else ''))
    return '<div class="model">' + '<br>'.join(lines) + '</div>'
