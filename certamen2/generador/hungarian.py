from fractions import Fraction as F
from itertools import permutations
import numpy as np
from scipy.optimize import linear_sum_assignment
from mnum import Mn
from core import fr

def mat(Cin):
    return [[Mn.of(x) for x in r] for r in Cin]

def max_matching(Z):
    n = len(Z); m = len(Z[0])
    match_c = [-1] * m
    def aug(i, seen):
        for j in range(m):
            if Z[i][j] and not seen[j]:
                seen[j] = True
                if match_c[j] == -1 or aug(match_c[j], seen):
                    match_c[j] = i; return True
        return False
    for i in range(n):
        aug(i, [False] * m)
    match_r = [-1] * n
    for j, i in enumerate(match_c):
        if i != -1: match_r[i] = j
    return match_r, match_c

def min_cover(A):
    n = len(A)
    Z = [[A[i][j] == 0 for j in range(n)] for i in range(n)]
    mr, mc = max_matching(Z)
    # König
    mark_r = [mr[i] == -1 for i in range(n)]; mark_c = [False] * n
    changed = True
    while changed:
        changed = False
        for i in range(n):
            if mark_r[i]:
                for j in range(n):
                    if Z[i][j] and not mark_c[j]:
                        mark_c[j] = True; changed = True
        for j in range(n):
            if mark_c[j] and mc[j] != -1 and not mark_r[mc[j]]:
                mark_r[mc[j]] = True; changed = True
    rows = [i for i in range(n) if not mark_r[i]]
    cols = [j for j in range(n) if mark_c[j]]
    return rows, cols, mr

