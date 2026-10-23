import json, random, datetime
from fractions import Fraction as F
import content_sens, content_bb, content_tr, content_tb, content_as
from build_sens import try_make, P_c_break, P_b_infeasible, P_newcons, P_range_b, P_range_c, P_identify
from content_bb import gen as bbgen, exercise as bbex
from content_tr import ex_transport, data_table
from content_tb import tb_table
from transport import C_, lp_check
from hungarian import hungarian, data_html
from content_as import CL as ASCL, ex_as, sp
from core import fr

def simulacro():
    rng = random.Random(1611)
    ex = []
    p1 = try_make(1300, 2, 3, [P_c_break, P_b_infeasible, (P_newcons, {'kind': 'violated'})])
    p1['q'] = '<p class="src"><b>Problema 1 (15 pts) · Sensibilidad</b></p>' + p1['q']
    ex.append(p1)
    c, cons = bbgen(rng, ncons=3, min_nodes=5, max_nodes=9)
    p2 = bbex(c, cons, pre='<p class="src"><b>Problema 2 (15 pts) · Branch and Bound</b></p>')
    ex.append(p2)
    # transport word problem
    for _ in range(500):
        sup = [rng.randint(3, 9), rng.randint(5, 12)]
        dem = [rng.randint(4, 9), rng.randint(2, 6), rng.randint(2, 6)]
        if sum(dem) - sum(sup) not in (1, 2, 3): continue
        C = [[rng.randint(2, 9) for _ in range(3)] for _ in range(2)]
        mA, mC = rng.randint(3, 7), rng.randint(3, 7)
        try:
            e = ex_transport(C, sup, dem, ['B1', 'B2'], ['A', 'B', 'C'],
                '<p class="src"><b>Problema 3 (15 pts) · Transporte</b></p>'
                f'<p>Un fabricante debe enviar todas las unidades de sus bodegas B1 ({sup[0]}) y B2 ({sup[1]}) a los clientes A, B y C, que demandan {dem[0]}, {dem[1]} y {dem[2]}. Costos unitarios:</p>'
                + data_table(C_(C), sup, dem, ['B1', 'B2'], ['A', 'B', 'C'])
                + f'<p>El cliente B exige toda su demanda. A y C cobran ${mA} y ${mC} por cada unidad no entregada.</p>',
                ['SBF inicial por Esquina Nor-Oeste.', 'Solución óptima con el algoritmo de transporte.', '¿Tiene soluciones múltiples? Fundamente.', 'Suponga que desde A y C se pueden enviar unidades a B a $1 y $2. Construya la tabla de transporte.'],
                method='NO', fic_row=[mA, 'M', mC])
        except Exception:
            continue
        Bt = sum(dem)
        fic = sum(dem) - sum(sup)
        r = [('B1', str(sup[0]), sup[0]), ('B2', str(sup[1]), sup[1]), ('Fic', str(fic), fic), ('A', f'0+{Bt}', Bt), ('C', f'0+{Bt}', Bt)]
        cc = [('A', f'{dem[0]}+{Bt}', dem[0] + Bt), ('B', str(dem[1]), dem[1]), ('C', f'{dem[2]}+{Bt}', dem[2] + Bt)]
        v = {'B1': C[0], 'B2': C[1], 'Fic': [mA, 'M', mC], 'A': [0, 1, 'M'], 'C': ['M', 2, 0]}
        th, Cx, sx, dx = tb_table(r, cc, lambda a, b: v[a][[x[0] for x in cc].index(b)])
        e['s'] += f'<div class="solpart"><h5>d)</h5><p>A y C pasan a ser nodos de transbordo con B = {Bt}.</p>{th}<p class="chk">Costo mínimo de esta tabla: {fr(F(round(lp_check(Cx, sx, dx))))}.</p></div>'
        ex.append(e)
        break
    # assignment
    for _ in range(2000):
        C = [[rng.randint(2, 9) for _ in range(4)] for _ in range(4)]
        C[0][2] = 'M'; C[2][3] = 'M'
        new = [rng.randint(1, 8) for _ in range(4)]
        try:
            h1, s1, t1, i1 = hungarian(C, ['Op1', 'Op2', 'Op3', 'Op4'], ['Máq1', 'Máq2', 'Máq3', 'Máq4'])
            C2 = [C[k] + [new[k]] for k in range(4)]
            h2, s2, t2, i2 = hungarian(C2, ['Op1', 'Op2', 'Op3', 'Op4'], ['Máq1', 'Máq2', 'Máq3', 'Máq4', 'Máq5'])
        except Exception:
            continue
        if i1['iters'] < 1 or t2 >= t1: continue
        shown = [[('–' if x == 'M' else x) for x in r] for r in C]
        rep = [cl for (i, j), cl in zip(s2, [None] * 5) if False]
        fic_machine = [j for (i, j) in s2 if i == 4][0]
        e = ex_as('<p class="src"><b>Problema 4 (15 pts) · Asignación</b></p><p>Asignar cuatro operadores a cuatro máquinas. El operador 1 no puede ir a la máquina 3 y el operador 3 no puede ir a la máquina 4. Costos:</p>' + data_html(shown, ['Op1', 'Op2', 'Op3', 'Op4'], ['Máq1', 'Máq2', 'Máq3', 'Máq4'])
                  + f'<p>Hay una quinta máquina con costos {", ".join(map(str, new))} para los operadores 1 a 4.</p>',
                  ['Encuentre la asignación óptima.', 'Construya la tabla con la quinta máquina y resuélvala. ¿Conviene reemplazar una máquina? ¿Cuál?'],
                  sp('a)', h1) + sp('b)', '<p>Operador ficticio con costo 0.</p>' + h2 + f'<p><b>Conclusión:</b> el costo baja de {t1} a {t2}; conviene reemplazar la <b>máquina {fic_machine + 1}</b> por la 5.</p>'))
        ex.append(e)
        break
    assert len(ex) == 4
    return {'clase': ASCL[5], 'ejemplos': [], 'ejercicios': ex}

