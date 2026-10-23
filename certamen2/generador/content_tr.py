import json, random
from fractions import Fraction as F
from transport import *
from core import fr, table

def balance(C, sup, dem, rlab, clab, fic_row=None, fic_col=None):
    """Return balanced data. fic_row: costs for fictitious origin (per column); fic_col: per row."""
    S, D = sum(map(F, sup)), sum(map(F, dem))
    C = [list(r) for r in C]; sup = list(sup); dem = list(dem); rlab = list(rlab); clab = list(clab)
    note = f'Oferta total = {fr(S)}, demanda total = {fr(D)}. '
    if S > D:
        fc = fic_col or [0] * len(sup)
        for i in range(len(C)): C[i].append(Mn.of(fc[i]))
        dem.append(S - D); clab.append('Fic')
        note += f'Sobra oferta ⇒ se agrega un <b>destino ficticio</b> con demanda {fr(S - D)}.'
    elif D > S:
        fr_ = fic_row or [0] * len(dem)
        C.append([Mn.of(x) for x in fr_]); sup.append(D - S); rlab.append('Fic')
        note += f'Falta oferta ⇒ se agrega un <b>origen ficticio</b> con oferta {fr(D - S)}.'
    else:
        note += 'El problema está balanceado.'
    return C, sup, dem, rlab, clab, note

def initial_html(method, C, sup, dem, rlab, clab):
    if method == 'NO':
        a = northwest(C, sup, dem)
        h = '<p><b>Esquina Nor-Oeste:</b> se parte en la celda (1,1), se asigna lo máximo y se avanza a la derecha o hacia abajo según se agote la demanda o la oferta.</p>'
        h += render(C, sup, dem, a, rlab=rlab, clab=clab) + f'<p>Z = {z_text(C, a)}. Celdas básicas: {len(a)} = m + n − 1 = {len(sup)}+{len(dem)}−1.</p>'
    elif method == 'MC':
        a = min_cost(C, sup, dem)
        h = '<p><b>Costo mínimo:</b> se asigna lo máximo a la celda más barata disponible, se elimina la fila o columna satisfecha y se repite.</p>'
        h += render(C, sup, dem, a, rlab=rlab, clab=clab) + f'<p>Z = {z_text(C, a)}.</p>'
    else:
        a, pr, pc, log = vogel(C, sup, dem)
        h = '<p><b>Vogel:</b> penalidad = diferencia entre los dos costos menores de cada fila y columna; en la línea con mayor penalidad se asigna a la celda más barata.</p>'
        h += '<ol class="log">' + ''.join(f'<li>{x}</li>' for x in log) + '</ol>'
        h += render(C, sup, dem, a, rlab=rlab, clab=clab, pens=(pr, pc)) + f'<p>Z = {z_text(C, a)}.</p>'
    return a, h

def solve_html(C, sup, dem, rlab, clab, method='V', show_multi=True, show_iters=True):
    a, h = initial_html(method, C, sup, dem, rlab, clab)
    final, out, red = modi(C, sup, dem, a, rlab=rlab, clab=clab)
    ref = lp_check(C, sup, dem)
    assert abs(zval(C, final).val() - ref) < 1e-6, (zval(C, final), ref)
    if show_iters:
        h += '<p><b>Algoritmo de transporte (u<sub>i</sub>, v<sub>j</sub>):</b></p>'
        for k, st in enumerate(out):
            h += f'<p class="it">Iteración {k+1}. {st["text"]}</p>' + st['table']
    else:
        h += f'<p>Tabla óptima:</p>' + out[-1]['table'] + f'<p>{out[-1]["text"]}</p>'
    h += '<p><b>Solución óptima:</b> ' + '; '.join(f'{rlab[i]} → {clab[j]}: {fr(q)}' for (i, j), q in sorted(final.items()) if q != 0) + f'. Z* = <b>{zval(C, final)}</b>.</p>'
    mult = multiple(red)
    if show_multi:
        if mult:
            e = mult[0]
            cyc = find_cycle(final, e)
            signs = {c: ('+' if k % 2 == 0 else '−') for k, c in enumerate(cyc)}
            theta = min(final[c] for c in cyc if signs[c] == '−')
            alt = dict(final)
            for c in cyc:
                if c == e: alt[c] = theta
                elif signs[c] == '+': alt[c] += theta
                else: alt[c] -= theta
            alt = {k: v for k, v in alt.items() if v != 0 or k in final}
            h += (f'<p><b>¿Soluciones múltiples?</b> Sí: la celda no básica ({rlab[e[0]]},{clab[e[1]]}) tiene costo reducido 0. Si entra (θ = {fr(theta)}) se obtiene otra solución con el mismo Z:</p>'
                  + render(C, sup, dem, {k: v for k, v in alt.items() if v != 0}, rlab=rlab, clab=clab)
                  + f'<p>Z = {z_text(C, {k: v for k, v in alt.items() if v != 0})}.</p>')
        else:
            h += '<p><b>¿Soluciones múltiples?</b> No: todos los costos reducidos de las celdas no básicas son estrictamente positivos ⇒ la solución es única.</p>'
    return h, final, red

