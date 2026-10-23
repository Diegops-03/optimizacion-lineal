import json, random
from hungarian import *
from core import table, fr

def ex_as(enun, parts, sol):
    L = 'abcdef'
    q = enun + '<ol class="parts">' + ''.join(f'<li><b>{L[i]})</b> {t}</li>' for i, t in enumerate(parts)) + '</ol>'
    return {'q': q, 's': sol}

def sp(title, body):
    return f'<div class="solpart"><h5>{title}</h5>{body}</div>'

def plain_table(C, rl, cl):
    return data_html(C, rl, cl)

CL = {}
CL[1] = '''<h4>Problema de asignación</h4>
<p>Asignar n recursos a n actividades, uno a uno, al mínimo costo. Es un transporte con ofertas y demandas iguales a 1 (muy degenerado), por eso se usa el <b>Método Húngaro</b>.</p>
<ol><li><b>Paso 0:</b> balancear (filas = columnas) con ficticios de costo 0.</li>
<li><b>Paso 1:</b> restar el mínimo de cada fila; después, el mínimo de cada columna.</li>
<li><b>Paso 2:</b> cubrir todos los ceros con el <b>mínimo</b> número de líneas (horizontales o verticales). Si se necesitan n líneas ⇒ hay asignación óptima entre los ceros.</li>
<li><b>Paso 3:</b> si hay menos de n líneas: k = menor valor no cubierto. Restar k a los no cubiertos y <b>sumar k a las intersecciones</b> (cubiertos por 2 líneas). Volver al paso 2.</li></ol>
<p class="tip">Para asignar: parte por la fila o columna que tenga un solo cero. Una vez elegido, tacha su fila y su columna.</p>'''
CL[2] = '''<h4>Casos: no balanceado, prohibidos y máximo</h4>
<ul><li><b>Más recursos que actividades</b> (o al revés): agrega columnas (o filas) ficticias con 0. El recurso asignado al ficticio queda sin actividad.</li>
<li><b>Asignación prohibida</b> ("el operador 1 no puede ir a la máquina 3"): costo <b>M</b>.</li>
<li><b>Maximizar</b>: transforma cada valor en (mayor valor de la tabla − c<sub>ij</sub>) y minimiza. También sirve cambiar el signo. Al final suma los valores <b>originales</b>.</li>
<li><b>Soluciones múltiples</b>: si en la matriz final puedes elegir otra combinación de ceros independientes, hay otra solución óptima con el mismo total.</li></ul>'''
CL[3] = '''<h4>Variantes que se piden "construya la tabla"</h4>
<ul><li><b>Un recurso puede hacer 2 tareas</b>: duplica su fila (la segunda con el costo que corresponda, p. ej. con 50% de descuento). Rellena con ficticios para balancear.</li>
<li><b>Una actividad admite 2 recursos</b>: duplica la columna.</li>
<li><b>Obligatorio asignar</b> a alguien ("Tomás debe ser asignado", "Peach no puede quedar sin depto."): costo <b>M</b> entre ese recurso y el ficticio.</li>
<li><b>Opcional</b> (puede quedar fuera): costo 0 con el ficticio.</li>
<li><b>Reemplazar una máquina</b>: agrega la nueva como columna y un operador ficticio con 0. La máquina que queda con el ficticio es la que conviene sacar.</li></ul>'''
CL[4] = '''<p><b>Mini-certamen de asignación.</b> 3 problemas: resolver por húngaro y construir tablas de variantes. 20 minutos cada uno.</p>'''
CL[5] = '''<p><b>Simulacro del Certamen 2.</b> 4 problemas, como en el C2 2026-1: sensibilidad, Branch and Bound, transporte/transbordo y asignación. Tiempo: <b>80 minutos</b>, sin apuntes. Después corrige con la pauta y anota cuánto te demoraste en cada uno.</p>'''
CL[6] = '''<h4>Formulario rápido</h4>
<div class="tw"><table class="t"><thead><tr><th>Tema</th><th>Lo esencial</th></tr></thead><tbody>
<tr><th>B⁻¹</th><td>Columnas de las holguras en la tabla óptima</td></tr>
<tr><th>Cambio b</th><td>x<sub>B</sub> = B⁻¹b; si hay negativos ⇒ simplex dual</td></tr>
<tr><th>Cambio c<sub>j</sub></th><td>Nueva fila Z, canonizar; si hay negativos ⇒ simplex primal</td></tr>
<tr><th>Nueva restricción</th><td>¿La cumple x*? Si no: fila nueva, canonizar, simplex dual</td></tr>
<tr><th>Simplex dual</th><td>Sale RHS más negativo; entra mín |z<sub>j</sub>/a<sub>rj</sub>| con a<sub>rj</sub> &lt; 0</td></tr>
<tr><th>B&amp;B</th><td>x ≤ ⌊x*⌋ y x ≥ ⌈x*⌉; podar por NF, entera o cota</td></tr>
<tr><th>Transporte</th><td>m+n−1 básicas; u<sub>i</sub>+v<sub>j</sub>=c<sub>ij</sub>; c<sub>ij</sub>−u<sub>i</sub>−v<sub>j</sub> ≥ 0 ⇒ óptimo</td></tr>
<tr><th>Múltiples</th><td>No básica con costo reducido 0 (transporte) o ceros alternativos (asignación)</td></tr>
<tr><th>Transbordo</th><td>B = total; transbordo: o<sub>i</sub>+B y d<sub>i</sub>+B; c<sub>ii</sub>=0; sin arco = M</td></tr>
<tr><th>Húngaro</th><td>Filas, columnas, mín. líneas, k: −k no cubiertos, +k intersecciones</td></tr>
</tbody></table></div>
<h4>Errores frecuentes</h4>
<ul><li>Olvidar canonizar la fila Z (o la fila nueva) antes de seguir.</li>
<li>En simplex dual, usar coeficientes positivos de la fila que sale (solo los negativos).</li>
<li>Decir "la solución no cambia" cuando solo se mantiene la base.</li>
<li>En B&amp;B, no verificar que la solución entera cumpla todas las restricciones.</li>
<li>En transporte, terminar con menos de m+n−1 básicas (faltan los 0 degenerados).</li>
<li>Poner 0 en vez de M en rutas prohibidas o demandas obligatorias.</li>
<li>En asignación de máximo, sumar los valores transformados en vez de los originales.</li></ul>'''

