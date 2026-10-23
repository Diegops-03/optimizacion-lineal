import random
from fractions import Fraction as F
from core import *

def nice_lp(rng, m, n, maxden=12, tries=5000, want_all_dec_basic=False):
    for _ in range(tries):
        c = [rng.randint(1, 9) for _ in range(n)]
        A = [[rng.choice([0,1,1,2,2,3,3,4,5,6]) if rng.random()<0.15 else rng.randint(1, 6) for _ in range(n)] for _ in range(m)]
        if any(all(v == 0 for v in row) for row in A):
            continue
        if any(all(A[i][j] == 0 for i in range(m)) for j in range(n)):
            continue
        b = [rng.randint(4, 30) for _ in range(m)]
        t, st, steps = solve_max(c, A, b)
        if st != 'opt':
            continue
        vals = [r[-1] for r in t.rows]
        if any(v <= 0 for v in vals):
            continue
        nb = [j for j in range(t.n) if j not in t.basis]
        if any(t.z[j] == 0 for j in nb):
            continue
        dens = [x.denominator for r in t.rows for x in r] + [x.denominator for x in t.z]
        if max(dens) > maxden:
            continue
        dec_basic = sum(1 for bj in t.basis if bj < n)
        if dec_basic == 0:
            continue
        if want_all_dec_basic and dec_basic < min(n, m):
            continue
        if len(steps) < 4:  # at least 2 iterations
            continue
        return c, A, b, t
    raise RuntimeError('no lp')


def binv(t, n, m):
    return [[r[n + k] for k in range(m)] for r in t.rows]


def matvec(M, v):
    return [sum(F(a) * F(x) for a, x in zip(row, v)) for row in M]


def cB(t, c):
    cc = list(c) + [0] * (t.n - len(c))
    return [F(cc[bj]) for bj in t.basis]


def matrix_html(M, name='B⁻¹'):
    rows = ''.join('<tr>' + ''.join(f'<td>{fr(x)}</td>' for x in r) + '</tr>' for r in M)
    return f'<span class="mat"><span class="mlab">{name} =</span><table class="m">{rows}</table></span>'


def vec_html(v, name=''):
    rows = ''.join(f'<tr><td>{fr(x)}</td></tr>' for x in v)
    lab = f'<span class="mlab">{name}</span>' if name else ''
    return f'<span class="mat">{lab}<table class="m">{rows}</table></span>'


def enunciado_base(c, A, b, t):
    n, m = len(c), len(A)
    slack = ', '.join(t.names[n + k] for k in range(m))
    return (model_html(c, A, b) +
            f'<p>Holguras: {slack} (restricciones 1…{m}). Tabla óptima:</p>' + t.html())


# ---------- question pieces (each returns (question_html, solution_html)) ----------

def q_identify(c, A, b, t):
    n, m = len(c), len(A)
    Bi = binv(t, n, m)
    x = t.values()
    y = [t.z[n + k] for k in range(m)]
    q = 'Identifique B⁻¹, la solución óptima, Z* y los precios duales (precio sombra) de cada recurso.'
    s = (f'<p>B⁻¹ son las columnas de las holguras ({", ".join(t.names[n+k] for k in range(m))}) en la tabla óptima, fila por fila:</p>'
         + matrix_html(Bi) +
         '<p>Solución: ' + ', '.join(f'{t.names[j]} = {fr(x[j])}' for j in range(n)) + f'; Z* = <b>{fr(t.z[-1])}</b>.</p>'
         + '<p>Precios duales = fila Z bajo las holguras: ' + ', '.join(f'y<sub>{k+1}</sub> = {fr(y[k])}' for k in range(m))
         + '. Interpretación: una unidad más del recurso i aumenta Z en y<sub>i</sub> (mientras la base no cambie). Comprobación: '
         + ' + '.join(f'{fr(y[k])}·{b[k]}' for k in range(m)) + f' = {fr(sum(y[k]*b[k] for k in range(m)))} = Z*.</p>')
    return q, s


