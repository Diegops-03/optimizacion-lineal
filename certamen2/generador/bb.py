import math, itertools, random
from fractions import Fraction as F
from core import fr, lin, table

# constraint: (a1, a2, rhs) meaning a1 x1 + a2 x2 <= rhs
def vertices(cons):
    allc = list(cons) + [(-1, 0, 0), (0, -1, 0)]  # x1>=0, x2>=0
    pts = set()
    for (a, b, r), (c, d, s) in itertools.combinations(allc, 2):
        det = F(a) * d - F(b) * c
        if det == 0:
            continue
        x = (F(r) * d - F(b) * s) / det
        y = (F(a) * s - F(r) * c) / det
        if all(F(p) * x + F(q) * y <= F(t) for p, q, t in allc):
            pts.add((x, y))
    return list(pts)

def lp2(c, cons):
    v = vertices(cons)
    if not v:
        return None
    best = max(v, key=lambda p: c[0] * p[0] + c[1] * p[1])
    z = c[0] * best[0] + c[1] * best[1]
    ties = [p for p in v if c[0] * p[0] + c[1] * p[1] == z]
    return best, z, v, len(ties)

def is_int(x):
    return F(x).denominator == 1

def fmt_pt(p):
    return f'({fr(p[0])}; {fr(p[1])})'

def dec(x):
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    s = f'{float(x):.3f}'.rstrip('0').rstrip('.')
    return s.replace('.', ',')

def cons_text(a, b, r, names=('x<sub>1</sub>', 'x<sub>2</sub>')):
    # pretty: turn -x2 <= -1 into x2 >= 1 when single var negative
    if a == 0 and b < 0:
        return f'{names[1]} ≥ {fr(F(-r, 1) / (-b) if b != -1 else -r)}' if True else ''
    if b == 0 and a < 0:
        return f'{names[0]} ≥ {fr(F(r) / a)}'
    return lin([a, b], list(names), r, '≤')


def branch_and_bound(c, cons, intc=True):
    """DFS, left (≤) first, branch on first fractional variable (x1 before x2).
    Returns nodes list and incumbent."""
    nodes = []
    best = {'z': None, 'x': None, 'label': None}
    def solve(label, extra, depth, parent, branch_txt):
        res = lp2(c, cons + extra)
        node = {'label': label, 'parent': parent, 'branch': branch_txt, 'depth': depth, 'extra': list(extra)}
        nodes.append(node)
        if res is None:
            node['status'] = 'NF'
            return
        x, z, v, ties = res
        node['x'], node['z'], node['ties'] = x, z, ties
        if all(is_int(t) for t in x):
            node['status'] = 'entera'
            if best['z'] is None or z > best['z']:
                if best['label']:
                    node['note'] = f"mejora la incumbente anterior ({best['label']}, Z = {dec(best['z'])})"
                best.update(z=z, x=x, label=label)
                node['status'] = 'incumbente'
            else:
                node['note'] = 'entera pero no mejora a la incumbente'
            return
        if best['z'] is not None:
            bound = math.floor(z) if intc else z
            if bound <= best['z']:
                node['status'] = 'podado'
                node['note'] = f"Z = {dec(z)} ≤ incumbente {dec(best['z'])}" if z <= best['z'] else f"Z = {dec(z)}, pero como Z entero debe ser ≤ {math.floor(z)} ≤ incumbente {dec(best['z'])}"
                return
        k = 0 if not is_int(x[0]) else 1
        fl = math.floor(x[k]); ce = fl + 1
        node['status'] = 'ramifica'
        node['branch_var'] = k
        e1 = (1, 0, fl) if k == 0 else (0, 1, fl)
        e2 = (-1, 0, -ce) if k == 0 else (0, -1, -ce)
        nm = f'x{k+1}'
        lab1 = label + '1' if label != 'P0' else 'P1'
        lab2 = label + '2' if label != 'P0' else 'P2'
        solve(lab1, extra + [e1], depth + 1, label, f'x<sub>{k+1}</sub> ≤ {fl}')
        solve(lab2, extra + [e2], depth + 1, label, f'x<sub>{k+1}</sub> ≥ {ce}')
    solve('P0', [], 0, None, '')
    return nodes, best


def tree_html(nodes):
    # nested list
    ch = {}
    for n in nodes:
        ch.setdefault(n['parent'], []).append(n)
    def box(n):
        if n['status'] == 'NF':
            body = '<b>Infactible</b>'
        else:
            body = f"x<sub>1</sub> = {dec(n['x'][0])}<br>x<sub>2</sub> = {dec(n['x'][1])}<br>Z = {dec(n['z'])}"
        tag = {'NF': 'Poda: infactible', 'incumbente': 'Entera → incumbente', 'entera': 'Entera (no mejora)', 'podado': 'Poda por cota', 'ramifica': 'Ramificar'}[n['status']]
        cls = {'NF': 'nf', 'incumbente': 'inc', 'entera': 'ent', 'podado': 'pod', 'ramifica': 'ram'}[n['status']]
        br = f'<div class="br">{n["branch"]}</div>' if n['branch'] else ''
        note = f'<div class="nn">{n["note"]}</div>' if n.get('note') else ''
        kids = ch.get(n['label'], [])
        kh = ('<ul>' + ''.join(f'<li>{box(k)}</li>' for k in kids) + '</ul>') if kids else ''
        return f'{br}<div class="node {cls}"><div class="nl">{n["label"]}</div>{body}<div class="tg">{tag}</div>{note}</div>{kh}'
    root = ch[None][0]
    return f'<div class="tree"><ul><li>{box(root)}</li></ul></div>'