def data_table(C, sup, dem, rlab, clab, cap=None):
    rows = [[rlab[i]] + [str(Mn.of(x)) for x in C[i]] + [fr(sup[i])] for i in range(len(C))]
    rows.append(['Demanda'] + [fr(x) for x in dem] + [''])
    return table([''] + clab + ['Oferta'], rows, caption=cap)

def gen_instance(rng, m, n, balanced=True, want_mult=None, method='V', min_it=1, max_it=3):
    for _ in range(4000):
        C = [[Mn(0, rng.randint(2, 20)) for _ in range(n)] for _ in range(m)]
        sup = [rng.randint(2, 12) * 5 for _ in range(m)]
        if balanced:
            dem = [rng.randint(2, 12) * 5 for _ in range(n - 1)]
            last = sum(sup) - sum(dem)
            if last <= 0: continue
            dem.append(last)
        else:
            dem = [rng.randint(2, 12) * 5 for _ in range(n)]
            if sum(dem) == sum(sup): continue
        Cb, sb, db, rl, cl, note = balance(C, sup, dem, [f'O{i+1}' for i in range(m)], [f'D{j+1}' for j in range(n)])
        try:
            a = vogel(Cb, sb, db)[0] if method == 'V' else (northwest(Cb, sb, db) if method == 'NO' else min_cost(Cb, sb, db))
            final, out, red = modi(Cb, sb, db, a)
        except Exception:
            continue
        its = len(out) - 1
        if not (min_it <= its <= max_it): continue
        mult = bool(multiple(red))
        if want_mult is not None and mult != want_mult: continue
        return C, sup, dem
    raise RuntimeError

def ex_transport(C, sup, dem, rlab, clab, enun, parts, method='V', fic_row=None, fic_col=None, show_multi=True, extra_sol=''):
    Cb, sb, db, rl, cl, note = balance(C_(C), sup, dem, rlab, clab, fic_row, fic_col)
    h, final, red = solve_html(Cb, sb, db, rl, cl, method=method, show_multi=show_multi)
    sol = f'<div class="solpart"><h5>Tabla de transporte</h5><p>{note}</p>' + data_table(Cb, sb, db, rl, cl) + extra_sol + '</div><div class="solpart"><h5>Solución</h5>' + h + '</div>'
    L = 'abcdef'
    q = enun + '<ol class="parts">' + ''.join(f'<li><b>{L[i]})</b> {t}</li>' for i, t in enumerate(parts)) + '</ol>'
    return {'q': q, 's': sol}

def ex_three_methods(C, sup, dem, rlab, clab, enun):
    Cb, sb, db, rl, cl, note = balance(C_(C), sup, dem, rlab, clab)
    sol = f'<p>{note}</p>'
    zs = []
    for mth, nm in [('NO', 'a'), ('MC', 'b'), ('V', 'c')]:
        a, h = initial_html(mth, Cb, sb, db, rl, cl)
        zs.append(zval(Cb, a))
        sol += f'<div class="solpart"><h5>{nm})</h5>{h}</div>'
    best = lp_check(Cb, sb, db)
    sol += f'<p>Comparación: NO = {zs[0]}, costo mínimo = {zs[1]}, Vogel = {zs[2]}. El óptimo es {fr(F(round(best)))}: Vogel suele quedar más cerca.</p>'
    q = enun + '<ol class="parts"><li><b>a)</b> SBF inicial por Esquina Nor-Oeste y su Z.</li><li><b>b)</b> SBF inicial por costo mínimo y su Z.</li><li><b>c)</b> SBF inicial por Vogel y su Z.</li></ol>'
    return {'q': q, 's': sol}

