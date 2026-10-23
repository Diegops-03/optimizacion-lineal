from fractions import Fraction as F
from mnum import Mn
from core import fr
import numpy as np
from scipy.optimize import linprog

def C_(C):
    return [[Mn.of(x) for x in row] for row in C]

def zval(C, alloc):
    return sum((C[i][j] * q for (i, j), q in alloc.items()), Mn(0))

def z_text(C, alloc):
    terms = [f'{C[i][j]}·{fr(q)}' for (i, j), q in sorted(alloc.items()) if q != 0]
    return ' + '.join(terms) + f' = <b>{zval(C, alloc)}</b>'

# ---------------- initial solutions ----------------
def northwest(C, sup, dem):
    s, d = list(map(F, sup)), list(map(F, dem))
    i = j = 0; m, n = len(s), len(d)
    alloc = {}
    while i < m and j < n:
        q = min(s[i], d[j]); alloc[(i, j)] = q
        s[i] -= q; d[j] -= q
        if s[i] == 0 and i < m - 1:
            i += 1
        elif d[j] == 0:
            j += 1
        else:
            i += 1
    return alloc

def min_cost(C, sup, dem):
    s, d = list(map(F, sup)), list(map(F, dem)); m, n = len(s), len(d)
    rows, cols = set(range(m)), set(range(n)); alloc = {}
    while rows and cols:
        if len(rows) == 1:
            i = next(iter(rows))
            for j in sorted(cols): alloc[(i, j)] = d[j]
            break
        if len(cols) == 1:
            j = next(iter(cols))
            for i in sorted(rows): alloc[(i, j)] = s[i]
            break
        i, j = min(((i, j) for i in rows for j in cols), key=lambda p: (C[p[0]][p[1]], p))
        q = min(s[i], d[j]); alloc[(i, j)] = q; s[i] -= q; d[j] -= q
        if s[i] == 0: rows.discard(i)
        else: cols.discard(j)
    return alloc

def vogel(C, sup, dem):
    s, d = list(map(F, sup)), list(map(F, dem)); m, n = len(s), len(d)
    rows, cols = set(range(m)), set(range(n)); alloc = {}
    pr = {i: [] for i in range(m)}; pc = {j: [] for j in range(n)}
    log = []
    while rows and cols:
        if len(rows) == 1 or len(cols) == 1:
            # assign remaining by min cost order
            cells = sorted(((i, j) for i in rows for j in cols), key=lambda p: (C[p[0]][p[1]], p))
            for i, j in cells:
                q = min(s[i], d[j]); alloc[(i, j)] = q; s[i] -= q; d[j] -= q
            log.append('Queda una sola fila o columna: se completa con el método del costo menor.')
            break
        pen = {}
        for i in rows:
            cs = sorted(C[i][j] for j in cols); p = cs[1] - cs[0]; pen[('r', i)] = p; pr[i].append(p)
        for j in cols:
            cs = sorted(C[i][j] for i in rows); p = cs[1] - cs[0]; pen[('c', j)] = p; pc[j].append(p)
        best = max(pen.values())
        cand = [k for k, v in pen.items() if v == best]
        def mincell(k):
            if k[0] == 'r':
                j = min(cols, key=lambda j: (C[k[1]][j], j)); return (k[1], j)
            i = min(rows, key=lambda i: (C[i][k[1]], i)); return (i, k[1])
        k = min(cand, key=lambda k: (C[mincell(k)[0]][mincell(k)[1]], 0 if k[0] == 'r' else 1, k[1]))
        i, j = mincell(k)
        q = min(s[i], d[j]); alloc[(i, j)] = q; s[i] -= q; d[j] -= q
        lname = (f'fila {i+1}' if k[0] == 'r' else f'columna {j+1}')
        log.append(f'Mayor penalidad = {best} ({lname}); se asigna {fr(q)} a la celda ({i+1},{j+1}) de costo {C[i][j]}.')
        if s[i] == 0 and d[j] == 0:
            if k[0] == 'r': rows.discard(i)
            else: cols.discard(j)
        elif s[i] == 0: rows.discard(i)
        else: cols.discard(j)
    return alloc, pr, pc, log

# ---------------- MODI ----------------
def duals(C, alloc, m, n):
    basics = list(alloc.keys())
    rc = [sum(1 for (i, j) in basics if i == r) for r in range(m)]
    cc = [sum(1 for (i, j) in basics if j == c) for c in range(n)]
    u = [None] * m; v = [None] * n
    if max(rc) >= max(cc):
        r0 = rc.index(max(rc)); u[r0] = Mn(0); start = ('u', r0)
    else:
        c0 = cc.index(max(cc)); v[c0] = Mn(0); start = ('v', c0)
    changed = True
    while changed:
        changed = False
        for (i, j) in basics:
            if u[i] is not None and v[j] is None:
                v[j] = C[i][j] - u[i]; changed = True
            elif v[j] is not None and u[i] is None:
                u[i] = C[i][j] - v[j]; changed = True
    if any(x is None for x in u) or any(x is None for x in v):
        raise ValueError('degenerate: basis disconnected')
    return u, v, start

def find_cycle(alloc, enter):
    cells = set(alloc.keys()) | {enter}
    changed = True
    while changed:
        changed = False
        for c in list(cells):
            if c == enter: continue
            r = sum(1 for x in cells if x[0] == c[0]); k = sum(1 for x in cells if x[1] == c[1])
            if r < 2 or k < 2:
                cells.discard(c); changed = True
    # order: start enter, move along row, then col alternately
    path = [enter]; cur = enter; horiz = True
    while True:
        if horiz:
            nxt = [x for x in cells if x[0] == cur[0] and x != cur and x not in path]
        else:
            nxt = [x for x in cells if x[1] == cur[1] and x != cur and x not in path]
        if not nxt:
            break
        cur = nxt[0]; path.append(cur); horiz = not horiz
    return path

