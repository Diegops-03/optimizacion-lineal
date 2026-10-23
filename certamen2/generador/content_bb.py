import json, random, math
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from fractions import Fraction as F
from bb import *
from core import model_html, lin

def ref(c, cons):
    A = np.array([[a, b] for a, b, r in cons], float); ub = np.array([r for a, b, r in cons], float)
    r = milp(-np.array(c, float), constraints=LinearConstraint(A, -np.inf, ub), integrality=[1, 1], bounds=Bounds(0, np.inf))
    return -r.fun

def model(c, cons):
    A = [[a, b] for a, b, r in cons]; b = [r for a, b, r in cons]
    return model_html(c, A, b, integer=True)

def gen(rng, ncons=None, min_nodes=5, max_nodes=9):
    for _ in range(20000):
        k = ncons or rng.choice([2, 2, 3])
        c = [rng.randint(1, 8), rng.randint(1, 8)]
        cons = []
        for i in range(k):
            a = rng.randint(1, 9); b = rng.randint(1, 9)
            if rng.random() < 0.25:
                if rng.random() < 0.5: a = -rng.randint(1, 3)
                else: b = -rng.randint(1, 3)
            r = rng.randint(6, 45) if (a > 0 and b > 0) else rng.randint(0, 8)
            cons.append((a, b, r))
        res = lp2(c, cons)
        if res is None: continue
        x, z, v, ties = res
        if ties > 1: continue
        if max(max(p) for p in v) > 9: continue
        # bounded check: polygon must be bounded -> test with large objective directions
        if lp2([1, 0], cons + [(1, 0, 100)])[0][0] >= 100 or lp2([0, 1], cons + [(0, 1, 100)])[0][1] >= 100: continue
        if is_int(x[0]) and is_int(x[1]): continue
        if any(F(p).denominator > 12 for p in x): continue
        nodes, best = branch_and_bound(c, cons)
        if not (min_nodes <= len(nodes) <= max_nodes): continue
        if any(n.get('ties', 1) > 1 for n in nodes): continue
        if best['z'] is None: continue
        assert abs(float(best['z']) - ref(c, cons)) < 1e-7
        return c, cons
    raise RuntimeError

def rounding_text(c, cons, x, best):
    cand = []
    for a in {math.floor(x[0]), math.ceil(x[0])}:
        for b in {math.floor(x[1]), math.ceil(x[1])}:
            feas = all(p * a + q * b <= r for p, q, r in cons) and a >= 0 and b >= 0
            cand.append(((a, b), feas, c[0] * a + c[1] * b))
    rows = ''.join(f'<li>({a}; {b}): {"factible" if f else "<b>infactible</b>"}{", Z = %d" % z if f else ""}</li>' for (a, b), f, z in sorted(cand))
    fz = [z for _, f, z in cand if f]
    bestr = max(fz) if fz else None
    msg = ('Ningún redondeo es factible.' if bestr is None else
           (f'El mejor redondeo da Z = {bestr}' + (' y coincide con el óptimo entero.' if bestr == best['z'] else f', pero el óptimo entero es Z = {dec(best["z"])}: <b>redondear no asegura el óptimo</b>.')))
    return f'<p>Redondeos de la solución de la RL:</p><ul>{rows}</ul><p>{msg}</p>'