def q_change_b(c, A, b, t, newb, label=None):
    n, m = len(c), len(A)
    Bi = binv(t, n, m)
    xb = matvec(Bi, newb)
    cb = cB(t, c)
    z = sum(a * x for a, x in zip(cb, xb))
    chg = ', '.join(f'b<sub>{i+1}</sub> = {newb[i]}' for i in range(m) if newb[i] != b[i])
    q = label or f'Si {chg}, ¿cuál es la nueva solución óptima y el nuevo Z?'
    s = ('<p>x<sub>B</sub> = B⁻¹·b<sub>nuevo</sub>:</p><div class="eq">' + matrix_html(Bi) + ' · ' + vec_html(newb) + ' = ' + vec_html(xb) + '</div>'
         + '<p>(x<sub>B</sub> en el orden de la base: ' + ', '.join(t.names[bj] for bj in t.basis) + ')</p>')
    if all(v >= 0 for v in xb):
        s += ('<p>Todos ≥ 0 ⇒ la base sigue siendo óptima (cambian los valores). ' + ', '.join(f'{t.names[bj]} = {fr(v)}' for bj, v in zip(t.basis, xb))
              + f'; las demás = 0.</p><p>Z = c<sub>B</sub>·x<sub>B</sub> = ' + ' + '.join(f'{fr(a)}·{fr(v)}' for a, v in zip(cb, xb)) + f' = <b>{fr(z)}</b>.</p>')
        return q, s, None
    # infeasible -> dual simplex
    t2 = t.copy()
    for i in range(m):
        t2.rows[i][-1] = xb[i]
    t2.z[-1] = z
    s += '<p>Hay un valor negativo ⇒ la tabla queda <b>infactible</b> (pero sigue cumpliendo optimalidad). Se reemplaza el RHS y se aplica <b>simplex dual</b>:</p>'
    steps, tf, st = dual_steps(t2)
    s += ''.join(steps)
    if st == 'feas':
        x = tf.values()
        s += '<p><b>Nueva solución:</b> ' + ', '.join(f'{tf.names[j]} = {fr(x[j])}' for j in range(n)) + f'; Z = <b>{fr(tf.z[-1])}</b>.</p>'
    return q, s, tf


def q_range_b(c, A, b, t, i):
    n, m = len(c), len(A)
    Bi = binv(t, n, m)
    # x_B = Bi*b + delta*Bi[:,i] >= 0
    base = matvec(Bi, b)
    col = [Bi[r][i] for r in range(m)]
    lo, hi = None, None
    conds = []
    for r in range(m):
        a, d = base[r], col[r]
        conds.append(f'{fr(a)} {"+" if d >= 0 else "−"} {fr(abs(d))}·Δ ≥ 0')
        if d > 0:
            v = -a / d
            lo = v if lo is None or v > lo else lo
        elif d < 0:
            v = -a / d
            hi = v if hi is None or v < hi else hi
    lo_b = '−∞' if lo is None else fr(b[i] + lo)
    hi_b = '∞' if hi is None else fr(b[i] + hi)
    lo_d = '−∞' if lo is None else fr(lo)
    hi_d = '∞' if hi is None else fr(hi)
    q = f'Encuentre el rango de b<sub>{i+1}</sub> en que la base actual sigue siendo óptima.'
    s = (f'<p>b<sub>{i+1}</sub> → {b[i]} + Δ. Entonces x<sub>B</sub> = B⁻¹b + Δ·(columna {i+1} de B⁻¹) ≥ 0:</p><ul>'
         + ''.join(f'<li>{cnd}</li>' for cnd in conds) + f'</ul><p>⇒ {lo_d} ≤ Δ ≤ {hi_d} ⇒ <b>{lo_b} ≤ b<sub>{i+1}</sub> ≤ {hi_b}</b>.</p>')
    return q, s