def solve_block(C, rl, cl, **kw):
    h, stars, total, info = hungarian(C, rl, cl, **kw)
    return h, total, info

def build():
    days = []
    rng = random.Random(1811)
    # ---- Ejemplos ----
    h, t, i = solve_block([[10, 9, 7, 8], [5, 8, 7, 7], [5, 4, 6, 5], [2, 3, 4, 5]], ['M1', 'M2', 'M3', 'M4'], ['T1', 'T2', 'T3', 'T4'])
    A1 = ex_as('<p>Encontrar la asignación de costo mínimo (ejemplo del apunte "El Problema de Asignación y Método Húngaro"):</p>' + plain_table([[10, 9, 7, 8], [5, 8, 7, 7], [5, 4, 6, 5], [2, 3, 4, 5]], ['M1', 'M2', 'M3', 'M4'], ['T1', 'T2', 'T3', 'T4']),
               ['Resuelva con el método húngaro.'], sp('Desarrollo', h))
    A1['intro'] = 'El apunte llega a costo total = 20 después de una corrección con k.'
    mx = [[2, 4, 10, 3, 6], [7, 7, 5, 6, 4], [8, 6, 7, 8, 9], [4, 9, 12, 8, 7], [11, 8, 6, 6, 5]]
    h, t, i = solve_block(mx, list('ABCDE'), list('12345'), maximize=True)
    A2 = ex_as('<p>Resolver el problema de asignación que <b>maximiza</b> los beneficios (apunte "Un problema de asignación de MÁXIMO"):</p>' + plain_table(mx, list('ABCDE'), list('12345')), ['Encuentre la asignación de beneficio máximo.'], sp('Desarrollo', h))
    A2['intro'] = 'El profesor transforma con 12 − c<sub>ij</sub> y obtiene un total de 45.'
    c26 = [[5, 5, 'M', 2], [7, 4, 2, 3], [9, 3, 5, 'M'], [7, 2, 6, 7]]
    c26d = [[5, 5, '–', 2], [7, 4, 2, 3], [9, 3, 5, '–'], [7, 2, 6, 7]]
    h, t, i = solve_block(c26, ['Op1', 'Op2', 'Op3', 'Op4'], ['Máq1', 'Máq2', 'Máq3', 'Máq4'])
    A3 = ex_as('<p>Asignar cuatro operadores a cuatro máquinas. El operador 1 no puede ir a la máquina 3 y el operador 3 no puede ir a la máquina 4:</p>' + plain_table(c26d, ['Op1', 'Op2', 'Op3', 'Op4'], ['Máq1', 'Máq2', 'Máq3', 'Máq4']) + '<p class="src">C2 2026-1, Problema 4 a).</p>',
               ['Encuentre la asignación óptima.'], sp('Desarrollo', '<p>Las asignaciones prohibidas se reemplazan por M.</p>' + h))
    A3['intro'] = 'Problema 4 a) del último C2: la pauta obtiene costo total 14.'
    c26b = [[5, 5, 'M', 2, 2], [7, 4, 2, 3, 1], [9, 3, 5, 'M', 2], [7, 2, 6, 7, 8]]
    h, t, i = solve_block(c26b, ['Op1', 'Op2', 'Op3', 'Op4'], ['Máq1', 'Máq2', 'Máq3', 'Máq4', 'Máq5'])
    A4 = ex_as('<p>Mismo problema anterior, pero ahora hay una quinta máquina disponible, con costos 2, 1, 2 y 8 para los operadores 1 a 4. La nueva máquina reemplazaría a una existente si se justifica económicamente.</p><p class="src">C2 2026-1, Problema 4 b).</p>',
               ['Construya la tabla de asignación y encuentre la solución óptima. ¿Conviene reemplazar una máquina? ¿Cuál?'],
               sp('Desarrollo', '<p>5 máquinas y 4 operadores ⇒ un <b>operador ficticio</b> con costo 0. La máquina que quede asignada al ficticio es la que se reemplaza.</p>' + h + f'<p><b>Conclusión:</b> el costo baja de 14 a {t}. Conviene reemplazar la <b>máquina 1</b> (queda con el ficticio) por la máquina 5.</p>'))
    A4['intro'] = 'Variante "máquina nueva": la pauta obtiene costo total 8 y reemplaza la máquina 1.'
    ob = [[50, 46, 42, 40], [51, 48, 44, 'M'], [51, 48, 44, 'M'], ['M', 47, 45, 45], ['M', 47, 45, 45]]
    h, t, i = solve_block(ob, ['Obr1', 'Obr2', "Obr2'", 'Obr3', "Obr3'"], ['T1', 'T2', 'T3', 'T4'])
    A5 = ex_as('<p>Una constructora debe contratar obreros para 4 trabajos. Montos (miles de $):</p>' + plain_table([[50, 46, 42, 40], [51, 48, 44, '–'], ['–', 47, 45, 45]], ['Obrero 1', 'Obrero 2', 'Obrero 3'], ['T1', 'T2', 'T3', 'T4'])
               + '<p>El obrero 1 puede hacer solo un trabajo; los obreros 2 y 3 pueden hacer hasta dos.</p><p class="src">C2 2024-2, Problema 3 a).</p>',
               ['Determine la(s) asignación(es) que minimizan el costo de ejecutar los cuatro trabajos.'],
               sp('Desarrollo', '<p>Los obreros 2 y 3 se <b>duplican</b> (filas 2\' y 3\'). Quedan 5 filas y 4 trabajos ⇒ un trabajo ficticio con 0 (el obrero que lo recibe no trabaja).</p>' + h))
    A5['intro'] = 'Variante "un recurso hace dos tareas": duplicar filas.'
    # ---- D22 ----
    d22 = []
    for n_ in (4, 4, 5):
        for _ in range(3000):
            C = [[rng.randint(2, 20) for _ in range(n_)] for _ in range(n_)]
            try:
                h, t, i = solve_block(C, [f'R{k+1}' for k in range(n_)], [f'A{k+1}' for k in range(n_)])
            except Exception:
                continue
            if i['iters'] >= 1 and not i['multi']:
                break
        d22.append(ex_as('<p>Encuentre la asignación de costo mínimo:</p>' + plain_table(C, [f'R{k+1}' for k in range(n_)], [f'A{k+1}' for k in range(n_)]), ['Resuelva con el método húngaro.'], sp('Desarrollo', h)))
    days.append({'clase': CL[1], 'ejemplos': [A1], 'ejercicios': d22})
    # ---- D23 ----
    d23 = []
    h, t, i = solve_block([[13, 16, 11, 12], [15, 'M', 13, 20], [5, 7, 10, 6]], ['Máq1', 'Máq2', 'Máq3'], ['Sitio1', 'Sitio2', 'Sitio3', 'Sitio4'])
    d23.append(ex_as('<p>Una compañía compró 3 máquinas nuevas y hay 4 sitios para instalarlas. Costo de manejo de materiales por unidad de tiempo; el sitio 2 no es adecuado para la máquina 2:</p>'
                     + plain_table([[13, 16, 11, 12], [15, '–', 13, 20], [5, 7, 10, 6]], ['Máq1', 'Máq2', 'Máq3'], ['Sitio1', 'Sitio2', 'Sitio3', 'Sitio4']) + '<p class="src">Ejemplo 2 del apunte de asignación.</p>',
                     ['Construya la tabla de asignación balanceada.', 'Encuentre la asignación óptima.'], sp('Desarrollo', h)))
    med = [[6, 5, 7, 8], [7, 4, 6, 7], [5, 9, 7, 8], [4, 8, 1, 6]]
    h, t, i = solve_block(med, ['Méd1', 'Méd2', 'Méd3', 'Méd4'], ['A', 'B', 'C', 'D'], maximize=True)
    greedy = '<p><b>Algoritmo del director</b> (tomar siempre el mayor valor disponible): Méd3→B (9), Méd1→D (8), Méd2→A (7), Méd4→C (1) ⇒ total 25.</p>'
    d23.append(ex_as('<p>El director de una clínica asigna 4 médicos a 4 pacientes. Valor de éxito (1 a 10):</p>' + plain_table(med, ['Méd1', 'Méd2', 'Méd3', 'Méd4'], ['A', 'B', 'C', 'D'])
                     + '<p>El director siempre asigna a cada médico el paciente con mayor éxito disponible.</p><p class="src">C2 2025-2, Problema 1.</p>',
                     ['¿Es buena la solución del director? Compárela con el óptimo (máximo).', 'Si solo hay 3 quirófanos, construya la tabla que deja un médico y un paciente sin asignar (sin resolver).'],
                     sp('a)', greedy + h + f'<p><b>Conclusión:</b> el óptimo es {t} &gt; 25: el método "goloso" del director <b>no es óptimo</b>.</p>')
                     + sp('b)', '<p>Se agrega un paciente ficticio (el médico asignado ahí no opera) y un médico ficticio (el paciente asignado ahí espera). Ficticio–ficticio = −M (prohibido, para que haya exactamente 3 operaciones). Como se maximiza, el resto de los ficticios vale 0.</p>'
                            + plain_table([[6, 5, 7, 8, 0], [7, 4, 6, 7, 0], [5, 9, 7, 8, 0], [4, 8, 1, 6, 0], [0, 0, 0, 0, '−M']], ['Méd1', 'Méd2', 'Méd3', 'Méd4', 'Fic'], ['A', 'B', 'C', 'D', 'Fic']))))
    llm = [[7, 2, 14, 10, 13, 16], [9, 12, 17, 10, 17, 6], [13, 5, 6, 19, 18, 14], [11, 7, 13, 4, 17, 13], [6, 5, 3, 17, 4, 17]]
    names = ['Ana', 'Berta', 'Carla', 'Daniela', 'Ester']; sv = [f'S{k}' for k in range(1, 7)]
    h, t, i = solve_block(llm, names, sv)
    tb = [[7, 2, 2, 14, 14, 10, 'M', 'M']] * 3 + [[9, 12, 12, 17, 17, 10, 'M', 'M'], [13, 5, 5, 6, 6, 19, 'M', 'M'], [11, 7, 7, 13, 13, 4, 'M', 'M'], [11, 7, 7, 13, 13, 4, 0, 0], [6, 5, 5, 3, 3, 17, 0, 0]]
    h2, t2, i2 = solve_block(tb, ['Ana1', 'Ana2', 'Ana3', 'Berta', 'Carla', 'Dani1', 'Dani2', 'Ester'], ['S1', 'S2', "S2'", 'S3', "S3'", 'S4', 'Fic1', 'Fic2'])
    d23.append(ex_as('<p>Una empresa asigna consultas de clientas a servidores. Tiempo estimado de ejecución (cada servidor responde una consulta):</p>' + plain_table(llm, names, sv) + '<p class="src">C2 2024-1, Problema 3 (y Tarea 5).</p>',
                     ['Asigne por el método húngaro. ¿Valor de Z? ¿Sobra algún servidor?', 'Se queman los servidores 5 y 6. Ana debe recibir 3 respuestas; Berta y Carla deben ser respondidas; Daniela envía 2 consultas pero solo se garantiza la primera; los servidores 2 y 3 ahora responden 2 consultas cada uno. Construya la tabla y resuélvala.'],
                     sp('a)', '<p>5 clientas y 6 servidores ⇒ clienta ficticia con 0 (el servidor asignado a ella sobra).</p>' + h)
                     + sp('b)', '<p>Filas: 3 para Ana, Berta, Carla, 2 para Daniela, Ester (8 consultas). Columnas: S1, S2, S2\', S3, S3\', S4 (6 respuestas) + 2 ficticias (consultas sin respuesta). M hacia el ficticio para las consultas obligatorias (Ana ×3, Berta, Carla, Daniela 1); 0 para Daniela 2 y Ester.</p>' + h2)))
    days.append({'clase': CL[2], 'ejemplos': [A2, A3], 'ejercicios': d23})
    # ---- D24 ----
    d24 = []
    tec = [[8, 9, 7, 12], [10, 12, 7, 9], [13, 12, 9, 10], [13, 14, 10, 12]]
    h, t, i = solve_block(tec, ['T1', 'T2', 'T3', 'T4'], ['M1', 'M2', 'M3', 'M4'])
    tc = [[8, 9, 7, 12, 0], ['M', 9, 'M', 12, 0], [10, 12, 7, 9, 'M'], [13, 12, 9, 10, 0], [13, 'M', 9, 'M', 0]]
    hc, tcz, ic = solve_block(tc, ['T1', "T1'", 'T2', 'T3', "T3'"], ['M1', 'M2', 'M3', 'M4', 'Fic'])
    d24.append(ex_as('<p>Cuatro técnicos hacen mantención a cuatro máquinas. Costos:</p>' + plain_table(tec, ['Téc1', 'Téc2', 'Téc3', 'Téc4'], ['Máq1', 'Máq2', 'Máq3', 'Máq4']) + '<p class="src">C2 2022-2, Problema 2.</p>',
                     ['Determine la asignación de costo mínimo.', '¿Hay soluciones múltiples? Si es así, entregue otra.', 'El técnico 4 está con licencia. Los técnicos 1 y 3 pueden atender dos máquinas: la segunda del técnico 1 debe ser la 2 o la 4; la segunda del técnico 3, la 1 o la 3. El técnico 2 debe ser asignado. Construya la tabla (y resuélvala).'],
                     sp('a) y b)', h + ('' if i['multi'] else '<p>No hay otra combinación de ceros independientes: la solución es única.</p>'))
                     + sp('c)', '<p>Filas T1, T1\' (segunda máquina: solo 2 o 4), T2, T3, T3\' (solo 1 o 3). 5 filas y 4 máquinas ⇒ máquina ficticia; T2 no puede quedar sin máquina ⇒ M en el ficticio.</p>' + hc)))
    lp = [[18, 6, 13, 9], [5, 8, 17, 2], [21, 7, 6, 11], [8, 3, 9, 14], [12, 5, 15, 18]]
    lpn = ['Lucía', 'Miguel', 'Sofía', 'Tomás', 'Paula']
    h, t, i = solve_block([r + [0 if k != 3 else 'M'] for k, r in enumerate(lp)], lpn, ['A', 'B', 'C', 'D', 'Fic'])
    d24.append(ex_as('<p>LogiPro S.A. elige líderes para 4 consultorías entre 5 empleados. Costos:</p>' + plain_table(lp, lpn, ['Cons. A', 'Cons. B', 'Cons. C', 'Cons. D']) + '<p>Es obligatorio asignar a Tomás.</p><p class="src">C2 2025-1, Problema 3.</p>',
                     ['Construya la tabla de asignación.', 'Encuentre la asignación óptima.'], sp('Desarrollo', '<p>5 empleados y 4 consultorías ⇒ consultoría ficticia con 0, pero Tomás tiene M hacia el ficticio (debe quedar asignado).</p>' + h)))
    dep = [[5, 5, 21, 13, 9], [8, 14, 15, 16, 10], [14, 10, 25, 20, 22], [21, 12, 11, 18, 25], [16, 11, 5, 8, 6]]
    dn = ['Antofagasta', 'La Serena', 'Santiago', 'Valparaíso', 'Concepción']
    h, t, i = solve_block(dep, dn, ['Mario', 'Luigi', 'Peach', 'Toad', 'Yoshi'])
    half = lambda x: F(x, 2)
    tb = []
    for k, r in enumerate(dep):
        toad = r[3] if k in (0, 1) else 'M'
        tb.append([r[0], half(r[0]), r[1], r[2], toad, r[4], half(r[4])])
    tb.append([0, 0, 0, 'M', 0, 0, 0]); tb.append([0, 0, 0, 'M', 0, 0, 0])
    cols = ['Mario', "Mario'", 'Luigi', 'Peach', 'Toad', 'Yoshi', "Yoshi'"]
    hb, tbz, ib = solve_block(tb, dn + ['Fic1', 'Fic2'], cols)
    d24.append(ex_as('<p>Usted tiene 5 departamentos para arrendar y 5 gestores con distintas comisiones:</p>' + plain_table(dep, dn, ['Mario', 'Luigi', 'Peach', 'Toad', 'Yoshi']) + '<p class="src">C2 2023-1, Problema 2.</p>',
                     ['¿Qué departamento asigna a cada gestor? (método húngaro)', 'Toad solo puede ir a Antofagasta o La Serena; Peach no puede quedar sin departamento; Mario y Yoshi pueden administrar un segundo departamento con 50% de descuento en la comisión. Escriba la tabla (y resuélvala).'],
                     sp('a)', h) + sp('b)', '<p>Columnas extra Mario\' y Yoshi\' (comisión a la mitad). 7 gestores y 5 departamentos ⇒ 2 departamentos ficticios con 0, salvo Peach (M). Toad: M fuera de Antofagasta y La Serena.</p>' + hb)))
    days.append({'clase': CL[3], 'ejemplos': [A4, A5], 'ejercicios': d24})
    # ---- D25 ----
    d25 = []
    cue = [[11, 18, 26, 25, 7, 26], [-3, 9, -4, 28, 21, 22], [-4, -1, 18, 25, 0, 20], [6, 11, -5, 14, 30, 0], [7, 11, 5, 30, 19, -3], [23, 16, 10, 24, 1, 5]]
    W = ['Ana', 'Berta', 'Carla', 'Daniela', 'Ester', 'Fernanda']; Mn_ = ['Gustavo', 'Henry', 'Isidro', 'Javier', 'Kevin', 'Larry']
    h, t, i = solve_block(cue, W, Mn_)
    tb_b = [[r[0], r[1], r[2], r[3], r[3], 0] for r in cue]
    hb, tb_z, _ = solve_block(tb_b, W, ['Gustavo', 'Henry', 'Isidro', 'Javier', "Javier'", 'Fic'])
    tb_c = [r + [0 if k == 0 else 'M'] for k, r in enumerate(cue)] + [[0] * 6 + [0]]
    hc2, tcz2, _ = solve_block(tb_c, W + ['Fic'], Mn_ + ['Fic'])
    d25.append(ex_as('<p>Para la fonda de Optimización Lineal hay que formar parejas de cueca. La tabla indica cuántas veces se pisaron los pies en los ensayos (negativo = pareja secretamente enamorada, para que bailen juntos):</p>' + plain_table(cue, W, Mn_) + '<p class="src">C2 2022-1, Problema 3.</p>',
                     ['Resuelva la asignación mediante el método húngaro.', 'Kevin y Larry se enferman; Javier bailará con dos mujeres. Escriba la tabla (y resuélvala).', 'Ana quiere que su participación sea opcional. Escriba la tabla (y resuélvala).'],
                     sp('a)', '<p>Los negativos no son problema: el método funciona igual (al restar el mínimo de cada fila todo queda ≥ 0).</p>' + h)
                     + sp('b)', '<p>Columnas: Gustavo, Henry, Isidro, Javier, Javier\' (5) para 6 mujeres ⇒ columna ficticia con 0.</p>' + hb)
                     + sp('c)', '<p>Se agrega columna ficticia (Ana puede quedar sin pareja: 0; las demás M) y fila ficticia (si Ana no baila, sobra un hombre: 0). Ficticio–ficticio = 0 (Ana sí baila).</p>' + hc2)))
    t26 = [[20, 30, 50, 40, 70, 0], [30, 10, 10, 20, 50, 0], [40, 30, 60, 30, 40, 0], [30, 20, 40, 50, 60, 0], [60, 70, 50, 70, 50, 0], [30, 40, 60, 40, 60, 0]]
    h, t, i = solve_block(t26, list('ABCDEF'), ['1', '2', '3', '4', '5', 'F'])
    d25.append(ex_as('<p>Resuelva el problema de asignación de costo mínimo (la columna F es ficticia):</p>' + plain_table(t26, list('ABCDEF'), ['1', '2', '3', '4', '5', 'F']) + '<p class="src">Test 11 Húngaro 2026-1 (R. Linfati). La pauta obtiene Z = 130.</p>',
                     ['Indique la asignación óptima y el valor de la función objetivo.'], sp('Desarrollo', h)))
    prof = [[27, 22, 34, 28, 36], [20, 36, 34, 28, 36], ['M', 'M', 23, 19, 26], [26, 25, 18, 42, 35]]
    tbp = [prof[0] + ['M', 'M'], prof[1] + ['M', 'M'], prof[1] + [0, 0], prof[2] + ['M', 'M'], prof[2] + [0, 0], prof[3] + ['M', 'M'], prof[3] + [0, 0]]
    hp, tp, ip = solve_block(tbp, ['P1', 'P2', "P2'", 'P3', "P3'", 'P4', "P4'"], ['A1', 'A2', 'A3', 'A4', 'A5', 'F1', 'F2'])
    d25.append(ex_as('<p>Hay que asignar 5 asignaturas a 4 profesores según la evaluación de encuestas (0 excelente, mayor es peor):</p>' + plain_table([[27, 22, 34, 28, 36], [20, 36, 34, 28, 36], [32, 38, 23, 19, 26], [26, 25, 18, 42, 35]], ['P1', 'P2', 'P3', 'P4'], ['A1', 'A2', 'A3', 'A4', 'A5'])
                     + '<p>P3 no puede dictar A1 ni A2. Todas las asignaturas se dictan y no se comparten. Ningún profesor queda sin asignatura. P1 dicta solo una; los demás pueden dictar más de una.</p><p class="src">Test 12 Asignación 2026-1 (R. Linfati).</p>',
                     ['Construya la tabla de asignación.', 'Resuelva.'], sp('Desarrollo', '<p>P2, P3 y P4 se duplican (pueden dictar 2). 7 filas y 5 asignaturas ⇒ 2 columnas ficticias. Las filas "principales" tienen M en los ficticios (nadie queda sin asignatura); las duplicadas, 0.</p>' + hp)))
    days.append({'clase': CL[4], 'ejemplos': [], 'ejercicios': d25})
    return days

if __name__ == '__main__':
    from fractions import Fraction as F
    d = build()
    json.dump(d, open('as_days.json', 'w'))
    print([(len(x['ejemplos']), len(x['ejercicios'])) for x in d])