def svg_graph(c, cons, mark=None, intopt=None, show_int=True, title=''):
    v = vertices(cons)
    xs = [p[0] for p in v] + [F(1)]
    ys = [p[1] for p in v] + [F(1)]
    X = float(max(xs)) * 1.25 + 0.5
    Y = float(max(ys)) * 1.25 + 0.5
    X = max(X, 3); Y = max(Y, 3)
    W, H, pad = 340, 300, 34
    sx = (W - pad - 12) / X; sy = (H - pad - 12) / Y
    s = min(sx, sy)
    def P(x, y):
        return pad + float(x) * s, H - pad - float(y) * s
    out = [f'<svg viewBox="0 0 {W} {H}" class="graph" role="img" aria-label="Región factible">']
    # grid
    for i in range(0, int(X) + 1):
        x0, _ = P(i, 0)
        out.append(f'<line x1="{x0:.1f}" y1="{12}" x2="{x0:.1f}" y2="{H-pad:.1f}" class="gr"/>')
        out.append(f'<text x="{x0:.1f}" y="{H-pad+14:.1f}" class="ax" text-anchor="middle">{i}</text>')
    for j in range(0, int(Y) + 1):
        _, y0 = P(0, j)
        out.append(f'<line x1="{pad}" y1="{y0:.1f}" x2="{W-12}" y2="{y0:.1f}" class="gr"/>')
        if j:
            out.append(f'<text x="{pad-6}" y="{y0+4:.1f}" class="ax" text-anchor="end">{j}</text>')
    # axes
    out.append(f'<line x1="{pad}" y1="{H-pad}" x2="{W-12}" y2="{H-pad}" class="axl"/>')
    out.append(f'<line x1="{pad}" y1="{H-pad}" x2="{pad}" y2="12" class="axl"/>')
    out.append(f'<text x="{W-14}" y="{H-pad-6}" class="ax" text-anchor="end">x₁</text>')
    out.append(f'<text x="{pad+6}" y="20" class="ax">x₂</text>')
    # polygon
    if v:
        cx = sum(float(p[0]) for p in v) / len(v); cy = sum(float(p[1]) for p in v) / len(v)
        vs = sorted(v, key=lambda p: math.atan2(float(p[1]) - cy, float(p[0]) - cx))
        pts = ' '.join('%.1f,%.1f' % P(*p) for p in vs)
        out.append(f'<polygon points="{pts}" class="reg"/>')
    # constraint lines
    for k, (a, b, r) in enumerate(cons):
        # clip line a x + b y = r to box
        segs = []
        for x in (0, X):
            if b != 0:
                y = (r - a * x) / b
                if 0 <= y <= Y: segs.append((x, y))
        for y in (0, Y):
            if a != 0:
                x = (r - b * y) / a
                if 0 <= x <= X: segs.append((x, y))
        segs = sorted(set((round(float(p), 6), round(float(q), 6)) for p, q in segs))
        if len(segs) >= 2:
            (x1, y1), (x2, y2) = segs[0], segs[-1]
            a1, b1 = P(x1, y1); a2, b2 = P(x2, y2)
            out.append(f'<line x1="{a1:.1f}" y1="{b1:.1f}" x2="{a2:.1f}" y2="{b2:.1f}" class="cl c{k%4}"/>')
            # label near second point
            fx = 0.12 + 0.18 * (k % 3)
            lx, ly = a1 + (a2 - a1) * fx, b1 + (b2 - b1) * fx
            out.append(f'<text x="{lx+4:.1f}" y="{ly-4:.1f}" class="clab c{k%4}">({k+1})</text>')
    # integer points
    if show_int:
        for i in range(0, int(X) + 1):
            for j in range(0, int(Y) + 1):
                if all(a * i + b * j <= r for a, b, r in cons):
                    x0, y0 = P(i, j)
                    out.append(f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="2.2" class="ip"/>')
    # vertices
    for p in v:
        x0, y0 = P(*p)
        out.append(f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="3.2" class="vx"/>')
    if mark:
        x0, y0 = P(*mark)
        out.append(f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="6" class="opt"/>')
        out.append(f'<text x="{x0+8:.1f}" y="{y0-8:.1f}" class="olab">RL {fmt_pt((F(mark[0]), F(mark[1])))}</text>')
    if intopt:
        x0, y0 = P(*intopt)
        out.append(f'<rect x="{x0-5:.1f}" y="{y0-5:.1f}" width="10" height="10" class="iopt"/>')
        out.append(f'<text x="{x0+8:.1f}" y="{y0+14:.1f}" class="ilab">entera ({intopt[0]}; {intopt[1]})</text>')
    out.append('</svg>')
    return ''.join(out)


def vertex_table(c, cons):
    v = sorted(vertices(cons))
    rows = [[fmt_pt(p), fr(c[0] * p[0] + c[1] * p[1]), dec(c[0] * p[0] + c[1] * p[1])] for p in v]
    return table(['Vértice (x₁; x₂)', 'Z', 'Z (decimal)'], rows)
