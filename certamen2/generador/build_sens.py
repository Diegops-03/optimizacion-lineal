import random, json, math
from fractions import Fraction as F
from scipy.optimize import linprog
from sens import *

def scipy_max(c, A, b, extra=None):
    A_ub, b_ub = [list(r) for r in A], list(b)
    if extra:
        for a, rhs, op in extra:
            if op == '≤':
                A_ub.append(list(a)); b_ub.append(rhs)
            else:
                A_ub.append([-v for v in a]); b_ub.append(-rhs)
    r = linprog([-x for x in c], A_ub=A_ub, b_ub=b_ub, method='highs')
    return (-r.fun if r.status == 0 else None)

def check(z_ours, z_ref, tag):
    assert z_ref is not None and abs(float(z_ours) - z_ref) < 1e-7, (tag, z_ours, z_ref)

def range_c_vals(c, t, j):
    n = len(c)
    if j not in t.basis:
        return None, c[j] + t.z[j]
    r = t.basis.index(j)
    lo = hi = None
    for k in range(t.n):
        if k in t.basis: continue
        a, zk = t.rows[r][k], t.z[k]
        if a > 0:
            v = -zk / a; lo = v if lo is None or v > lo else lo
        elif a < 0:
            v = -zk / a; hi = v if hi is None or v < hi else hi
    return (None if lo is None else c[j] + lo), (None if hi is None else c[j] + hi)

def range_b_vals(c, A, b, t, i):
    n, m = len(c), len(A)
    Bi = binv(t, n, m)
    base = matvec(Bi, b)
    lo = hi = None
    for r in range(m):
        a, d = base[r], Bi[r][i]
        if d > 0:
            v = -a / d; lo = v if lo is None or v > lo else lo
        elif d < 0:
            v = -a / d; hi = v if hi is None or v < hi else hi
    return (None if lo is None else b[i] + lo), (None if hi is None else b[i] + hi)

def ex(enun, parts):
    """parts: list of (q, s). Returns dict with lettered questions and solutions."""
    letters = 'abcdef'
    qh = enun + '<ol class="parts">' + ''.join(f'<li><b>{letters[k]})</b> {q}</li>' for k, (q, s) in enumerate(parts)) + '</ol>'
    sh = ''.join(f'<div class="solpart"><h5>{letters[k]})</h5>{s}</div>' for k, (q, s) in enumerate(parts))
    return {'q': qh, 's': sh}

def get_lp(seed, m, n, **kw):
    rng = random.Random(seed)
    return nice_lp(rng, m, n, **kw)

# ---------------- part builders with verification ----------------
def P_identify(c, A, b, t):
    q, s = q_identify(c, A, b, t); return q, s

def P_b_feasible(c, A, b, t, rng):
    n, m = len(c), len(A)
    for _ in range(200):
        i = rng.randrange(m)
        lo, hi = range_b_vals(c, A, b, t, i)
        lo = 0 if lo is None else lo; hi = b[i] + 20 if hi is None else hi
        cands = [v for v in range(max(1, math.ceil(lo)), math.floor(hi) + 1) if v != b[i]]
        if cands:
            nb = list(b); nb[i] = rng.choice(cands)
            q, s, tf = q_change_b(c, A, b, t, nb)
            Bi = binv(t, n, m); xb = matvec(Bi, nb)
            z = sum(a * x for a, x in zip(cB(t, c), xb))
            check(z, scipy_max(c, A, nb), 'bfeas')
            return q, s
    raise RuntimeError

def P_b_infeasible(c, A, b, t, rng):
    n, m = len(c), len(A)
    for _ in range(400):
        i = rng.randrange(m)
        lo, hi = range_b_vals(c, A, b, t, i)
        opts = []
        if hi is not None: opts += list(range(math.floor(hi) + 2, math.floor(hi) + 12))
        if lo is not None and lo > 2: opts += [v for v in range(1, math.ceil(lo) - 1)]
        if not opts: continue
        nb = list(b); nb[i] = rng.choice(opts)
        zref = scipy_max(c, A, nb)
        if zref is None: continue
        q, s, tf = q_change_b(c, A, b, t, nb)
        if tf is None or not tf.is_feas(): continue
        dens = max(x.denominator for r in tf.rows for x in r)
        if dens > 30: continue
        check(tf.z[-1], zref, 'binf')
        return q, s
    raise RuntimeError('binf')

def P_range_b(c, A, b, t, rng, i=None):
    m = len(A)
    i = rng.randrange(m) if i is None else i
    return q_range_b(c, A, b, t, i)

