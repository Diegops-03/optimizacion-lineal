import json, random
from fractions import Fraction as F
from transport import *
from content_tr import data_table, solve_html
from core import fr, table
from scipy.optimize import linprog

def tb_table(rows, cols, cost):
    """rows: [(label, supply_str, supply_val)], cols: [(label, dem_str, dem_val)], cost(rlabel, clabel)->num|'M'"""
    C = [[Mn.of(cost(r[0], c[0])) for c in cols] for r in rows]
    S = sum(F(r[2]) for r in rows); D = sum(F(c[2]) for c in cols)
    assert S == D, (S, D)
    h = ['<div class="tw"><table class="t tb"><thead><tr><th></th>' + ''.join(f'<th>{c[0]}</th>' for c in cols) + '<th>Oferta</th></tr></thead><tbody>']
    for i, r in enumerate(rows):
        h.append(f'<tr><th>{r[0]}</th>' + ''.join(f'<td>{C[i][j]}</td>' for j in range(len(cols))) + f'<td class="sd">{r[1]}</td></tr>')
    h.append('<tr><th>Demanda</th>' + ''.join(f'<td class="sd">{c[1]}</td>' for c in cols) + f'<td class="sd">{fr(S)}</td></tr></tbody></table></div>')
    return ''.join(h), C, [F(r[2]) for r in rows], [F(c[2]) for c in cols]

def network_lp(nodes, arcs, M=10**6):
    """nodes: {name: net} (supply positive, demand negative); must balance. arcs {(u,v): cost}"""
    names = list(nodes); idx = {n: k for k, n in enumerate(names)}
    A = list(arcs)
    c = [Mn.of(arcs[a]).val(M) for a in A]
    Aeq = []; beq = []
    for n in names:
        Aeq.append([(1 if a[0] == n else 0) - (1 if a[1] == n else 0) for a in A]); beq.append(float(nodes[n]))
    r = linprog(c, A_eq=Aeq, b_eq=beq, method='highs')
    return r.fun

def table_lp(C, sup, dem):
    return lp_check(C, sup, dem)

def arcs_html(arcs, nodes=None):
    rows = [[f'{u} → {v}', str(Mn.of(c))] for (u, v), c in arcs.items()]
    return table(['Arco', 'Costo'], rows)

def make_tb(origins, dests, trans, arcs, fic_cost=None, enun='', parts=None, extra_note=''):
    """origins {name: supply}, dests {name: demand}, trans {name: (o, d)}, arcs {(u,v): c}.
    Builds professor-style table: rows = origins + trans (+Fic), cols = trans + dests (+Fic)."""
    S = sum(origins.values()) + sum(o for o, d in trans.values())
    D = sum(dests.values()) + sum(d for o, d in trans.values())
    B = max(S, D)
    rows = [(o, str(s), s) for o, s in origins.items()]
    rows += [(t, f'{o}+{B}', o + B) for t, (o, d) in trans.items()]
    cols = [(t, f'{d}+{B}', d + B) for t, (o, d) in trans.items()]
    cols += [(dn, str(d), d) for dn, d in dests.items()]
    fic_cost = fic_cost or {}
    note = f'Oferta total = {S}, demanda total = {D}. B = {B}. '
    if S > D:
        cols.append(('Fic', str(S - D), S - D)); note += f'Sobra oferta: destino ficticio con {S - D}.'
    elif D > S:
        rows.insert(len(origins), ('Fic', str(D - S), D - S)); note += f'Falta oferta: origen ficticio con {D - S}.'
    def cost(r, c):
        if r == c: return 0
        if r == 'Fic':
            return fic_cost.get(c, 'M')
        if c == 'Fic':
            return fic_cost.get(r, 0 if r in origins or (r in trans and trans[r][0] > 0) else 'M')
        return arcs.get((r, c), 'M')
    th, C, sup, dem = tb_table(rows, cols, cost)
    # verify with network LP
    nodes = {n: s for n, s in origins.items()}
    nodes.update({n: -d for n, d in dests.items()})
    nodes.update({n: o - d for n, (o, d) in trans.items()})
    arcs2 = dict(arcs)
    if S > D:
        nodes['Fic'] = -(S - D)
        for r, _, _ in rows:
            if r != 'Fic':
                arcs2[(r, 'Fic')] = cost(r, 'Fic')
    elif D > S:
        nodes['Fic'] = D - S
        for c, _, _ in cols:
            if c != 'Fic':
                arcs2[('Fic', c)] = cost('Fic', c)
    zt = table_lp(C, sup, dem); zn = network_lp(nodes, arcs2)
    assert abs(zt - zn) < 1e-6, (zt, zn)
    sol = (f'<div class="solpart"><h5>Clasificación de nodos</h5><p>Orígenes puros: {", ".join(origins) or "—"}. Destinos puros: {", ".join(dests) or "—"}. Transbordo: {", ".join(trans) or "—"}.</p><p>{note}</p>'
           f'<p>Filas = orígenes puros + transbordo; columnas = transbordo + destinos puros. Transbordo: oferta o<sub>i</sub> + B y demanda d<sub>i</sub> + B, costo 0 consigo mismo, M donde no hay arco.</p></div>'
           f'<div class="solpart"><h5>Tabla de transporte</h5>{th}{extra_note}</div>')
    return sol, C, sup, dem, rows, cols, zt