def repaso():
    rng = random.Random(1711)
    ex = []
    ex.append(try_make(1400, 2, 2, [P_identify, P_range_b, P_range_c]))
    for _ in range(500):
        sup = [rng.randint(2, 8) * 5, rng.randint(2, 8) * 5]
        dem = [rng.randint(2, 6) * 5 for _ in range(2)]
        last = sum(sup) - sum(dem)
        if last <= 0: continue
        dem.append(last)
        C = [[rng.randint(2, 12) for _ in range(3)] for _ in range(2)]
        try:
            e = ex_transport(C, sup, dem, ['O1', 'O2'], ['D1', 'D2', 'D3'], '<p>Problema de transporte balanceado:</p>' + data_table(C_(C), sup, dem, ['O1', 'O2'], ['D1', 'D2', 'D3']),
                             ['SBF por Vogel.', 'Solución óptima y ¿soluciones múltiples?'], method='V')
        except Exception:
            continue
        if 'Sí: la celda' in e['s']:
            ex.append(e); break
    for _ in range(1000):
        C = [[rng.randint(1, 10) for _ in range(4)] for _ in range(4)]
        h, s, t, i = hungarian(C, ['R1', 'R2', 'R3', 'R4'], ['A1', 'A2', 'A3', 'A4'], maximize=True)
        if i['iters'] >= 1:
            ex.append(ex_as('<p>Maximice el beneficio total de asignar:</p>' + data_html(C, ['R1', 'R2', 'R3', 'R4'], ['A1', 'A2', 'A3', 'A4']), ['Resuelva por el método húngaro.'], sp('Desarrollo', h)))
            break
    assert len(ex) == 3
    return {'clase': ASCL[6], 'ejemplos': [], 'ejercicios': ex}

BLOCKS = [
    ('sens', 'Sensibilidad', content_sens.build(), ['B⁻¹ y precios duales', 'Cambio en c<sub>j</sub>', 'Cambio en b y simplex dual', 'Nueva restricción', 'Nueva variable', 'Tipo certamen', 'Mini-certamen']),
    ('bb', 'Branch and Bound', content_bb.build(), ['Relajación lineal gráfica', 'El árbol de B&amp;B', 'Podas y cotas', 'Casos de certamen', 'Mini-certamen']),
    ('tr', 'Transporte', content_tr.build(), ['Modelo y balanceo', 'NO, costo mínimo y Vogel', 'Método u-v', 'Degeneración y múltiples', 'Producción, períodos y máximo', 'Mini-certamen']),
    ('tb', 'Transbordo', content_tb.build(), ['Tabla de transbordo', 'Casos especiales', 'Mini-certamen']),
    ('as', 'Asignación', content_as.build(), ['Método Húngaro', 'Prohibidas, ficticios y máximo', 'Variantes de tablas', 'Mini-certamen']),
    ('rep', 'Repaso', [simulacro(), repaso()], ['Simulacro C2 (80 min)', 'Formulario y errores frecuentes']),
]

def main():
    start = datetime.date(2026, 10, 22)
    out = []
    k = 0
    for key, name, days, titles in BLOCKS:
        assert len(days) == len(titles), (key, len(days), len(titles))
        for j, (d, t) in enumerate(zip(days, titles)):
            date = start + datetime.timedelta(days=k)
            d.update({'n': k + 1, 'date': date.isoformat(), 'block': key, 'blockName': name, 'title': t, 'dayInBlock': j + 1, 'blockLen': len(days)})
            out.append(d); k += 1
    assert out[-1]['date'] == '2026-11-17', out[-1]['date']
    json.dump(out, open('days.json', 'w'), ensure_ascii=False)
    print(len(out), sum(len(d['ejercicios']) for d in out), sum(len(d['ejemplos']) for d in out))

if __name__ == '__main__':
    main()