def gen_enun(C, sup, dem, rlab=None, clab=None, extra=''):
    m, n = len(C), len(C[0])
    rlab = rlab or [f'O{i+1}' for i in range(m)]; clab = clab or [f'D{j+1}' for j in range(n)]
    return f'<p>Considere el siguiente problema de transporte (costos unitarios):</p>' + data_table(C_(C), sup, dem, rlab, clab) + extra

CL = {}
CL[1] = '''<h4>El problema de transporte</h4>
<p>Enviar unidades desde m orígenes (oferta o<sub>i</sub>) a n destinos (demanda d<sub>j</sub>) al mínimo costo. x<sub>ij</sub> = unidades de i a j.</p>
<p>Min Z = ΣΣ c<sub>ij</sub>x<sub>ij</sub>; s.a. Σ<sub>j</sub> x<sub>ij</sub> = o<sub>i</sub>; Σ<sub>i</sub> x<sub>ij</sub> = d<sub>j</sub>; x<sub>ij</sub> ≥ 0. Hay <b>m + n − 1</b> variables básicas.</p>
<h4>Balancear (Paso 1 del algoritmo)</h4>
<div class="tw"><table class="t"><thead><tr><th>Caso</th><th>Se agrega</th><th>Costo en el ficticio</th></tr></thead><tbody>
<tr><th>Oferta &gt; Demanda</th><td>destino ficticio</td><td>0 si da lo mismo · costo de almacenaje/fabricación · <b>M</b> si ese origen no puede quedarse con unidades</td></tr>
<tr><th>Demanda &gt; Oferta</th><td>origen ficticio</td><td>0 · multa por unidad no enviada · <b>M</b> si el cliente exige toda su demanda</td></tr>
</tbody></table></div>
<ul><li>Ruta prohibida (puente cortado, no se desea enviar): costo <b>M</b>.</li>
<li>Si hay costos de producción por planta, se <b>suman</b> al costo de transporte de esa fila.</li></ul>'''
CL[2] = '''<h4>Soluciones básicas factibles iniciales</h4>
<ul><li><b>Esquina Nor-Oeste (NO):</b> no mira costos. Rápida pero suele quedar lejos del óptimo.</li>
<li><b>Costo mínimo:</b> asigna primero a la celda más barata.</li>
<li><b>Vogel:</b> penalidad de fila/columna = diferencia entre sus dos costos menores. Se elige la mayor penalidad y se asigna a su celda más barata. Se recalculan penalidades. Si queda una sola fila o columna, se completa con costo mínimo.</li></ul>
<p class="tip"><b>Degeneración:</b> si una asignación agota oferta y demanda a la vez, se elimina <b>solo una</b> (fila o columna) y la otra queda con saldo 0, que luego se asigna como un 0 básico. Siempre debes terminar con m + n − 1 celdas básicas.</p>'''
CL[3] = '''<h4>Algoritmo de transporte (método u-v)</h4>
<ol><li>Para cada celda básica: <b>u<sub>i</sub> + v<sub>j</sub> = c<sub>ij</sub></b>. Fija en 0 la u o v de la fila/columna con más básicas y despeja el resto.</li>
<li>Para cada no básica: <b>costo reducido = c<sub>ij</sub> − u<sub>i</sub> − v<sub>j</sub></b>.</li>
<li>Si todos son ≥ 0 ⇒ óptimo. Si no, <b>entra</b> la celda con el más negativo.</li>
<li>Circuito: parte en la celda que entra (+), se mueve en horizontal y vertical alternando solo por celdas básicas, poniendo − , +, −, …</li>
<li><b>Sale</b> la celda "−" con menor valor θ. Suma θ en las "+" y resta θ en las "−". Vuelve al paso 1.</li></ol>'''
CL[4] = '''<h4>Soluciones múltiples y degeneración</h4>
<ul><li>En la tabla óptima, si una celda <b>no básica</b> tiene costo reducido <b>0</b>, hay soluciones múltiples. Para mostrar otra, haz entrar esa celda con su circuito: Z no cambia.</li>
<li>Si una básica vale 0 (degenerada), igual cuenta como básica y se usa en u-v y en los circuitos. Si θ = 0, la iteración cambia la base pero no la solución.</li>
<li>Exigencias típicas: "el cliente B exige toda su demanda" ⇒ M desde el ficticio a B. "Multa de $4 por unidad no satisfecha" ⇒ costo 4 desde el ficticio.</li></ul>'''
CL[5] = '''<h4>Variantes de modelación</h4>
<ul><li><b>Producción + transporte:</b> costo de la celda = costo de producir en la planta + costo de enviar.</li>
<li><b>Planificación por períodos:</b> filas = (mes, tiempo normal/extra), columnas = meses de demanda. Costo = producción + almacenaje × meses guardado. Producir para un mes anterior (pedido atrasado) prohibido ⇒ M.</li>
<li><b>Maximización:</b> o se usa el criterio "entra el costo reducido más positivo", o se multiplica todo por −1 y se minimiza (el apunte muestra ambas y llegan al mismo óptimo).</li></ul>'''
CL[6] = '''<p><b>Mini-certamen de transporte.</b> 3 problemas tipo certamen: tabla balanceada, SBF inicial, óptimo y soluciones múltiples. 25 minutos cada uno.</p>'''