CL = {}
CL[1] = '''<h4>Problema de transbordo</h4>
<p>Las unidades pueden pasar por nodos intermedios antes de llegar al destino. Se transforma en un problema de transporte:</p>
<ol><li>Clasifica los nodos: <b>origen puro</b> (solo envía), <b>destino puro</b> (solo recibe), <b>transbordo</b> (envía y recibe; puede tener oferta o demanda propia).</li>
<li><b>Balancea</b> (ficticio) y calcula <b>B</b> = total de unidades que circulan (oferta total, o demanda total si es mayor).</li>
<li>Filas: orígenes puros + nodos de transbordo. Columnas: nodos de transbordo + destinos puros.</li>
<li>Nodo de transbordo i: oferta = o<sub>i</sub> + B, demanda = d<sub>i</sub> + B.</li>
<li>Costos: c<sub>ii</sub> = 0; sin arco directo ⇒ <b>M</b>.</li></ol>
<p class="tip">B es un "colchón": el envío del nodo a sí mismo (celda c<sub>ii</sub> = 0) absorbe lo que no transita por ahí.</p>'''
CL[2] = '''<h4>Casos especiales que piden en el C2</h4>
<ul><li><b>Sitio intermedio con costo de paso</b>: el costo de pasar se suma a los arcos que llegan (o salen) del sitio. Si hay costo de fabricación, se suma en las filas de cada planta.</li>
<li><b>% mínimo de demanda</b> ("al menos el 80%"): divide al cliente en dos columnas, la parte obligatoria (M desde el ficticio) y el resto (0 o multa desde el ficticio).</li>
<li><b>"A lo más el 10% puede quedar en bodega"</b>: divide al origen en dos filas, una que debe enviarse (M al ficticio) y otra que puede quedarse (0 o costo de almacenaje).</li>
<li><b>Máximo de unidades por una ruta</b> (p. ej. "máximo 10 de la planta 3 al cliente 2"): divide el origen en una parte que puede usar esa ruta y otra con M en esa ruta.</li>
<li><b>Planta que sirve de paso</b> (envíos P1→P2): esa planta pasa a ser nodo de transbordo con oferta propia + B.</li></ul>'''
CL[3] = '''<p><b>Mini-certamen de transbordo.</b> Construye las tablas sin resolver, como en la parte (d) del problema de transporte del C2. 15 minutos cada una.</p>'''

def ex_from(sol, enun, parts):
    L = 'abcdef'
    q = enun + '<ol class="parts">' + ''.join(f'<li><b>{L[i]})</b> {t}</li>' for i, t in enumerate(parts)) + '</ol>'
    return {'q': q, 's': sol}