def render(C, sup, dem, alloc, u=None, v=None, red=None, signs=None, rlab=None, clab=None, caption=None, pens=None):
    m, n = len(sup), len(dem)
    rlab = rlab or [f'{i+1}' for i in range(m)]
    clab = clab or [f'{j+1}' for j in range(n)]
    h = ['<div class="tw"><table class="tt">']
    if caption: h.append(f'<caption>{caption}</caption>')
    h.append('<thead><tr><th></th>' + ''.join(f'<th>{c}</th>' for c in clab) + '<th>Oferta</th>' + ('<th>u<sub>i</sub></th>' if u else '') + ('<th class="pen">Penal.</th>' if pens else '') + '</tr></thead><tbody>')
    for i in range(m):
        h.append(f'<tr><th>{rlab[i]}</th>')
        for j in range(n):
            cost = C[i][j]
            inner = f'<span class="cc">{cost}</span>'
            sg = signs.get((i, j)) if signs else None
            if (i, j) in alloc:
                inner += f'<span class="al">{fr(alloc[(i, j)])}</span>'
            elif red is not None and (i, j) in red:
                inner += f'<span class="rd{" neg" if red[(i,j)] < 0 else ""}">{red[(i, j)]}</span>'
            if sg:
                inner += f'<span class="sg">{sg}</span>'
            cls = ' class="ent"' if sg == '+' and (i, j) not in alloc else ''
            h.append(f'<td{cls}>{inner}</td>')
        h.append(f'<td class="sd">{fr(sup[i])}</td>')
        if u: h.append(f'<td class="uv">{u[i]}</td>')
        if pens: h.append(f'<td class="pen">{"/".join(str(p) for p in pens[0][i])}</td>')
        h.append('</tr>')
    h.append('<tr><th>Demanda</th>' + ''.join(f'<td class="sd">{fr(x)}</td>' for x in dem) + '<td></td>' + ('<td></td>' if u else '') + ('<td></td>' if pens else '') + '</tr>')
    if v:
        h.append('<tr><th>v<sub>j</sub></th>' + ''.join(f'<td class="uv">{x}</td>' for x in v) + '<td></td><td></td>' + ('<td></td>' if pens else '') + '</tr>')
    if pens:
        h.append('<tr><th class="pen">Penal.</th>' + ''.join(f'<td class="pen">{"/".join(str(p) for p in pens[1][j])}</td>' for j in range(n)) + '<td></td>' + ('<td></td>' if u else '') + '<td></td></tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)

def modi(C, sup, dem, alloc, rlab=None, clab=None, maxit=12):
    m, n = len(sup), len(dem)
    alloc = dict(alloc); out = []; it = 0
    while True:
        u, v, start = duals(C, alloc, m, n)
        red = {(i, j): C[i][j] - u[i] - v[j] for i in range(m) for j in range(n) if (i, j) not in alloc}
        neg = [k for k, x in red.items() if x < 0]
        st = f'u<sub>{start[1]+1}</sub> = 0' if start[0] == 'u' else f'v<sub>{start[1]+1}</sub> = 0'
        if not neg:
            out.append({'table': render(C, sup, dem, alloc, u, v, red, rlab=rlab, clab=clab), 'text': f'Se fija {st} (la fila/columna con más celdas básicas) y se resuelve u<sub>i</sub> + v<sub>j</sub> = c<sub>ij</sub> en las básicas. Costos reducidos c<sub>ij</sub> − u<sub>i</sub> − v<sub>j</sub> de las no básicas: todos ≥ 0 ⇒ <b>solución óptima</b>. Z = ' + z_text(C, alloc), 'red': red, 'u': u, 'v': v})
            return alloc, out, red
        enter = min(neg, key=lambda k: (red[k], k))
        cyc = find_cycle(alloc, enter)
        signs = {c: ('+' if k % 2 == 0 else '−') for k, c in enumerate(cyc)}
        minus = [c for c in cyc if signs[c] == '−']
        theta = min(alloc[c] for c in minus)
        leave = min((c for c in minus if alloc[c] == theta), key=lambda c: c)
        cyc_txt = ' → '.join(f'({i+1},{j+1}){signs[(i,j)]}' for i, j in cyc)
        text = (f'Se fija {st}. Costo reducido más negativo: celda ({enter[0]+1},{enter[1]+1}) con {red[enter]} ⇒ <b>entra</b>. Circuito: {cyc_txt}. '
                f'Menor valor en celdas "−": {fr(theta)} ⇒ <b>sale</b> la celda ({leave[0]+1},{leave[1]+1}). Z actual = {zval(C, alloc)}.')
        out.append({'table': render(C, sup, dem, alloc, u, v, red, signs, rlab=rlab, clab=clab), 'text': text})
        for c in cyc:
            if c == enter: alloc[c] = theta
            elif signs[c] == '+': alloc[c] += theta
            else: alloc[c] -= theta
        del alloc[leave]
        it += 1
        if it > maxit: raise RuntimeError('too many iterations')

def lp_check(C, sup, dem, M=10**6):
    m, n = len(sup), len(dem)
    c = [Mn.of(C[i][j]).val(M) for i in range(m) for j in range(n)]
    A_eq = []; b_eq = []
    for i in range(m):
        A_eq.append([1 if k // n == i else 0 for k in range(m * n)]); b_eq.append(float(sup[i]))
    for j in range(n):
        A_eq.append([1 if k % n == j else 0 for k in range(m * n)]); b_eq.append(float(dem[j]))
    r = linprog(c, A_eq=A_eq, b_eq=b_eq, method='highs')
    return r.fun

def multiple(red):
    return [k for k, x in red.items() if x == 0]