def q_change_c(c, A, b, t, j, newcj):
    n, m = len(c), len(A)
    nc = list(c)
    nc[j] = newcj
    t2 = t.copy()
    # replace Z row with -c (new) in original columns for basic + nonbasic decision vars
    zrow = [F(0)] * (t.n + 1)
    for k in range(n):
        zrow[k] = -F(nc[k])
    # Z row before canonizing: in optimal table, Z row = -c for decision vars, 0 for slacks, keep structure
    t_raw = t.copy()
    t_raw.z = zrow
    # canonize: for each basic var with nonzero coef in zrow, add coef*row
    t_can = t_raw.copy()
    ops = ['Z'] + ['—'] * m
    terms = []
    for r, bj in enumerate(t.basis):
        k = t_can.z[bj]
        if k != 0:
            t_can.z = [a - k * x for a, x in zip(t_can.z, t.rows[r])]
            terms.append(f'{"+" if -k > 0 else "−"} {fr(abs(k)) + "·" if abs(k) != 1 else ""}F{r+1}')
    ops[0] = 'Z ' + ' '.join(terms) if terms else 'Z'
    q = f'Si el coeficiente de {t.names[j]} en la función objetivo cambia de {c[j]} a {newcj}, ¿cuál es la nueva solución óptima?'
    s = f'<p>Nueva función objetivo: Z = {lin(nc, ["x<sub>%d</sub>" % (k+1) for k in range(n)])}.</p>'
    if j in t.basis:
        s += '<p>Se escribe la fila Z con los nuevos −c<sub>j</sub> sobre la tabla óptima:</p>' + t_raw.html()
    if j not in t.basis:
        s += f'<p>{t.names[j]} es <b>no básica</b>: no hace falta canonizar, solo cambia su costo reducido. En general, el costo reducido nuevo es el anterior − Δc = {fr(t.z[j])} − ({fr(newcj - c[j])}) = {fr(t.z[j] - (newcj - c[j]))}.</p>'
        t_can = t.copy()
        t_can.z[j] = t.z[j] - (newcj - c[j])
        s += '<p>Tabla resultante:</p>' + t_can.html()
    else:
        s += '<p>Como hay variables básicas con coeficiente ≠ 0 en la fila Z, se <b>canoniza</b> (se suma a Z cada fila básica por su coeficiente):</p>' + t_can.html(ops=ops)
    if t_can.is_opt():
        x = t_can.values()
        s += '<p>Todos los costos reducidos ≥ 0 ⇒ <b>sigue óptima</b>, la solución no cambia: ' + ', '.join(f'{t.names[k]} = {fr(x[k])}' for k in range(n)) + f'; solo cambia Z = <b>{fr(t_can.z[-1])}</b>.</p>'
        return q, s, t_can
    s += '<p>Hay costo reducido negativo ⇒ ya no es óptima. Se continúa con <b>simplex primal</b>:</p>'
    steps, tf, st = primal_steps(t_can)
    s += ''.join(steps)
    x = tf.values()
    s += '<p><b>Nueva solución:</b> ' + ', '.join(f'{tf.names[k]} = {fr(x[k])}' for k in range(n)) + f'; Z = <b>{fr(tf.z[-1])}</b>.</p>'
    return q, s, tf


def q_range_c(c, A, b, t, j):
    n, m = len(c), len(A)
    q = f'Determine el rango de c<sub>{j+1}</sub> para el cual la solución actual sigue siendo óptima.'
    if j not in t.basis:
        hi = c[j] + t.z[j]
        s = (f'<p>{t.names[j]} es no básica. Su costo reducido con c<sub>{j+1}</sub> = {c[j]} + Δ es {fr(t.z[j])} − Δ ≥ 0 ⇒ Δ ≤ {fr(t.z[j])}.</p>'
             f'<p><b>−∞ &lt; c<sub>{j+1}</sub> ≤ {fr(hi)}</b>. Si c<sub>{j+1}</sub> supera {fr(hi)}, conviene producir {t.names[j]}.</p>')
        return q, s
    r = t.basis.index(j)
    lo, hi = None, None
    conds = []
    for k in range(t.n):
        if k in t.basis:
            continue
        a = t.rows[r][k]
        zk = t.z[k]
        conds.append(f'{t.names[k]}: {fr(zk)} {"+" if a >= 0 else "−"} {fr(abs(a))}·Δ ≥ 0')
        if a > 0:
            v = -zk / a
            lo = v if lo is None or v > lo else lo
        elif a < 0:
            v = -zk / a
            hi = v if hi is None or v < hi else hi
    lo_c = '−∞' if lo is None else fr(c[j] + lo)
    hi_c = '∞' if hi is None else fr(c[j] + hi)
    s = (f'<p>c<sub>{j+1}</sub> = {c[j]} + Δ. Al canonizar, a la fila Z se le suma Δ·(fila de {t.names[j]}). Los costos reducidos de las no básicas deben quedar ≥ 0:</p><ul>'
         + ''.join(f'<li>{x}</li>' for x in conds)
         + f'</ul><p>⇒ <b>{lo_c} ≤ c<sub>{j+1}</sub> ≤ {hi_c}</b>.</p>')
    return q, s