def solution(c, cons, parts=('rl', 'bb')):
    x, z, v, _ = lp2(c, cons)
    nodes, best = branch_and_bound(c, cons)
    s = ''
    if 'rl' in parts:
        s += ('<div class="solpart"><h5>Relajación lineal (método gráfico)</h5><p>Se grafican las restricciones como igualdades, se sombrea la región factible y se evalúa Z en cada vértice:</p>'
              + svg_graph(c, cons, mark=x, intopt=(best['x'][0], best['x'][1]) if 'bb' in parts else None)
              + vertex_table(c, cons)
              + f'<p>Óptimo de la RL: x<sub>1</sub> = {fr(x[0])} ≈ {dec(x[0])}, x<sub>2</sub> = {fr(x[1])} ≈ {dec(x[1])}, Z = {fr(z)} ≈ <b>{dec(z)}</b>. Es una <b>cota superior</b> para el problema entero.</p></div>')
    if 'round' in parts:
        s += '<div class="solpart"><h5>¿Sirve redondear?</h5>' + rounding_text(c, cons, x, best) + '</div>'
    if 'bb' in parts:
        s += ('<div class="solpart"><h5>Branch and Bound</h5><p>Se ramifica la primera variable fraccionaria (x<sub>1</sub> antes que x<sub>2</sub>), explorando primero la rama ≤. Cada nodo se resuelve gráficamente agregando su restricción.</p>'
              + tree_html(nodes)
              + f'<p><b>Óptimo entero:</b> x<sub>1</sub> = {best["x"][0]}, x<sub>2</sub> = {best["x"][1]}, Z = <b>{dec(best["z"])}</b> (nodo {best["label"]}). Gap = {dec(z)} − {dec(best["z"])} = {dec(z - best["z"])}.</p></div>')
    return s

def exercise(c, cons, parts=('rl', 'bb'), pre=''):
    qs = []
    if 'rl' in parts: qs.append('Resuelva la relajación lineal mediante el método gráfico.')
    if 'round' in parts: qs.append('¿Se obtiene el óptimo entero redondeando la solución de la relajación? Justifique.')
    if 'bb' in parts: qs.append('Resuelva el problema entero mediante Branch and Bound (muestre el árbol).')
    L = 'abc'
    q = pre + '<p>Considere el modelo de programación lineal entera:</p>' + model(c, cons) + '<ol class="parts">' + ''.join(f'<li><b>{L[i]})</b> {t}</li>' for i, t in enumerate(qs)) + '</ol>'
    return {'q': q, 's': solution(c, cons, parts)}

CL = {}
CL[1] = '''<h4>Programación lineal entera (PLE)</h4>
<ul><li><b>PLE</b>: todas las variables enteras. <b>PLEM</b>: mixto. <b>Binario</b>: variables 0-1.</li>
<li>La <b>relajación lineal (RL)</b> es el mismo modelo sin la condición de entero. En un Max, su Z es una <b>cota superior</b> del Z entero.</li>
<li>Redondear la RL <b>no asegura</b> el óptimo (puede ser infactible o no óptimo). Por eso se usa Branch and Bound.</li></ul>
<h4>Método gráfico (repaso)</h4>
<ol><li>Dibuja cada restricción como recta (busca los cortes con los ejes).</li>
<li>Sombrea el lado que cumple (prueba con el (0;0) si no pasa por él).</li>
<li>Calcula los vértices resolviendo los sistemas de 2 rectas.</li>
<li>Evalúa Z en cada vértice: el mayor es el óptimo (Max).</li></ol>
<p class="tip">En el certamen dibuja con regla y escala clara; marca la solución de la RL y, después, la entera.</p>'''
CL[2] = '''<h4>Branch and Bound (ramificación y acotamiento)</h4>
<ol><li>Resuelve la RL (nodo P0). Si es entera, terminaste.</li>
<li>Elige una variable fraccionaria x<sub>j</sub> = 3,4 y crea dos subproblemas: <b>x<sub>j</sub> ≤ 3</b> y <b>x<sub>j</sub> ≥ 4</b>. La franja 3 &lt; x<sub>j</sub> &lt; 4 no tiene enteros, así que no se pierde nada.</li>
<li>Resuelve cada subproblema gráficamente (misma región + la nueva restricción).</li>
<li>Un nodo se <b>poda</b> (no se ramifica más) si:<ul><li>es <b>infactible</b>,</li><li>su solución es <b>entera</b> → candidata (incumbente si es la mejor),</li><li>su Z ≤ Z de la incumbente (<b>poda por cota</b>).</li></ul></li>
<li>Al no quedar nodos abiertos, la incumbente es el óptimo.</li></ol>
<p>En cada nodo escribe x<sub>1</sub>, x<sub>2</sub> y Z, y sobre cada rama la restricción agregada.</p>'''
CL[3] = '''<h4>Podas y orden de exploración</h4>
<ul><li>Aquí exploramos primero la rama ≤ y en profundidad. El óptimo no depende del orden; la cantidad de nodos sí.</li>
<li><b>Cota con coeficientes enteros</b>: si los c<sub>j</sub> son enteros, el Z entero es entero, así que un nodo con Z = 25,5 puede dar como máximo 25. Si la incumbente ya tiene 25, ese nodo se poda.</li>
<li>Un nodo hijo nunca tiene Z mayor que su padre.</li>
<li><b>Gap</b> = Z(RL) − Z(entero): lo que se "pierde" por exigir enteros.</li></ul>'''
CL[4] = '''<h4>Casos que aparecen en certámenes</h4>
<ul><li>Restricciones con coeficientes negativos (−2x<sub>1</sub> + 3x<sub>2</sub> ≤ 0 pasa por el origen) o del tipo −x<sub>2</sub> ≤ −1 (es x<sub>2</sub> ≥ 1).</li>
<li>Varias soluciones enteras con el mismo Z: indícalo.</li>
<li>Ramas que llegan a un punto entero en el borde: igual se verifica que sea factible en todas las restricciones.</li></ul>'''
CL[5] = '''<p><b>Mini-certamen de Branch and Bound.</b> 3 problemas completos (gráfico + árbol). 25 minutos cada uno.</p>'''

