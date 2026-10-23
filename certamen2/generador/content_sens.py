from build_sens import *

def example_from(c, A, b, parts_fn, intro=''):
    t, st, steps = solve_max(c, A, b)
    rng = random.Random(1)
    enun = '<p>Considere el modelo:</p>' + enunciado_base(c, A, b, t)
    parts = parts_fn(c, A, b, t, rng)
    e = ex(enun, parts)
    e['intro'] = intro
    return e

def fixed_parts_b(c, A, b, t, rng):
    out = [q_identify(c, A, b, t)]
    q, s, _ = q_change_b(c, A, b, t, [b[0], b[1] + 10]); out.append((q, s))
    return out

CLASE = {}
CLASE[1] = '''
<p><b>Idea:</b> el análisis de sensibilidad estudia qué pasa con la solución óptima si cambia un dato del modelo, <i>sin resolver todo de nuevo</i>. Todo sale de la <b>tabla óptima</b>.</p>
<h4>Lo que se lee directo en la tabla óptima (Max, restricciones ≤)</h4>
<ul>
<li><b>B⁻¹</b>: las columnas de las variables que eran básicas en la tabla inicial (las holguras x<sub>3</sub>, x<sub>4</sub>, …) tal como aparecen en la tabla óptima. Se copian fila por fila.</li>
<li><b>x<sub>B</sub> = B⁻¹·b</b>: valores de las variables básicas (columna RHS).</li>
<li><b>Z* = c<sub>B</sub>·x<sub>B</sub></b>, donde c<sub>B</sub> son los coeficientes de la F.O. de las básicas, en el orden de la base.</li>
<li><b>Precios duales y<sub>i</sub></b>: fila Z bajo cada holgura. Dicen cuánto sube Z por una unidad más del recurso i. Se cumple Z* = Σ y<sub>i</sub>·b<sub>i</sub>.</li>
</ul>
<h4>Cambio en b que mantiene la base</h4>
<p>Se calcula x<sub>B</sub> = B⁻¹·b<sub>nuevo</sub>. Si todo es ≥ 0, la base sigue siendo óptima: <b>las mismas variables son básicas, pero con otros valores</b>. Z nuevo = c<sub>B</sub>·x<sub>B</sub> (o Z + y<sub>i</sub>·Δb<sub>i</sub>).</p>
<p class="tip">Error típico: decir "la solución no cambia". Cambian los valores; lo que se mantiene es <b>cuáles</b> variables son básicas.</p>
'''
CLASE[2] = '''
<h4>Cambio en un coeficiente c<sub>j</sub> de la función objetivo</h4>
<ol>
<li>En la tabla óptima, reescribe la fila Z con los <b>nuevos −c<sub>j</sub></b> (0 bajo las holguras, RHS = 0).</li>
<li><b>Canoniza</b>: bajo cada variable básica debe quedar 0. Para eso suma a la fila Z: (c de esa básica)·(su fila). Ej.: Z + 7·F1 + 9·F2.</li>
<li>Si todos los costos reducidos quedan ≥ 0 → sigue óptima; la solución es la misma y solo cambia Z.</li>
<li>Si alguno queda negativo → sigue con <b>simplex primal</b> (entra el más negativo, razón mínima).</li>
</ol>
<h4>Atajo para variable no básica</h4>
<p>Si x<sub>j</sub> no es básica, solo cambia su propio costo reducido: nuevo = anterior − Δc<sub>j</sub>. Si queda negativo, x<sub>j</sub> entra.</p>
<h4>Rango de c<sub>j</sub> (básica)</h4>
<p>Pon c<sub>j</sub> + Δ, canoniza y exige que cada costo reducido de las no básicas quede ≥ 0: z̄<sub>k</sub> + Δ·a<sub>rk</sub> ≥ 0, donde a<sub>rk</sub> es el número de la fila de x<sub>j</sub> en la columna k. Despeja Δ.</p>
'''
CLASE[3] = '''
<h4>Cambio en b que deja la tabla infactible</h4>
<p>Si x<sub>B</sub> = B⁻¹·b<sub>nuevo</sub> tiene algún valor negativo, la tabla sigue cumpliendo optimalidad (fila Z ≥ 0) pero es infactible. Se reemplaza la columna RHS (y Z = c<sub>B</sub>·x<sub>B</sub>) y se aplica <b>simplex dual</b>:</p>
<ol>
<li><b>Sale</b> la fila con el RHS más negativo.</li>
<li>En esa fila, mira solo los coeficientes <b>negativos</b>. Calcula |z̄<sub>j</sub> / a<sub>rj</sub>|. <b>Entra</b> el menor cociente.</li>
<li>Pivotea igual que en simplex. Repite hasta que todo el RHS sea ≥ 0.</li>
</ol>
<p>Si la fila que sale no tiene coeficientes negativos, el problema es infactible.</p>
<h4>Rango de b<sub>i</sub></h4>
<p>b<sub>i</sub> + Δ ⇒ x<sub>B</sub> = B⁻¹b + Δ·(columna i de B⁻¹) ≥ 0. Cada fila da una desigualdad en Δ; el rango es la intersección. Dentro de ese rango el precio dual y<sub>i</sub> es válido.</p>
'''
CLASE[4] = '''
<h4>Agregar una restricción nueva</h4>
<ol>
<li><b>Evalúa</b> la solución óptima actual en la restricción. Si se cumple, no cambia nada.</li>
<li>Si no se cumple: déjala en forma ≤ (si es ≥, multiplica por −1), agrega su holgura (x<sub>n+1</sub>) y ponla como <b>fila nueva</b> en la tabla óptima.</li>
<li><b>Canoniza</b> la fila nueva: bajo las variables básicas debe haber 0. Réstale k·(fila de la básica) por cada básica con coeficiente k ≠ 0.</li>
<li>El RHS de la fila nueva queda negativo ⇒ <b>simplex dual</b>.</li>
</ol>
<p class="tip">Z nunca mejora al agregar una restricción (la región factible se achica o queda igual). Sirve para revisar tu resultado.</p>
'''
CLASE[5] = '''
<h4>Agregar una variable nueva (nuevo producto)</h4>
<p>Con precios duales y = (y<sub>1</sub>, …, y<sub>m</sub>) de la tabla óptima y la columna a de la nueva actividad:</p>
<ul>
<li><b>Costo reducido</b>: c̄ = y·a − c<sub>nuevo</sub> (lo que "cuestan" sus recursos menos lo que deja).</li>
<li>Si c̄ ≥ 0, no conviene producirla.</li>
<li>Si c̄ &lt; 0, conviene: su columna en la tabla óptima es <b>B⁻¹·a</b>; agrega la columna con c̄ en la fila Z y sigue con simplex primal.</li>
</ul>
<p>Resumen de toda la semana:</p>
<div class="tw"><table class="t"><thead><tr><th>Cambio</th><th>Qué calculo</th><th>Si falla…</th></tr></thead><tbody>
<tr><th>b</th><td>x<sub>B</sub> = B⁻¹b ≥ 0</td><td>simplex dual</td></tr>
<tr><th>c<sub>j</sub></th><td>fila Z canonizada ≥ 0</td><td>simplex primal</td></tr>
<tr><th>restricción</th><td>¿cumple x*?</td><td>simplex dual</td></tr>
<tr><th>variable</th><td>c̄ = y·a − c ≥ 0</td><td>simplex primal</td></tr>
</tbody></table></div>
'''
CLASE[6] = '''
<p>Hoy, problemas con el formato del certamen (como el Problema 1 del C2 2026-1): te dan la tabla óptima y piden (a) nueva solución si cambia un c<sub>j</sub>, (b) si cambia un recurso b<sub>i</sub>, (c) si se agrega una restricción. Cada parte es independiente y parte de la tabla óptima original.</p>
<p class="tip">En el certamen: escribe siempre B⁻¹ explícita, muestra la operación al lado de cada fila y termina con la solución completa (x<sub>1</sub>, x<sub>2</sub>, …, Z).</p>
'''
CLASE[7] = '''
<p><b>Mini-certamen de sensibilidad.</b> Hazlo sin mirar la clase: 3 problemas, 20 minutos cada uno. Luego corrige con la pauta y anota tus errores.</p>
'''