def build():
    days = []
    # ---- Ejemplo TB1 Maderas ----
    origins = {'Constitución': 150, 'Linares': 200}; dests = {'Curicó': 130, 'S. Fernando': 130}
    trans = {'S. Javier': (0, 0), 'Talca': (0, 0)}
    arcs = {('Constitución', 'S. Javier'): 8, ('Constitución', 'Talca'): 14, ('Constitución', 'Curicó'): 16, ('Constitución', 'S. Fernando'): 18,
            ('Linares', 'S. Javier'): 9, ('Linares', 'Talca'): 7, ('Linares', 'Curicó'): 16, ('Linares', 'S. Fernando'): 13,
            ('S. Javier', 'Talca'): 4, ('S. Javier', 'Curicó'): 8, ('S. Javier', 'S. Fernando'): 9,
            ('Talca', 'S. Javier'): 10, ('Talca', 'Curicó'): 3, ('Talca', 'S. Fernando'): 5}
    sol, C, sup, dem, rows, cols, zt = make_tb(origins, dests, trans, arcs)
    h, final, red = solve_html(C, sup, dem, [r[0] for r in rows], [c[0] for c in cols], method='V', show_multi=False, show_iters=False)
    sol += '<div class="solpart"><h5>Solución óptima</h5>' + h + '<p>Lectura: las celdas S. Javier→S. Javier y Talca→Talca con valor B − (lo que pasa) indican cuánto <b>no</b> transita por ese nodo.</p></div>'
    enun = ('<p>Maderas S.A. tiene aserraderos en Constitución (150 m³/día) y Linares (200 m³/día). Los clientes de Curicó y San Fernando requieren 130 m³ cada uno. Se puede enviar pasando por Talca o San Javier. Costos ($/m³):</p>'
            + table(['', 'S. Javier', 'Talca', 'Curicó', 'S. Fernando'], [['Constitución', '8', '14', '16', '18'], ['Linares', '9', '7', '16', '13'], ['S. Javier', '0', '4', '8', '9'], ['Talca', '10', '0', '3', '5']])
            + '<p class="src">Ejemplo final del apunte "Algoritmo de Transporte-Transbordo".</p>')
    TB1 = ex_from(sol, enun, ['Construya la red y la tabla de transporte.', 'Encuentre la solución óptima.'])
    TB1['intro'] = 'Ejemplo completo del apunte: clasificación de nodos, B, tabla y solución.'
    # ---- D19 exercises ----
    d19 = []
    o2 = {'1': 10, '5': 6, '6': 4}
    # locales network: nodes 1..7; 1 origin pure? In apunte table rows: 1,Fic,2,3,4,5,6 ; cols 2..7
    arcsL = {('1', '2'): 35, ('1', '3'): 15, ('1', '4'): 45, ('2', '5'): 5, ('3', '2'): 20, ('3', '5'): 10, ('3', '6'): 5, ('4', '3'): 1,
             ('5', '3'): 10, ('5', '6'): 5, ('5', '7'): 20, ('6', '4'): 8, ('6', '5'): 5, ('6', '7'): 10}
    sol, C, sup, dem, rows, cols, zt = make_tb({'1': 10}, {'7': 9}, {'2': (0, 8), '3': (0, 5), '4': (0, 0), '5': (6, 0), '6': (4, 0)}, arcsL,
                                               fic_cost={'2': 0, '3': 0, '7': 0})
    h, final, red = solve_html(C, sup, dem, [r[0] for r in rows], [c[0] for c in cols], method='V', show_multi=False, show_iters=False)
    sol += '<div class="solpart"><h5>Solución óptima</h5>' + h + '</div>'
    d19.append(ex_from(sol, '<p>Una empresa redistribuye artículos entre sus locales. Sobran 10, 6 y 4 unidades en los locales 1, 5 y 6; faltan 8, 5 y 9 en los locales 2, 3 y 7. Arcos disponibles (costo por unidad):</p>' + arcs_html(arcsL)
                       + '<p>Al faltar oferta, da lo mismo qué local queda con faltante.</p><p class="src">Problema de transbordo del apunte del profesor.</p>',
                       ['Clasifique los nodos y construya la tabla de transporte.', 'Encuentre la solución óptima.']))
    rng = random.Random(77)
    for k in range(2):
        for _ in range(500):
            o = {'P1': rng.randint(3, 8) * 10, 'P2': rng.randint(3, 8) * 10}
            dd = {'C1': rng.randint(2, 6) * 10, 'C2': rng.randint(2, 6) * 10}
            t = {'H': (0, 0)} if k == 0 else {'C1': (0, dd.pop('C1'))}
            if k == 1:
                dd['C3'] = rng.randint(2, 6) * 10
            S = sum(o.values()); D = sum(dd.values()) + sum(x[1] for x in t.values())
            if S < D: continue
            if k == 0:
                ar = {('P1', 'H'): rng.randint(2, 5), ('P2', 'H'): rng.randint(2, 5), ('H', 'C1'): rng.randint(2, 6), ('H', 'C2'): rng.randint(2, 6),
                      ('P1', 'C1'): rng.randint(7, 14), ('P2', 'C2'): rng.randint(7, 14)}
                desc = '<p>Las plantas P1 y P2 producen {} y {} unidades. Los clientes C1 y C2 requieren {} y {}. Se puede enviar directo (solo P1→C1 y P2→C2) o pasando por la bodega H.</p>'.format(o['P1'], o['P2'], dd['C1'], dd['C2'])
            else:
                ar = {('P1', 'C1'): rng.randint(3, 8), ('P2', 'C1'): rng.randint(3, 8), ('P1', 'C2'): rng.randint(6, 12), ('P2', 'C3'): rng.randint(6, 12),
                      ('C1', 'C2'): rng.randint(1, 4), ('C1', 'C3'): rng.randint(1, 4)}
                desc = '<p>Las plantas P1 y P2 producen {} y {} unidades. Los clientes C1, C2 y C3 requieren {}, {} y {}. El cliente C1 también puede reenviar unidades a C2 y C3.</p>'.format(o['P1'], o['P2'], t['C1'][1], dd['C2'], dd['C3'])
            try:
                sol, C, sup, dem, rows, cols, zt = make_tb(o, dd, t, ar)
                h, final, red = solve_html(C, sup, dem, [r[0] for r in rows], [c[0] for c in cols], method='V', show_multi=False, show_iters=False)
            except Exception as e:
                continue
            sol += '<div class="solpart"><h5>Solución óptima</h5>' + h + '</div>'
            d19.append(ex_from(sol, desc + '<p>Arcos disponibles:</p>' + arcs_html(ar), ['Clasifique los nodos, calcule B y construya la tabla de transporte.', 'Encuentre la solución óptima.']))
            break
    days.append({'clase': CL[1], 'ejemplos': [TB1], 'ejercicios': d19})

    # ---- D20 ----
    # TB2: C2 2025-1 b and c (original costs)
    rowsb = [('A', '230', 230), ('B', '270', 270), ('Fic', '50', 50)]
    colsb = [('C1', '150', 150), ('C2 (80%)', '160', 160), ("C2'", '40', 40), ('C3 (50%)', '100', 100), ("C3'", '100', 100)]
    base = {'A': [11, 12, 12, 8, 8], 'B': [8, 9, 9, 8, 8]}
    def cb(r, c):
        j = [x[0] for x in colsb].index(c)
        if r == 'Fic': return ['M', 'M', 0, 'M', 0][j]
        return base[r][j]
    thb, Cb, sb, db = tb_table(rowsb, colsb, cb)
    rowsc = [('Sitio C', '0+550', 550), ('A', '230', 230), ('B', '270', 270), ('Fic', '50', 50)]
    colsc = [('Sitio C', '0+550', 550)] + colsb
    cC = {'Sitio C': [0, 2, 3, 3, 1, 1], 'A': [3 + 3 + 2, 11, 12, 12, 8, 8], 'B': [2 + 4 + 2, 8, 9, 9, 8, 8], 'Fic': ['M', 'M', 'M', 0, 'M', 0]}
    thc, Cc, sc, dc = tb_table(rowsc, colsc, lambda r, c: cC[r][[x[0] for x in colsc].index(c)])
    zb, zc = lp_check(Cb, sb, db), lp_check(Cc, sc, dc)
    enun = ('<p>Las plantas A y B producen 230 y 270 unidades; fabricar cuesta $3 en A y $2 en B. Clientes: C1 150, C2 200, C3 200. Transporte:</p>'
            + data_table(C_([[8, 9, 5], [6, 7, 6]]), [230, 270], [150, 200, 200], ['A', 'B'], ['C1', 'C2', 'C3'])
            + '<p>(b) C1 es Premium: se satisface toda su demanda; a C2 al menos el 80%; a C3 al menos el 50%. (c) Con lo mismo de (b), existe un sitio C que recibe desde las plantas y reenvía a los clientes; pasar por C cuesta $2 por unidad. A→C $3, B→C $4; C→C1, C2, C3: $2, $3, $1.</p><p class="src">C2 2025-1, Problema 2 b) y c).</p>')
    sol = (f'<div class="solpart"><h5>b)</h5><p>Costo de celda = fabricación + transporte. Oferta 500 &lt; demanda 550 ⇒ ficticio con 50. C2 se divide en 160 obligatorias (80%) + 40; C3 en 100 + 100. Desde el ficticio: M a C1, a C2 (80%) y a C3 (50%); 0 a las partes opcionales.</p>{thb}<p class="chk">Comprobación: el costo mínimo de esta tabla es {fr(F(round(zb)))}.</p></div>'
           f'<div class="solpart"><h5>c)</h5><p>El sitio C es nodo de transbordo: oferta 0 + B y demanda 0 + B, con B = 550. Costo planta→C = fabricación + transporte + paso (A: 3+3+2 = 8; B: 2+4+2 = 8).</p>{thc}<p class="chk">Comprobación: costo mínimo {fr(F(round(zc)))} (menor o igual que en b, porque hay más rutas).</p></div>')
    TB2 = ex_from(sol, enun, ['Construya la tabla con los requerimientos de satisfacción (sin resolver).', 'Construya la tabla agregando el sitio intermedio C (sin resolver).'])
    TB2['intro'] = 'Así lo resolvió la pauta (ver también Test 09/10 de Linfati): porcentajes mínimos ⇒ dividir columnas; sitio intermedio ⇒ nodo de transbordo con B.'
    d20 = []
    # 2024-1 e, f
    re_ = [('P1', '12', 12), ('P2', '13', 13), ("P3'", '10', 10), ("P3''", '5', 5)]
    ce_ = [('C1', '18', 18), ('C2', '20', 20), ('Fic', '2', 2)]
    ve = {'P1': [3, 5, 0], 'P2': [3, 8, 0], "P3'": [7, 4, 0], "P3''": [7, 'M', 0]}
    the, Ce, se, de = tb_table(re_, ce_, lambda r, c: ve[r][[x[0] for x in ce_].index(c)])
    rf = [('P1', '12', 12), ('P2', '13+40', 53), ('P3', '15', 15)]
    cf = [('P2', '40', 40), ('C1', '18', 18), ('C2', '20', 20), ('Fic', '2', 2)]
    vf = {'P1': [2, 3, 5, 0], 'P2': [0, 3, 8, 0], 'P3': [1, 7, 4, 0]}
    thf, Cf, sf, df = tb_table(rf, cf, lambda r, c: vf[r][[x[0] for x in cf].index(c)])
    nodes = {'P1': 12, 'P2': 13, 'P3': 15, 'C1': -18, 'C2': -20, 'Fic': -2}
    arcsf = {('P1', 'P2'): 2, ('P3', 'P2'): 1, ('P1', 'C1'): 3, ('P1', 'C2'): 5, ('P2', 'C1'): 3, ('P2', 'C2'): 8, ('P3', 'C1'): 7, ('P3', 'C2'): 4, ('P1', 'Fic'): 0, ('P2', 'Fic'): 0, ('P3', 'Fic'): 0}
    assert abs(network_lp(nodes, arcsf) - lp_check(Cf, sf, df)) < 1e-6
    d20.append(ex_from(
        f'<div class="solpart"><h5>a)</h5><p>Oferta 40 &gt; demanda 38 ⇒ destino ficticio 2 (costo 0). P3 se divide: P3\' (10 unidades, puede ir a C2) y P3\'\' (5 unidades, M hacia C2). Así C2 recibe a lo más 10 de P3.</p>{the}<p class="chk">Costo mínimo de la tabla: {fr(F(round(lp_check(Ce, se, de))))}.</p></div>'
        f'<div class="solpart"><h5>b)</h5><p>P2 pasa a ser nodo de transbordo: fila con 13 + B y columna con 0 + B (B = 40). P1→P2 = 2, P3→P2 = 1, P2→P2 = 0. P1 y P3 no reciben: no son columnas.</p>{thf}<p class="chk">Costo mínimo: {fr(F(round(lp_check(Cf, sf, df))))} (verificado contra el modelo de red).</p></div>',
        '<p>Plantas P1, P2, P3 producen 12, 13 y 15. Clientes C1 y C2 demandan 18 y 20. Costos:</p>' + data_table(C_([[3, 5], [3, 8], [7, 4]]), [12, 13, 15], [18, 20], ['P1', 'P2', 'P3'], ['C1', 'C2']) + '<p class="src">C2 2024-1, Problema 2 e) y f).</p>',
        ['El cliente 2 acepta como máximo 10 unidades de la planta 3. Construya la tabla.', 'Sin lo anterior, las unidades de P1 y P3 pueden ir a los clientes pasando por P2 (P1→P2 $2, P3→P2 $1). Construya la tabla.']))
    # 2023-1 b, c
    rb = [('A', '50', 50), ("B (obligatorio)", '63', 63), ("B (hasta 10%)", '7', 7), ('C', '40', 40)]
    cbb = [('Alm. 1', '80', 80), ('Alm. 2', '60', 60), ('Fic', '20', 20)]
    vb = {'A': [10, 20, 4], 'B (obligatorio)': [18, 11, 'M'], 'B (hasta 10%)': [18, 11, 3], 'C': [12, 20, 5]}
    thb2, _, _, _ = tb_table(rb, cbb, lambda r, c: vb[r][[x[0] for x in cbb].index(c)])
    rc = [('A', '50+160', 210), ('B', '70+160', 230), ('C', '40', 40)]
    ccc = [('A', '160', 160), ('B', '160', 160), ('Alm. 1', '80', 80), ('Alm. 2', '60', 60), ('Fic', '20', 20)]
    vc = {'A': [0, 'M', 10, 20, 4], 'B': [5, 0, 18, 11, 3], 'C': ['M', 2, 12, 20, 5]}
    thc2, Cc2, sc2, dc2 = tb_table(rc, ccc, lambda r, c: vc[r][[x[0] for x in ccc].index(c)])
    nodes = {'A': 50, 'B': 70, 'C': 40, 'Alm1': -80, 'Alm2': -60, 'Fic': -20}
    arcs3 = {('B', 'A'): 5, ('C', 'B'): 2, ('A', 'Alm1'): 10, ('A', 'Alm2'): 20, ('B', 'Alm1'): 18, ('B', 'Alm2'): 11, ('C', 'Alm1'): 12, ('C', 'Alm2'): 20, ('A', 'Fic'): 4, ('B', 'Fic'): 3, ('C', 'Fic'): 5}
    assert abs(network_lp(nodes, arcs3) - lp_check(Cc2, sc2, dc2)) < 1e-6
    d20.append(ex_from(
        f'<div class="solpart"><h5>a)</h5><p>A lo más 10% de 70 = 7 t de B pueden quedar en bodega. B se divide en 63 t que deben enviarse (M al ficticio) y 7 t que pueden quedarse (costo 3). Oferta 160, demanda 140 ⇒ ficticio 20.</p>{thb2}</div>'
        f'<div class="solpart"><h5>b)</h5><p>A y B reciben (de B y de C) y envían: son transbordo. C solo envía. B = 160. A→B y C→A no existen ⇒ M.</p>{thc2}<p class="chk">Costo mínimo: {fr(F(round(lp_check(Cc2, sc2, dc2))))} (verificado contra el modelo de red).</p></div>',
        '<p>Fábricas A, B, C producen 50, 70 y 40 t. Almacenes 1 y 2 reciben 80 y 60 t. Cada tonelada no enviada cuesta 4, 3 y 5. Costos:</p>' + data_table(C_([[10, 20], [18, 11], [12, 20]]), [50, 70, 40], [80, 60], ['A', 'B', 'C'], ['Alm. 1', 'Alm. 2']) + '<p class="src">C2 2023-1, Problema 3 b) y c).</p>',
        ['A lo más el 10% de lo fabricado en B puede quedar en bodega. Construya la tabla.', 'Se puede enviar de B a A ($5/t) y de C a B ($2/t). Construya la tabla.']))
    # 2023-2 c
    r3 = [('A', '150', 150), ('B', '200', 200), ('C', '250', 250), ('Fic', '200', 200), ('Cl3', '0+800', 800)]
    c3 = [('Cl1', '150', 150), ('Cl2', '150', 150), ('Cl3', '400+800', 1200), ('Cl4', '100', 100)]
    v3 = {'A': [25, 29, 27, 28], 'B': [23, 24, 28, 26], 'C': [24, 21, 22, 23], 'Fic': [32, 30, 33, 34], 'Cl3': [2, 'M', 0, 3]}
    th3, C3, s3, d3 = tb_table(r3, c3, lambda r, c: v3[r][[x[0] for x in c3].index(c)])
    d20.append(ex_from(
        f'<div class="solpart"><h5>Tabla</h5><p>Costos = fabricación + transporte. Oferta 600 &lt; demanda 800 ⇒ ficticio de 200 que cobra la multa de cada cliente. Cl3 es transbordo (recibe y reenvía): fila 0 + B y columna 400 + B, B = 800. Cl3→Cl2 no existe ⇒ M.</p>{th3}<p class="chk">Costo mínimo de la tabla: {fr(F(round(lp_check(C3, s3, d3))))}.</p></div>',
        '<p>Tres fábricas (150, 200 y 250 unid./día; costo de fabricación $4, $3, $2) abastecen a cuatro clientes (150, 150, 400 y 100). Transporte y multas:</p>'
        + table(['', 'Cl1', 'Cl2', 'Cl3', 'Cl4'], [['A', '21', '25', '23', '24'], ['B', '20', '21', '25', '23'], ['C', '22', '19', '20', '21'], ['Multa', '32', '30', '33', '34']])
        + '<p>Desde el cliente 3 también se pueden enviar unidades a los clientes 1 y 4, a $2 y $3 por unidad.</p><p class="src">C2 2023-2, Problema 1 c).</p>',
        ['Construya la tabla de transporte que resuelve el problema.']))
    days.append({'clase': CL[2], 'ejemplos': [TB2], 'ejercicios': d20})

    # ---- D21 mini certamen ----
    d21 = []
    r = [('B1', '4', 4), ('B2', '8', 8), ('Fic', '2', 2), ('A', '0+14', 14), ('C', '0+14', 14)]
    c = [('A', '7+14', 21), ('B', '4', 4), ('C', '3+14', 17)]
    v = {'B1': [3, 5, 2], 'B2': [4, 5, 3], 'Fic': [4, 'M', 3], 'A': [0, 1, 'M'], 'C': ['M', 2, 0]}
    th, Cx, sx, dx = tb_table(r, c, lambda a, b: v[a][[x[0] for x in c].index(b)])
    d21.append(ex_from(f'<div class="solpart"><h5>Tabla (igual a la pauta)</h5><p>A y C reciben y reenvían a B ⇒ transbordo, con B = 14. El ficticio mantiene las multas (4 a A, 3 a C) y M a B.</p>{th}<p class="chk">Costo mínimo: {fr(F(round(lp_check(Cx, sx, dx))))}.</p></div>',
        '<p>Mismo problema del ejemplo del 6 nov (C2 2026-1, P3): B1 = 4, B2 = 8; demandas A 7, B 4, C 3; B exige todo; multas A $4, C $3. Costos B1: 3, 5, 2; B2: 4, 5, 3.</p><p class="src">C2 2026-1, Problema 3 d).</p>',
        ['Suponga que desde los clientes A y C se pueden enviar unidades al cliente B a $1 y $2 por unidad. Construya la tabla de transporte.']))
    r = [('I (oblig.)', '20', 20), ('I (resto)', '30', 30), ('II', '20', 20), ('III', '40+110', 150), ('B', '0+110', 110)]
    c = [('A', '35', 35), ('B', '35+110', 145), ('C', '22', 22), ('III', '110', 110), ('Fic', '18', 18)]
    v = {'I (oblig.)': [10, 8, 15, 'M', 'M'], 'I (resto)': [10, 8, 15, 'M', 0], 'II': [12, 25, 5, 'M', 'M'], 'III': [20, 7, 14, 0, 0], 'B': ['M', 0, 10, 6, 'M']}
    th, Cx, sx, dx = tb_table(r, c, lambda a, b: v[a][[x[0] for x in c].index(b)])
    d21.append(ex_from(f'<div class="solpart"><h5>Tabla</h5><p>B (consumo) envía a III y a C ⇒ B y III son transbordo. B = 110. Se mantienen las exigencias: II no puede quedarse con productos (M al ficticio) y al menos 40% de I (20 t) debe salir (fila obligatoria con M al ficticio). B no puede mandar al ficticio (no tiene oferta propia) ⇒ M.</p>{th}<p class="chk">Costo mínimo: {fr(F(round(lp_check(Cx, sx, dx))))}.</p></div>',
        '<p>Centros de producción I, II, III: 50, 20 y 40 t. Consumo A, B, C: 35, 35 y 22. Costos I: 10, 8, 15; II: 12, 25, 5; III: 20, 7, 14. II debe quedar vacío y al menos el 40% de I debe transportarse.</p><p class="src">C2 2024-2, Problema 2 b).</p>',
        ['Desde el centro de consumo B se pueden enviar toneladas al centro de producción III ($6) y al centro de consumo C ($10). Construya la tabla.']))
    r = [('A', '600', 600), ('B', '400', 400), ('C', '500', 500), ('Cl3', '0+1500', 1500)]
    c = [('Cl1', '300', 300), ('Cl2', '500', 500), ('Cl3', '400+1500', 1900), ('Fic', '300', 300)]
    v = {'A': [20, 23, 21, 0], 'B': [26, 25, 21, 0], 'C': [33, 25, 29, 0], 'Cl3': ['M', 2, 0, 'M']}
    th, Cx, sx, dx = tb_table(r, c, lambda a, b: v[a][[x[0] for x in c].index(b)])
    d21.append(ex_from(f'<div class="solpart"><h5>Tabla</h5><p>Costo = producción + transporte. Cl3 recibe y reenvía a Cl2 ⇒ transbordo, B = 1500. Oferta 1500 &gt; demanda 1200 ⇒ ficticio 300 (las plantas pueden no producir: costo 0).</p>{th}<p class="chk">Costo mínimo: {fr(F(round(lp_check(Cx, sx, dx))))}.</p></div>',
        '<p>Johnson Electric (ver 7 nov): plantas A, B, C con costo de producción 17, 20, 24 y capacidad 600, 400, 500; clientes 300, 500, 400. Transporte A: 3, 6, 4; B: 6, 5, 1; C: 9, 1, 5.</p><p class="src">C2 2022-1, Problema 2 b).</p>',
        ['Desde las plantas A y B también se pueden enviar unidades al cliente 2 pasando por el cliente 3 ($2 entre cliente 3 y cliente 2). Construya la tabla.']))
    days.append({'clase': CL[3], 'ejemplos': [], 'ejercicios': d21})
    return days

if __name__ == '__main__':
    d = build()
    json.dump(d, open('tb_days.json', 'w'))
    print([(len(x['ejemplos']), len(x['ejercicios'])) for x in d])