def build():
    days = []
    rng = random.Random(42)
    E = []
    meta = [
        ([6, 5], [(4, 3, 19), (3, 4, 18)], 'Basado en el ejemplo del apunte "Optimización lineal entera" (RL: x<sub>1</sub> ≈ 3,14, x<sub>2</sub> ≈ 2,14, Z ≈ 29,57).'),
        ([2, 3], [(1, 2, 7), (-2, 2, 5), (10, 9, 45)], 'Problema 2 del C2 2026-1 (Prof. Obreque).'),
        ([1, 1], [(6, -6, 9), (1, 6, 18)], 'Problema 1 del C2 2023-1.'),
        ([2, 4], [(0, -1, -1), (-2, 3, 0), (2, 3, 15)], 'Problema 1 de la Ayudantía 5 (2026-1). Tiene dos óptimos enteros.'),
        ([6, 3], [(-1, 0, 2), (3, -2, 0), (3, 2, 15)], 'Problema 2 de la Ayudantía 5 / Test 08 2026-1. Fíjate en la poda por cota con Z múltiplo de 3.'),
    ]
    for c, cons, intro in meta:
        e = exercise(c, cons)
        assert abs(float(branch_and_bound(c, cons)[1]['z']) - ref(c, cons)) < 1e-7
        e['intro'] = intro
        E.append(e)
    def gx(n, parts=('rl', 'bb'), **kw):
        return [exercise(*gen(rng, **kw), parts=parts) for _ in range(n)]
    days.append({'clase': CL[1], 'ejemplos': [E[0]], 'ejercicios': gx(3, parts=('rl', 'round'), min_nodes=3, max_nodes=11)})
    days.append({'clase': CL[2], 'ejemplos': [E[1]], 'ejercicios': gx(3, min_nodes=3, max_nodes=5)})
    days.append({'clase': CL[3], 'ejemplos': [E[2]], 'ejercicios': gx(3, min_nodes=5, max_nodes=7)})
    days.append({'clase': CL[4], 'ejemplos': [E[3], E[4]], 'ejercicios': gx(2, min_nodes=5, max_nodes=9, ncons=3) + [exercise([6, 5], [(2, 3, 20), (11, 9, 70)], pre='<p class="src">Problema 1 del C2 2022-2.</p>')]})
    days.append({'clase': CL[5], 'ejemplos': [], 'ejercicios': [exercise([5, 4], [(1, 2, 12), (2, 1, 8)], pre='<p class="src">Basado en el Problema 1 del C2 2024-1.</p>')] + gx(2, min_nodes=7, max_nodes=11)})
    return days

if __name__ == '__main__':
    d = build()
    json.dump(d, open('bb_days.json', 'w'))
    print([(len(x['ejemplos']), len(x['ejercicios'])) for x in d])