def build():
    days = []
    # Day 1
    e1 = example_from([5, 3], [[3, 5], [5, 2]], [15, 10], fixed_parts_b,
        intro='Es el ejemplo del apunte del profesor (Análisis de sensibilidad). Fíjate cómo se arma B⁻¹ y cómo cambia la solución si b<sub>2</sub> sube 10 unidades.')
    def ex2_parts(c, A, b, t, rng):
        return [q_identify(c, A, b, t), P_b_feasible(c, A, b, t, rng)]
    c, A, b, t = get_lp(101, 2, 3, maxden=8)
    rng = random.Random(3)
    e2 = ex('<p>Considere el modelo:</p>' + enunciado_base(c, A, b, t), ex2_parts(c, A, b, t, rng))
    e2['intro'] = 'Ahora con 3 variables y 2 restricciones (como en el C2 2026-1). B⁻¹ es 2×2 aunque haya 3 variables de decisión.'
    exs = [try_make(200 + 10 * k, m, n, [P_identify, P_b_feasible]) for k, (m, n) in enumerate([(2, 2), (3, 2), (2, 3)])]
    days.append({'clase': CLASE[1], 'ejemplos': [e1, e2], 'ejercicios': exs})
    # Day 2
    def e3_parts(c, A, b, t, rng):
        return [P_c_keep(c, A, b, t, rng), P_c_break(c, A, b, t, rng), P_range_c(c, A, b, t, rng, j=0)]
    for sd in range(300, 400):
        try:
            c, A, b, t = get_lp(sd, 2, 2, maxden=10)
            e3 = ex('<p>Considere el modelo:</p>' + enunciado_base(c, A, b, t), e3_parts(c, A, b, t, random.Random(sd)))
            break
        except RuntimeError:
            continue
    e3['intro'] = 'Tres casos de cambio en c<sub>j</sub>: uno que mantiene la base, uno que obliga a seguir con simplex primal y el rango.'
    exs = [try_make(400 + 10 * k, m, n, [P_c_keep, P_c_break, P_range_c]) for k, (m, n) in enumerate([(2, 2), (2, 3), (3, 2)])]
    days.append({'clase': CLASE[2], 'ejemplos': [e3], 'ejercicios': exs})
    # Day 3
    def e4_parts(c, A, b, t, rng):
        return [P_range_b(c, A, b, t, rng, i=0), P_b_infeasible(c, A, b, t, rng)]
    for sd in range(500, 600):
        try:
            c, A, b, t = get_lp(sd, 2, 2, maxden=10)
            e4 = ex('<p>Considere el modelo:</p>' + enunciado_base(c, A, b, t), e4_parts(c, A, b, t, random.Random(sd)))
            break
        except RuntimeError:
            continue
    e4['intro'] = 'Primero el rango de b<sub>1</sub>; después un cambio fuera del rango, que obliga a usar simplex dual.'
    exs = [try_make(600 + 10 * k, m, n, [P_range_b, P_b_infeasible]) for k, (m, n) in enumerate([(2, 2), (3, 2), (2, 3)])]
    days.append({'clase': CLASE[3], 'ejemplos': [e4], 'ejercicios': exs})
    # Day 4
    def e5_parts(c, A, b, t, rng):
        return [P_newcons(c, A, b, t, rng, kind='ok'), P_newcons(c, A, b, t, rng, kind='violated')]
    e5 = example_from([5, 3], [[3, 5], [5, 2]], [15, 10],
                      lambda c, A, b, t, rng: [q_new_constraint(c, A, b, t, [1, 1], 4)[:2], q_new_constraint(c, A, b, t, [12, 9], 30)[:2]],
                      intro='Mismo modelo del apunte. La segunda restricción (12x<sub>1</sub> + 9x<sub>2</sub> ≤ 30) es la del ejemplo del profesor.')
    exs = [try_make(700 + 10 * k, m, n, spec) for k, (m, n, spec) in enumerate([
        (2, 2, [(P_newcons, {'kind': 'ok'}), (P_newcons, {'kind': 'violated'})]),
        (2, 3, [(P_newcons, {'kind': 'violated'})]),
        (3, 2, [(P_newcons, {'kind': 'violated', 'op': '≥'})])])]
    days.append({'clase': CLASE[4], 'ejemplos': [e5], 'ejercicios': exs})
    # Day 5
    for sd in range(800, 900):
        try:
            c, A, b, t = get_lp(sd, 2, 2, maxden=10)
            rng = random.Random(sd)
            e6 = ex('<p>Considere el modelo:</p>' + enunciado_base(c, A, b, t), [P_newvar(c, A, b, t, rng, want_enter=False), P_newvar(c, A, b, t, rng, want_enter=True)])
            break
        except RuntimeError:
            continue
    e6['intro'] = 'Ejemplo extra: un producto nuevo que no conviene y otro que sí.'
    exs = [try_make(900 + 10 * k, m, n, spec) for k, (m, n, spec) in enumerate([
        (2, 2, [(P_newvar, {'want_enter': False}), (P_newvar, {'want_enter': True})]),
        (3, 2, [(P_newvar, {'want_enter': True})]),
        (2, 3, [P_identify, (P_newvar, {'want_enter': True})])])]
    days.append({'clase': CLASE[5], 'ejemplos': [e6], 'ejercicios': exs})
    # Day 6 certamen type
    spec = [P_c_break, P_b_infeasible, (P_newcons, {'kind': 'violated'})]
    exs = [try_make(1000 + 20 * k, m, n, spec) for k, (m, n) in enumerate([(2, 3), (2, 2), (3, 2)])]
    days.append({'clase': CLASE[6], 'ejemplos': [], 'ejercicios': exs})
    # Day 7 mini certamen
    exs = [try_make(1100, 2, 3, [P_identify, P_range_b, P_c_break]),
           try_make(1150, 2, 2, [P_range_c, P_b_infeasible, (P_newcons, {'kind': 'violated', 'op': '≥'})]),
           try_make(1200, 3, 2, [(P_newvar, {'want_enter': True}), (P_newcons, {'kind': 'violated'})])]
    days.append({'clase': CLASE[7], 'ejemplos': [], 'ejercicios': exs})
    return days

if __name__ == '__main__':
    d = build()
    json.dump(d, open('sens_days.json', 'w'))
    print([ (len(x['ejemplos']), len(x['ejercicios'])) for x in d])