def q_new_constraint(c, A, b, t, a, rhs, op='≤'):
    n, m = len(c), len(A)
    x = t.values()
    lhs = sum(F(a[k]) * x[k] for k in range(n))
    names = [f'x<sub>{k+1}</sub>' for k in range(n)]
    cons = lin(a, names, rhs, op)
    q = f'Si se agrega la restricción {cons}, ¿cuál es la nueva solución óptima?'
    ok = lhs <= rhs if op == '≤' else lhs >= rhs
    s = f'<p>Se evalúa la solución actual: {lin(a, names)} = ' + ' + '.join(f'{a[k]}·{fr(x[k])}' for k in range(n) if a[k]) + f' = {fr(lhs)}.</p>'
    if ok:
        s += f'<p>{fr(lhs)} {op} {rhs} se cumple ⇒ <b>la solución óptima no cambia</b> (Z = {fr(t.z[-1])}).</p>'
        return q, s, t
    s += f'<p>{fr(lhs)} {op} {rhs} <b>no se cumple</b>. '
    aa = [F(v) for v in a]
    rr = F(rhs)
    if op == '≥':
        aa = [-v for v in aa]
        rr = -rr
        s += f'Se multiplica por −1 para dejarla en forma ≤: {lin(aa, names, rr, "≤")}. '
    sname = f'x<sub>{t.n+1}</sub>'
    s += f'Se agrega la holgura {sname} y la fila a la tabla óptima:</p>'
    names2 = t.names + [sname]
    rows2 = [r[:-1] + [F(0)] + [r[-1]] for r in t.rows]
    newrow = aa + [F(0)] * (t.n - n) + [F(1)] + [rr]
    t2 = Tableau(names2, t.z[:-1] + [F(0)] + [t.z[-1]], rows2 + [newrow], t.basis + [t.n])
    s += t2.html()
    # canonize new row
    t3 = t2.copy()
    terms = []
    for r, bj in enumerate(t.basis):
        k = t3.rows[-1][bj]
        if k != 0:
            t3.rows[-1] = [p - k * qv for p, qv in zip(t3.rows[-1], t2.rows[r])]
            terms.append(f'{"−" if k > 0 else "+"} {fr(abs(k)) + "·" if abs(k) != 1 else ""}F{r+1}')
    ops = ['—'] * (len(t3.rows) + 1)
    ops[-1] = f'F{len(t3.rows)} ' + ' '.join(terms)
    s += '<p>Se canoniza la nueva fila (dejar 0 bajo las variables básicas):</p>' + t3.html(ops=ops)
    steps, tf, st = dual_steps(t3)
    s += ''.join(steps)
    if st == 'feas':
        x = tf.values()
        s += '<p><b>Nueva solución:</b> ' + ', '.join(f'{tf.names[k]} = {fr(x[k])}' for k in range(n)) + f'; Z = <b>{fr(tf.z[-1])}</b> (no mejora, como debe ser).</p>'
    else:
        s += '<p>El problema queda infactible.</p>'
    return q, s, tf


def q_new_var(c, A, b, t, col, cnew, name=None):
    n, m = len(c), len(A)
    Bi = binv(t, n, m)
    y = [t.z[n + k] for k in range(m)]
    newcol = matvec(Bi, col)
    red = sum(yy * F(a) for yy, a in zip(y, col)) - F(cnew)
    nm = name or f'x<sub>{t.n+1}</sub>'
    q = f'Se evalúa un nuevo producto {nm} con utilidad {cnew} que usa ' + ', '.join(f'{col[i]} unidades del recurso {i+1}' for i in range(m)) + '. ¿Conviene producirlo? Si conviene, ¿cuál es la nueva solución?'
    s = ('<p>Costo reducido del nuevo producto: c̄ = y·a − c = '
         + ' + '.join(f'{fr(y[i])}·{col[i]}' for i in range(m)) + f' − {cnew} = <b>{fr(red)}</b>.</p>')
    if red >= 0:
        s += '<p>c̄ ≥ 0 ⇒ <b>no conviene</b>: los recursos que usaría valen más (a precios duales) que su utilidad. La solución no cambia.</p>'
        return q, s, t
    s += '<p>c̄ &lt; 0 ⇒ <b>conviene</b>. Su columna en la tabla óptima es B⁻¹·a:</p><div class="eq">' + matrix_html(Bi) + ' · ' + vec_html(col) + ' = ' + vec_html(newcol) + '</div>'
    names2 = t.names + [nm]
    rows2 = [r[:-1] + [newcol[i]] + [r[-1]] for i, r in enumerate(t.rows)]
    t2 = Tableau(names2, t.z[:-1] + [red] + [t.z[-1]], rows2, t.basis)
    s += '<p>Se agrega la columna y se sigue con simplex primal:</p>' + t2.html()
    steps, tf, st = primal_steps(t2)
    s += ''.join(steps)
    x = tf.values()
    s += '<p><b>Nueva solución:</b> ' + ', '.join(f'{tf.names[k]} = {fr(x[k])}' for k in list(range(n)) + [len(names2) - 1]) + f'; Z = <b>{fr(tf.z[-1])}</b>.</p>'
    return q, s, tf