def build():
    rng = random.Random(2026)
    days = []
    # ---------- Ejemplos ----------
    dep_enun = ('<p>Tres depósitos abastecen a cuatro almacenes. Costos unitarios, capacidades y requerimientos:</p>'
                + data_table(C_([[2, 3, 4, 4], [4, 8, 3, 6], [6, 7, 8, 3]]), [120, 200, 150], [120, 150, 100, 80], ['A', 'B', 'C'], ['1', '2', '3', '4'])
                + '<p>Un puente dañado impide enviar de A al almacén 2 y de B al almacén 4. Cada unidad que no se transporta cuesta $2, $5 y $3 de almacenaje en A, B y C. (Ejemplo del apunte "Algoritmo de Transporte-Transbordo".)</p>')
    T1 = ex_transport([[2, 'M', 4, 4], [4, 8, 3, 'M'], [6, 7, 8, 3]], [120, 200, 150], [120, 150, 100, 80], ['A', 'B', 'C'], ['1', '2', '3', '4'],
                      dep_enun, ['Construya la tabla de transporte balanceada.', 'Encuentre una SBF inicial por Vogel.', 'Encuentre la solución óptima y diga si hay soluciones múltiples.'], fic_col=[2, 5, 3])
    T1['intro'] = 'Este ejemplo junta todo: rutas prohibidas (M), destino ficticio con costos de almacenaje, Vogel, u-v y soluciones múltiples. El profesor obtiene Z = 1990.'
    hu = [[8, 19, 22, 6], [15, 6, 16, 5], [7, 8, 9, 12]]
    hu_enun = ('<p>Una forestal envía semillas (millones) desde 3 huertos a 4 bosques. Costos proporcionales a la distancia (ejemplo del apunte):</p>' + data_table(C_(hu), [5, 1, 2], [2, 3, 2, 1], ['H1', 'H2', 'H3'], ['B1', 'B2', 'B3', 'B4']))
    T2 = ex_three_methods(hu, [5, 1, 2], [2, 3, 2, 1], ['H1', 'H2', 'H3'], ['B1', 'B2', 'B3', 'B4'], hu_enun)
    T2['intro'] = 'Las tres reglas sobre el mismo problema. El apunte obtiene NO = 110, costo mínimo = 120 y Vogel = 84.'
    T3 = ex_transport(hu, [5, 1, 2], [2, 3, 2, 1], ['H1', 'H2', 'H3'], ['B1', 'B2', 'B3', 'B4'], hu_enun,
                      ['Parta de la SBF de Esquina Nor-Oeste y encuentre la solución óptima con el algoritmo de transporte.'], method='NO', show_multi=False)
    T3['intro'] = 'Desde la Esquina NO (Z = 110) hasta el óptimo (Z = 84), mostrando u<sub>i</sub>, v<sub>j</sub>, costos reducidos y circuitos.'
    c26_enun = ('<p>Un fabricante debe enviar todas las unidades que quedan en sus bodegas B1 (4 unid.) y B2 (8 unid.) a los clientes A, B y C, que demandan 7, 4 y 3. Costos unitarios:</p>'
                + data_table(C_([[3, 5, 2], [4, 5, 3]]), [4, 8], [7, 4, 3], ['B1', 'B2'], ['A', 'B', 'C'])
                + '<p>El cliente B exige obligatoriamente toda su demanda. A y C cobran $4 y $3 por cada unidad que no se les entregue. (C2 2026-1, Problema 3.)</p>')
    T4 = ex_transport([[3, 5, 2], [4, 5, 3]], [4, 8], [7, 4, 3], ['B1', 'B2'], ['A', 'B', 'C'], c26_enun,
                      ['SBF inicial por Esquina Nor-Oeste.', 'Solución óptima con el algoritmo de transporte.', '¿Tiene soluciones múltiples? Si es así, muestre otra.'], method='NO', fic_row=[4, 'M', 3])
    T4['intro'] = 'Problema real del último C2. El ficticio cobra la multa (4 y 3) y tiene M hacia B porque B exige todo.'
    mx = [[4, 5, 8, 3, 6], [7, 3, 8, 13, 17], [7, 1, 9, 3, 7], [14, 6, 12, 8, 10]]
    mx_enun = ('<p>Resolver el problema de transporte que <b>maximiza</b> los beneficios (ejemplo del apunte "Un problema de transporte - MÁXIMO"):</p>'
               + data_table(C_(mx), [65, 75, 110, 110], [40, 80, 90, 80, 70], ['A', 'B', 'C', 'D'], ['1', '2', '3', '4', '5']))
    neg = [[-x for x in r] for r in mx]
    T5 = ex_transport(neg, [65, 75, 110, 110], [40, 80, 90, 80, 70], ['A', 'B', 'C', 'D'], ['1', '2', '3', '4', '5'], mx_enun,
                      ['Encuentre la solución que maximiza el beneficio total (transforme a minimización multiplicando por −1).'], method='V', show_multi=False)
    T5['s'] = '<p>Max Z = −Min(−Z): se cambian todos los beneficios de signo y se minimiza. Al final, el beneficio máximo es el negativo del Z obtenido.</p>' + T5['s']
    T5['intro'] = 'Maximización: el apunte obtiene un beneficio máximo de 3540.'
    # ---------- Ejercicios ----------
    d13 = []
    g2 = [[10, 20, 5, 9, 10], [3, 11, 8, 30, 5], [1, 20, 7, 10, 4]]
    d13.append(ex_transport(g2, [100, 100, 120], [40, 50, 70, 90, 90], ['A', 'B', 'C'], ['I', 'II', 'III', 'IV', 'V'],
        '<p>Una fábrica tiene tres centros de distribución A, B y C con 100, 100 y 120 toneladas. Debe entregarlas a cinco almacenes I–V que requieren 40, 50, 70, 90 y 90 toneladas. Si no se satisface la demanda, cuesta 4, 6, 6, 8 y 3 por tonelada en los almacenes I–V. Costos:</p>'
        + data_table(C_(g2), [100, 100, 120], [40, 50, 70, 90, 90], ['A', 'B', 'C'], ['I', 'II', 'III', 'IV', 'V']) + '<p class="src">Guía de transporte resuelta, Problema 2 (certamen 2013-1).</p>',
        ['Construya la tabla balanceada.', 'SBF inicial por Esquina Nor-Oeste.', 'Solución óptima.'], method='NO', fic_row=[4, 6, 6, 8, 3]))
    c231 = [[10, 20], [18, 11], [12, 20]]
    d13.append(ex_transport(c231, [50, 70, 40], [80, 60], ['A', 'B', 'C'], ['Alm. 1', 'Alm. 2'],
        '<p>Tres fábricas A, B, C producen 50, 70 y 40 toneladas. Los almacenes 1 y 2 deben recibir 80 y 60. Por cada tonelada que no se envía, las fábricas pagan 4, 3 y 5 pesos. Costos:</p>'
        + data_table(C_(c231), [50, 70, 40], [80, 60], ['A', 'B', 'C'], ['Alm. 1', 'Alm. 2']) + '<p class="src">C2 2023-1, Problema 3 a).</p>',
        ['Construya la tabla balanceada.', 'SBF inicial por Esquina Nor-Oeste y solución óptima.', '¿Hay soluciones múltiples? Justifique.'], method='NO', fic_col=[4, 3, 5]))
    C, s, d = gen_instance(rng, 3, 3, balanced=False, min_it=1, max_it=2)
    while sum(d) <= sum(s):
        C, s, d = gen_instance(rng, 3, 3, balanced=False, min_it=1, max_it=2)
    fr_row = [0, 'M', 0]
    d13.append(ex_transport([[x.b for x in r] for r in C], s, d, ['O1', 'O2', 'O3'], ['D1', 'D2', 'D3'],
        gen_enun([[x.b for x in r] for r in C], s, d, extra='<p>El destino D2 exige recibir toda su demanda; a los demás da lo mismo que les falte.</p>'),
        ['Construya la tabla balanceada.', 'SBF inicial por Vogel y solución óptima.'], method='V', fic_row=fr_row))
    days.append({'clase': CL[1], 'ejemplos': [T1], 'ejercicios': d13})
    # D14 three methods
    d14 = []
    for k in range(3):
        C, s, d = gen_instance(rng, 3, 4, balanced=True, min_it=1, max_it=3)
        Cb = [[x.b for x in r] for r in C]
        d14.append(ex_three_methods(Cb, s, d, ['O1', 'O2', 'O3'], ['D1', 'D2', 'D3', 'D4'], gen_enun(Cb, s, d)))
    days.append({'clase': CL[2], 'ejemplos': [T2], 'ejercicios': d14})
    # D15 MODI
    d15 = [ex_transport([[3, 5], [3, 8], [7, 4]], [12, 13, 15], [18, 20], ['P1', 'P2', 'P3'], ['C1', 'C2'],
        '<p>Tres plantas P1, P2, P3 producen 12, 13 y 15 unidades al mes. Los clientes C1 y C2 demandan 18 y 20. Costos unitarios:</p>' + data_table(C_([[3, 5], [3, 8], [7, 4]]), [12, 13, 15], [18, 20], ['P1', 'P2', 'P3'], ['C1', 'C2']) + '<p class="src">C2 2024-1 Problema 2 (es también la Tarea 4).</p>',
        ['Construya la tabla de transporte.', 'SBF por Vogel.', 'Solución óptima.', '¿Existen soluciones múltiples? Si es así, encuentre otra.'], method='V')]
    for k in range(2):
        C, s, d = gen_instance(rng, 3, 4, balanced=True, min_it=2, max_it=3, method='V')
        Cb = [[x.b for x in r] for r in C]
        d15.append(ex_transport(Cb, s, d, ['O1', 'O2', 'O3'], ['D1', 'D2', 'D3', 'D4'], gen_enun(Cb, s, d), ['SBF inicial por Vogel.', 'Solución óptima por el algoritmo de transporte.'], method='V', show_multi=False))
    days.append({'clase': CL[3], 'ejemplos': [T3], 'ejercicios': d15})
    # D16 multiples
    g3 = [[15, 10, 8, 10], [9, 11, 7, 5], [12, 14, 3, 14]]
    d16 = [ex_transport(g3, [200, 150, 225], [140, 130, 165, 100], ['CD1', 'CD2', 'CD3'], ['A', 'B', 'C', 'D'],
        '<p>Un laboratorio tiene 3 centros de distribución con capacidades 200, 150 y 225 cajas/semana. Las tiendas A, B, C y D piden 140, 130, 165 y 100 cajas. Costos por caja:</p>' + data_table(C_(g3), [200, 150, 225], [140, 130, 165, 100], ['CD1', 'CD2', 'CD3'], ['A', 'B', 'C', 'D']) + '<p class="src">Guía de transporte resuelta, Problema 3.</p>',
        ['SBF por Esquina Nor-Oeste.', 'Solución óptima.', '¿Es única? Justifique.'], method='NO')]
    d16.append(ex_transport([[11, 12, 8], [8, 9, 8]], [230, 270], [150, 200, 200], ['A', 'B'], ['C1', 'C2', 'C3'],
        '<p>Las plantas A y B producirán 230 y 270 unidades. Fabricar cuesta $3 en A y $2 en B. Los clientes 1, 2 y 3 demandan 150, 200 y 200. Transporte:</p>' + data_table(C_([[8, 9, 5], [6, 7, 6]]), [230, 270], [150, 200, 200], ['A', 'B'], ['C1', 'C2', 'C3']) + '<p class="src">C2 2025-1, Problema 2 a). Ojo: el costo de cada celda es fabricación + transporte.</p>',
        ['Construya la tabla (sumando el costo de fabricación).', 'Determine la solución óptima e indique si existen soluciones múltiples.'], method='V'))
    C, s, d = gen_instance(rng, 3, 3, balanced=True, want_mult=True, min_it=1, max_it=3)
    Cb = [[x.b for x in r] for r in C]
    d16.append(ex_transport(Cb, s, d, ['O1', 'O2', 'O3'], ['D1', 'D2', 'D3'], gen_enun(Cb, s, d), ['SBF por Vogel.', 'Solución óptima.', '¿Hay soluciones múltiples? Si es así, entregue otra solución óptima.'], method='V'))
    days.append({'clase': CL[4], 'ejemplos': [T4], 'ejercicios': d16})
    # D17 modelling
    je = [[17 + 3, 17 + 6, 17 + 4], [20 + 6, 20 + 5, 20 + 1], [24 + 9, 24 + 1, 24 + 5]]
    d17 = [ex_transport(je, [600, 400, 500], [300, 500, 400], ['A', 'B', 'C'], ['Cl1', 'Cl2', 'Cl3'],
        '<p>Johnson Electric produce motores en 3 plantas para 3 clientes (demandas 300, 500 y 400). Costo de producción por unidad y capacidad: A $17 (600), B $20 (400), C $24 (500). Transporte:</p>'
        + data_table(C_([[3, 6, 4], [6, 5, 1], [9, 1, 5]]), [600, 400, 500], [300, 500, 400], ['A', 'B', 'C'], ['Cl1', 'Cl2', 'Cl3']) + '<p class="src">C2 2022-1, Problema 2 a).</p>',
        ['Formule como modelo de transporte (costo = producción + transporte).', 'Encuentre la solución óptima.'], method='V')]
    reg = [100, 96, 115]; ext = [F(150), F(144), F(345, 2)]
    rows = []; sup = []; lab = []
    for mth in range(3):
        for kind, cost, cap in [('N', reg[mth], [180, 230, 430][mth]), ('E', ext[mth], [90, 115, 215][mth])]:
            rows.append(['M' if dmo < mth else cost + 4 * (dmo - mth) for dmo in range(3)]); sup.append(cap); lab.append(f'Mes{mth+1}-{kind}')
    d17.append(ex_transport(rows, sup, [200, 150, 300], lab, ['Ene', 'Feb', 'Mar'],
        '<p>La demanda de un dispositivo médico para enero, febrero y marzo es 200, 150 y 300. La capacidad normal es 180, 230 y 430; con tiempo extra se puede producir la mitad adicional. El costo normal es 100, 96 y 115; el tiempo extra cuesta 50% más. Guardar una unidad cuesta 4 por mes. No se aceptan pedidos atrasados.</p><p class="src">C2 2022-2, Problema 3.</p>',
        ['Construya la tabla de transporte (filas: mes y tipo de turno).', 'SBF inicial por Vogel.', 'Solución óptima.'], method='V', show_multi=False))
    C, s, d = gen_instance(rng, 3, 3, balanced=True, min_it=1, max_it=3)
    P = [[x.b for x in r] for r in C]
    negP = [[-x for x in r] for r in P]
    e = ex_transport(negP, s, d, ['O1', 'O2', 'O3'], ['D1', 'D2', 'D3'],
        '<p>La tabla muestra el <b>beneficio</b> por unidad enviada. Maximice el beneficio total.</p>' + data_table(C_(P), s, d, ['O1', 'O2', 'O3'], ['D1', 'D2', 'D3']),
        ['Transforme a minimización y encuentre la solución óptima.', 'Indique el beneficio máximo.'], method='V', show_multi=False)
    e['s'] = '<p>Se multiplican los beneficios por −1 y se minimiza; el beneficio máximo es −Z*.</p>' + e['s']
    d17.append(e)
    days.append({'clase': CL[5], 'ejemplos': [T5], 'ejercicios': d17})
    # D18 mini certamen
    c232 = [[4 + 21, 4 + 25, 4 + 23, 4 + 24], [3 + 20, 3 + 21, 3 + 25, 3 + 23], [2 + 22, 2 + 19, 2 + 20, 2 + 21]]
    d18 = [ex_transport(c232, [150, 200, 250], [150, 150, 400, 100], ['A', 'B', 'C'], ['Cl1', 'Cl2', 'Cl3', 'Cl4'],
        '<p>Tres fábricas (capacidad diaria 150, 200 y 250) abastecen a cuatro clientes (demanda 150, 150, 400 y 100). Costo de fabricación: A $4, B $3, C $2. Transporte y multa por unidad faltante:</p>'
        + table(['', 'Cl1', 'Cl2', 'Cl3', 'Cl4'], [['A', '21', '25', '23', '24'], ['B', '20', '21', '25', '23'], ['C', '22', '19', '20', '21'], ['Multa', '32', '30', '33', '34']]) + '<p class="src">C2 2023-2, Problema 1 a).</p>',
        ['Construya la tabla (fabricación + transporte; el ficticio cobra la multa).', 'Determine cuánto debe fabricar cada fábrica y a quién enviar.'], method='V', fic_row=[32, 30, 33, 34])]
    # 2024-2 P2a
    c242 = [[10, 8, 15], [10, 8, 15], [12, 25, 5], [20, 7, 14]]
    d18.append(ex_transport(c242, [20, 30, 20, 40], [35, 35, 22], ['I (obligatorio)', 'I (resto)', 'II', 'III'], ['A', 'B', 'C'],
        '<p>Los centros I, II y III producen 50, 20 y 40 toneladas diarias. Los centros de consumo A, B y C necesitan 35, 35 y 22. Costos:</p>'
        + data_table(C_([[10, 8, 15], [12, 25, 5], [20, 7, 14]]), [50, 20, 40], [35, 35, 22], ['I', 'II', 'III'], ['A', 'B', 'C'])
        + '<p>El centro II se cerrará: debe quedar sin productos. Al menos el 40% de las toneladas de I deben transportarse.</p><p class="src">C2 2024-2, Problema 2 a).</p>',
        ['Construya la tabla de transporte (pista: divida I en la parte obligatoria, 40% = 20 t, y el resto, 30 t).', 'Encuentre la solución óptima.'], method='V', fic_col=['M', 0, 'M', 0]))
    C, s, d = gen_instance(rng, 3, 4, balanced=True, min_it=2, max_it=3, method='NO')
    Cb = [[x.b for x in r] for r in C]
    d18.append(ex_transport(Cb, s, d, ['O1', 'O2', 'O3'], ['D1', 'D2', 'D3', 'D4'], gen_enun(Cb, s, d), ['SBF por Esquina Nor-Oeste.', 'Solución óptima.', '¿Soluciones múltiples?'], method='NO'))
    days.append({'clase': CL[6], 'ejemplos': [], 'ejercicios': d18})
    return days

if __name__ == '__main__':
    d = build()
    json.dump(d, open('tr_days.json', 'w'))
    print([(len(x['ejemplos']), len(x['ejercicios'])) for x in d])