def P_c_keep(c, A, b, t, rng):
    n = len(c)
    for _ in range(200):
        j = rng.randrange(n)
        lo, hi = range_c_vals(c, t, j)
        lo = 1 if lo is None else lo; hi = c[j] + 10 if hi is None else hi
        cands = [v for v in range(max(1, math.ceil(lo)), math.floor(hi) + 1) if v != c[j]]
        if cands:
            v = rng.choice(cands); nc = list(c); nc[j] = v
            q, s, tf = q_change_c(c, A, b, t, j, v)
            check(tf.z[-1], scipy_max(nc, A, b), 'ckeep'); return q, s
    raise RuntimeError

def P_c_break(c, A, b, t, rng, j=None):
    n = len(c)
    order = [j] if j is not None else rng.sample(range(n), n)
    for j in order:
        lo, hi = range_c_vals(c, t, j)
        opts = []
        if hi is not None: opts += list(range(math.floor(hi) + 1, math.floor(hi) + 8))
        if lo is not None and lo > 1: opts += list(range(1, math.ceil(lo)))
        rng.shuffle(opts)
        for v in opts:
            if v == c[j] or v <= 0: continue
            nc = list(c); nc[j] = v
            q, s, tf = q_change_c(c, A, b, t, j, v)
            if tf.is_opt() and tf is not None:
                dens = max(x.denominator for r in tf.rows for x in r)
                if dens > 30: continue
                check(tf.z[-1], scipy_max(nc, A, b), 'cbreak')
                if 'simplex primal' in s:
                    return q, s
    raise RuntimeError('cbreak')

def P_range_c(c, A, b, t, rng, j=None):
    n = len(c)
    j = rng.randrange(n) if j is None else j
    return q_range_c(c, A, b, t, j)

def P_newcons(c, A, b, t, rng, kind='violated', op='≤'):
    n = len(c)
    x = t.values()
    for _ in range(500):
        a = [rng.randint(1, 5) for _ in range(n)]
        if rng.random() < 0.3:
            a[rng.randrange(n)] = 0
        if all(v == 0 for v in a): continue
        lhs = sum(F(a[k]) * x[k] for k in range(n))
        if op == '≤':
            if kind == 'ok':
                rhs = math.ceil(lhs) + rng.randint(1, 4)
            else:
                rhs = math.floor(lhs) - rng.randint(0, 3)
                if rhs <= 0 or rhs >= lhs: continue
        else:
            if kind == 'ok':
                rhs = math.floor(lhs) - rng.randint(0, 3)
                if rhs <= 0: continue
            else:
                rhs = math.ceil(lhs) + rng.randint(0, 3)
                if rhs <= lhs: continue
        zref = scipy_max(c, A, b, extra=[(a, rhs, op)])
        if zref is None: continue
        q, s, tf = q_new_constraint(c, A, b, t, a, rhs, op)
        if kind == 'violated':
            if not tf.is_feas(): continue
            dens = max(x2.denominator for r in tf.rows for x2 in r)
            if dens > 40: continue
        check(tf.z[-1], zref, 'newcons')
        return q, s
    raise RuntimeError('newcons')

def P_newvar(c, A, b, t, rng, want_enter=True):
    n, m = len(c), len(A)
    y = [t.z[n + k] for k in range(m)]
    for _ in range(500):
        col = [rng.randint(1, 5) for _ in range(m)]
        val = sum(yy * F(a) for yy, a in zip(y, col))
        if want_enter:
            cnew = math.floor(val) + rng.randint(1, 4)
        else:
            cnew = max(1, math.floor(val) - rng.randint(0, 3))
            if cnew >= val: continue
        q, s, tf = q_new_var(c, A, b, t, col, cnew)
        zref = scipy_max(list(c) + [cnew], [list(A[i]) + [col[i]] for i in range(m)], b)
        if tf.is_opt():
            dens = max(x2.denominator for r in tf.rows for x2 in r)
            if dens > 40: continue
            check(tf.z[-1], zref, 'newvar')
            return q, s
    raise RuntimeError('newvar')


def make_problem(seed, m, n, parts_spec, maxden=12):
    c, A, b, t = get_lp(seed, m, n, maxden=maxden)
    rng = random.Random(seed * 31 + 5)
    enun = '<p>Considere el modelo:</p>' + enunciado_base(c, A, b, t)
    parts = []
    for sp in parts_spec:
        fn, kw = sp if isinstance(sp, tuple) else (sp, {})
        parts.append(fn(c, A, b, t, rng, **kw) if fn is not P_identify else fn(c, A, b, t))
    return ex(enun, parts)

def try_make(seed0, m, n, spec, maxden=12):
    for s in range(seed0, seed0 + 200):
        try:
            return make_problem(s, m, n, spec, maxden)
        except (RuntimeError, AssertionError) as e:
            if isinstance(e, AssertionError):
                print('ASSERT', e)
            continue
    raise RuntimeError('fail ' + str(seed0))