def render(A, rlab, clab, rows_cov=(), cols_cov=(), stars=(), extra_col=None, extra_row=None, caption=None):
    n = len(A)
    h = ['<div class="tw"><table class="ht">']
    if caption: h.append(f'<caption>{caption}</caption>')
    h.append('<thead><tr><th></th>' + ''.join(f'<th class="{"cov" if j in cols_cov else ""}">{clab[j]}</th>' for j in range(len(A[0]))) + (f'<th class="pen">{extra_col[0]}</th>' if extra_col else '') + '</tr></thead><tbody>')
    for i in range(n):
        h.append(f'<tr><th class="{"cov" if i in rows_cov else ""}">{rlab[i]}</th>')
        for j in range(len(A[0])):
            cls = []
            if i in rows_cov: cls.append('cr')
            if j in cols_cov: cls.append('cc2')
            if i in rows_cov and j in cols_cov: cls.append('x2')
            if (i, j) in stars: cls.append('star')
            if A[i][j] == 0: cls.append('z')
            h.append(f'<td class="{" ".join(cls)}">{A[i][j]}</td>')
        if extra_col: h.append(f'<td class="pen">{extra_col[1][i]}</td>')
        h.append('</tr>')
    if extra_row:
        h.append(f'<tr><th class="pen">{extra_row[0]}</th>' + ''.join(f'<td class="pen">{x}</td>' for x in extra_row[1]) + ('<td></td>' if extra_col else '') + '</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)

def all_assignments(A, limit=4):
    n = len(A); res = []
    def rec(i, used, cur):
        if len(res) >= limit: return
        if i == n:
            res.append(list(cur)); return
        for j in range(n):
            if j not in used and A[i][j] == 0:
                used.add(j); cur.append(j); rec(i + 1, used, cur); cur.pop(); used.discard(j)
    rec(0, set(), [])
    return res

def hungarian(Cin, rlab, clab, maximize=False, fic_cost=0, orig=None):
    """Returns html, assignment list [(i,j)], total (in original terms), info."""
    C = mat(Cin)
    m, n = len(C), len(C[0])
    rl, cl = list(rlab), list(clab)
    h = ''
    if m != n:
        if m < n:
            for _ in range(n - m):
                C.append([Mn.of(fic_cost)] * n); rl.append('Fic' if n - m == 1 else f'Fic{_+1}')
        else:
            for row in C:
                row.extend([Mn.of(fic_cost)] * (m - n))
            for k in range(m - n): cl.append('Fic' if m - n == 1 else f'Fic{k+1}')
        h += f'<p><b>Paso 0 (balancear):</b> hay {m} filas y {n} columnas ⇒ se agrega{"n" if abs(m-n)>1 else ""} {abs(m-n)} {"fila" if m < n else "columna"}{"s" if abs(m-n)>1 else ""} ficticia{"s" if abs(m-n)>1 else ""} con costo {fic_cost}.</p>'
        h += render(C, rl, cl)
    N = len(C)
    orig_C = [list(r) for r in C]
    if maximize:
        big = max(x for r in C for x in r if not x.isM())
        C = [[(big - x) if not x.isM() else Mn(1, 0) for x in r] for r in C]
        h += f'<p><b>Maximizar:</b> se transforma a minimizar con c\'<sub>ij</sub> = {big} − c<sub>ij</sub> (el mayor valor de la tabla menos cada valor). Las celdas prohibidas siguen con M.</p>' + render(C, rl, cl)
    # row reduction
    rmin = [min(r) for r in C]
    h += '<p><b>Paso 1a:</b> a cada fila se le resta su menor valor (entre paréntesis):</p>' + render(C, rl, cl, extra_col=('mín', [f'({x})' for x in rmin]))
    A = [[x - rmin[i] for x in C[i]] for i in range(N)]
    cmin = [min(A[i][j] for i in range(N)) for j in range(N)]
    h += '<p><b>Paso 1b:</b> a cada columna se le resta su menor valor:</p>' + render(A, rl, cl, extra_row=('mín', [f'({x})' for x in cmin]))
    A = [[A[i][j] - cmin[j] for j in range(N)] for i in range(N)]
    it = 0
    while True:
        rows, cols, mr = min_cover(A)
        L = len(rows) + len(cols)
        if L == N:
            stars = [(i, mr[i]) for i in range(N)]
            h += f'<p><b>Paso 2:</b> se necesitan {L} líneas para cubrir todos los ceros = n = {N} ⇒ <b>óptimo</b>. Asignación sobre los ceros (marcados):</p>' + render(A, rl, cl, rows, cols, stars)
            break
        unc = [A[i][j] for i in range(N) for j in range(N) if i not in rows and j not in cols]
        k = min(unc)
        h += f'<p><b>Paso 2:</b> mínimo de líneas = {L} &lt; {N}. <b>Paso 3:</b> menor valor no cubierto k = {k}: se resta a los no cubiertos y se suma a las intersecciones.</p>' + render(A, rl, cl, rows, cols)
        A = [[A[i][j] - k if (i not in rows and j not in cols) else (A[i][j] + k if (i in rows and j in cols) else A[i][j]) for j in range(N)] for i in range(N)]
        it += 1
        if it > 10: raise RuntimeError('loop')
    total = sum((orig_C[i][j] for i, j in stars), Mn(0))
    lines = [f'{rl[i]} → {cl[j]} ({orig_C[i][j]})' for i, j in stars]
    h += '<p><b>Solución:</b> ' + '; '.join(lines) + f'. <b>{"Beneficio" if maximize else "Costo"} total = {total}</b>.</p>'
    alts = all_assignments(A, limit=6)
    if len(alts) > 1:
        other = [p for p in alts if [j for _, j in stars] != p][0]
        tot2 = sum((orig_C[i][j] for i, j in enumerate(other)), Mn(0))
        h += f'<p><b>Soluciones múltiples:</b> hay más de una asignación sobre los ceros, por ejemplo: ' + '; '.join(f'{rl[i]} → {cl[j]}' for i, j in enumerate(other)) + f' (total = {tot2}).</p>'
        multi = True
    else:
        multi = False
    # verify
    M = 10**6
    arr = np.array([[x.val(M) for x in r] for r in orig_C])
    r_, c_ = linear_sum_assignment(arr, maximize=maximize) if not maximize else linear_sum_assignment(np.where(arr > M / 2, -M, arr), maximize=True)
    ref = arr[r_, c_].sum() if not maximize else np.where(arr > M / 2, -M, arr)[r_, c_].sum()
    assert abs(total.val(M) - ref) < 1e-6, (total, ref)
    return h, stars, total, {'multi': multi, 'iters': it, 'rl': rl, 'cl': cl}

def data_html(C, rlab, clab):
    rows = ''.join(f'<tr><th>{rlab[i]}</th>' + ''.join(f'<td>{x if isinstance(x, str) and x != "M" else Mn.of(x)}</td>' for x in C[i]) + '</tr>' for i in range(len(C)))
    return '<div class="tw"><table class="ht"><thead><tr><th></th>' + ''.join(f'<th>{c}</th>' for c in clab) + f'</tr></thead><tbody>{rows}</tbody></table></div>'
