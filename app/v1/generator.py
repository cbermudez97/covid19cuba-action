from json import load, dump
from math import log10
from .countries import countries
from .utils import dump_util


def generate(debug=False):
    data_cuba = load(open('data/covid19-cuba.json', encoding='utf-8'))
    data_world = load(open('data/paises-info-dias.json', encoding='utf-8'))
    function_list = [
        resume,
        cases_by_sex,
        cases_by_mode_of_contagion,
        curves_evolution,
        evolution_of_cases_by_days,
        evolution_of_deaths_by_days,
        evolution_of_recovered_by_days,
        distribution_by_age_ranges,
        cases_by_nationality,
        distribution_by_nationality_of_foreign_cases,
        list_of_tests_performed,
        tests_by_days,
        affected_provinces,
        affected_municipalities,
        comparison_of_accumulated_cases,
        map_data,
        updated,
        note,
        top_20_accumulated_countries
    ]
    dump({
        f.__name__: dump_util('api/v1', f,
                              data_cuba=data_cuba,
                              data_world=data_world,
                              debug=debug)
        for f in function_list},
        open(f'api/v1/all.json', mode='w', encoding='utf-8'),
        ensure_ascii=False,
        indent=2 if debug else None,
        separators=(',', ': ') if debug else (',', ':'))


def resume(data):
    days = list(data['data_cuba']['casos']['dias'].values())
    diagnosed = sum((
        len(x['diagnosticados'])
        for x in days
        if 'diagnosticados' in x
    ))
    deaths = sum((
        x['muertes_numero']
        for x in days
        if 'muertes_numero' in x
    ))
    evacuees = sum((
        x['evacuados_numero']
        for x in days
        if 'evacuados_numero' in x
    ))
    recovered = sum((
        x['recuperados_numero']
        for x in days
        if 'recuperados_numero' in x
    ))
    active = diagnosed - deaths - evacuees - recovered
    return [
        {'name': 'Diagnosticados', 'value': diagnosed},
        {'name': 'Activos', 'value': active},
        {'name': 'Recuperados', 'value': recovered},
        {'name': 'Evacuados', 'value': evacuees},
        {'name': 'Fallecidos', 'value': deaths}
    ]


def cases_by_sex(data):
    result = {'hombre': 0, 'mujer': 0, 'no reportado': 0}
    days = list(data['data_cuba']['casos']['dias'].values())
    days.sort(key=lambda x: x['fecha'])
    for diagnosed in (x['diagnosticados'] for x in days if 'diagnosticados' in x):
        for item in diagnosed:
            if item.get('sexo') is None:
                result['no reportado'] += 1
            else:
                try:
                    result[item.get('sexo')] += 1
                except KeyError:
                    result[item.get('sexo')] = 1
    pretty = {
        'hombre': 'Hombres',
        'mujer': 'Mujeres',
        'no reportado': 'No Reportados'
    }
    hard = {
        'hombre': 'men',
        'mujer': 'women',
        'no reportado': 'unknown'
    }
    return {
        hard[key] if key in hard else key: {
            'name': pretty[key] if key in pretty else key.title(),
            'value': result[key]
        }
        for key in result
    }


def cases_by_mode_of_contagion(data):
    result = {
        'importado': 0,
        'introducido': 0,
        'autoctono': 0,
        'desconocido': 0
    }
    days = list(data['data_cuba']['casos']['dias'].values())
    days.sort(key=lambda x: x['fecha'])
    for diagnosed in (x['diagnosticados'] for x in days if 'diagnosticados' in x):
        for item in diagnosed:
            if item.get('contagio') is None:
                result['desconocido'] += 1
            else:
                try:
                    result[item.get('contagio')] += 1
                except KeyError:
                    result[item.get('contagio')] = 1
    pretty = {
        'importado': 'Importados',
        'introducido': 'Introducidos',
        'autoctono': 'Autóctonos',
        'desconocido': 'Desconocidos'
    }
    hard = {
        'importado': 'imported',
        'introducido': 'inserted',
        'autoctono': 'autochthonous',
        'desconocido': 'unknown'
    }
    return {
        hard[key] if key in hard else key: {
            'name': pretty[key] if key in pretty else key.title(),
            'value': result[key]
        }
        for key in result
    }


def evolution_of_cases_by_days(data):
    accumulated = [0]
    daily = [0]
    date = []
    actives = []
    total = 0
    deaths = 0
    recover = 0
    evacuees = 0
    days = list(data['data_cuba']['casos']['dias'].values())
    days.sort(key=lambda x: x['fecha'])
    for x in days:
        accumulated.append(accumulated[-1])
        daily.append(0)
        if x.get('diagnosticados'):
            accumulated[-1] += len(x['diagnosticados'])
            daily[-1] += len(x['diagnosticados'])
        total += len(x['diagnosticados']) if 'diagnosticados' in x else 0
        deaths += x['muertes_numero'] if 'muertes_numero' in x else 0
        recover += x['recuperados_numero'] if 'recuperados_numero' in x else 0
        evacuees += x['evacuados_numero'] if 'evacuados_numero' in x else 0
        actives.append(total - deaths - recover - evacuees)
        date.append(x['fecha'])
    return {
        'accumulated': {
            'name': 'Casos acumulados',
            'values': accumulated[1:]
        },
        'daily': {
            'name': 'Casos en el día',
            'values': daily[1:]
        },
        'active': {
            'name': 'Casos activos',
            'values': actives
        },
        'date': {
            'name': 'Fecha',
            'values': date
        }
    }


def evolution_of_deaths_by_days(data):
    accumulated = [0]
    daily = [0]
    date = []
    days = list(data['data_cuba']['casos']['dias'].values())
    days.sort(key=lambda x: x['fecha'])
    for x in days:
        accumulated.append(accumulated[-1])
        daily.append(0)
        if x.get('muertes_numero'):
            accumulated[-1] += x['muertes_numero']
            daily[-1] += x['muertes_numero']
        date.append(x['fecha'])
    return {
        'accumulated': {
            'name': 'Fallecimientos acumulados',
            'values': accumulated[1:]
        },
        'daily': {
            'name': 'Fallecimientos en el día',
            'values': daily[1:]
        },
        'date': {
            'name': 'Fecha',
            'values': date
        }
    }


def evolution_of_recovered_by_days(data):
    accumulated = [0]
    daily = [0]
    date = []
    days = list(data['data_cuba']['casos']['dias'].values())
    days.sort(key=lambda x: x['fecha'])
    for x in days:
        accumulated.append(accumulated[-1])
        daily.append(0)
        if x.get('recuperados_numero'):
            accumulated[-1] += x['recuperados_numero']
            daily[-1] += x['recuperados_numero']
        date.append(x['fecha'])
    return {
        'accumulated': {
            'name': 'Altas acumuladas',
            'values': accumulated[1:]
        },
        'daily': {
            'name': 'Altas en el día',
            'values': daily[1:]
        },
        'date': {
            'name': 'Fecha',
            'values': date
        }
    }


def distribution_by_age_ranges(data):
    result = [0] * 5
    keys = ['0-18', '19-40', '41-60', '>=61', 'Desconocido']
    hard = ['0-18', '19-40', '41-60', '>=61', 'unknown']
    days = list(data['data_cuba']['casos']['dias'].values())
    for diagnosed in (x['diagnosticados'] for x in days if 'diagnosticados' in x):
        for item in diagnosed:
            age = item.get('edad')
            if age is None:
                result[4] += 1
            elif 0 <= age <= 18:
                result[0] += 1
            elif 18 < age <= 40:
                result[1] += 1
            elif 40 < age <= 60:
                result[2] += 1
            else:
                result[3] += 1
    return [
        {'code': item[0], 'name': item[1][0], 'value': item[1][1]}
        for item in zip(hard, zip(keys, result))
    ]


def cases_by_nationality(data):
    pretty = {
        'foreign': 'Extranjeros',
        'cubans': 'Cubanos',
        'unknown': 'No reportados'
    }
    result = {'foreign': 0, 'cubans': 0, 'unknown': 0}
    days = list(data['data_cuba']['casos']['dias'].values())
    for diagnosed in (x['diagnosticados'] for x in days if 'diagnosticados' in x):
        for item in diagnosed:
            country = item.get('pais')
            if country is None:
                result['unknown'] += 1
            elif country == 'cu':
                result['cubans'] += 1
            else:
                result['foreign'] += 1
    return {
        key: {
            'name': pretty[key] if key in pretty else key.title(),
            'value': result[key]
        }
        for key in result
    }


def distribution_by_nationality_of_foreign_cases(data):
    result = {}
    days = list(data['data_cuba']['casos']['dias'].values())
    for diagnosed in (x['diagnosticados'] for x in days if 'diagnosticados' in x):
        for item in diagnosed:
            country = item['pais']
            if country == 'cu':
                continue
            try:
                result[country] += 1
            except KeyError:
                result[country] = 1
    return [
        {
            'code': key,
            'name': countries[key] if key in countries else key.title(),
            'value': result[key]
        }
        for key in result
    ]


def list_of_tests_performed(data):
    total = 0
    positive = 0
    days = list(data['data_cuba']['casos']['dias'].values())
    for day in (x for x in days if 'diagnosticados' in x):
        positive += len(day['diagnosticados'])
        if 'tests_total' in day:
            total = max(total, day['tests_total'])
    return {
        'positive': {
            'name': 'Tests Positivos',
            'value': positive
        },
        'negative': {
            'name': 'Tests Negativos',
            'value': total - positive
        },
        'total': {
            'name': 'Total de Tests',
            'value': total
        }
    }


def tests_by_days(data):
    ntest_days = []
    ntest_negative = []
    ntest_positive = []
    ntest_cases = []
    prev_test_cases = 0
    prev_test_negative = 0
    prev_test_positive = 0
    total = 0
    days = list(data['data_cuba']['casos']['dias'].values())
    for day in (x for x in days if 'diagnosticados' in x):
        total += len(day['diagnosticados'])
        if 'tests_total' in day:
            prev_test_cases = day['tests_total']
            test_negative = day['tests_total'] - total
            prev_test_negative = test_negative
            prev_test_positive = total
            break
    for day in (x for x in days if 'diagnosticados' in x):
        total += len(day['diagnosticados'])
        if 'tests_total' in day:
            ntest_days.append(day['fecha'])
            ntest_cases.append(day['tests_total'] - prev_test_cases)
            prev_test_cases = day['tests_total']
            test_negative = day['tests_total'] - total
            ntest_negative.append(test_negative - prev_test_negative)
            prev_test_negative = test_negative
            ntest_positive.append(total - prev_test_positive)
            prev_test_positive = total
    return {
        'date': {
            'name': 'Fecha',
            'values': ntest_days[1:]
        },
        'negative': {
            'name': 'Tests Negativos',
            'values': ntest_negative[1:]
        },
        'positive': {
            'name': 'Tests Positivos',
            'values': ntest_positive[1:]
        },
        'total': {
            'name': 'Total de Tests',
            'values': ntest_cases[1:]
        }
    }


def affected_provinces(data):
    counter = {}
    total = 0
    days = list(data['data_cuba']['casos']['dias'].values())
    diagnosed = [x['diagnosticados'] for x in days if 'diagnosticados' in x]
    for patients in diagnosed:
        for p in patients:
            dpacode = 'dpacode_provincia_deteccion'
            try:
                counter[p[dpacode]]['value'] += 1
                counter[p[dpacode]]['name'] = p['provincia_detección']
            except KeyError:
                counter[p[dpacode]] = {
                    'value': 1,
                    'name': p['provincia_detección']
                }
            total += 1
    result = []
    result_list = list(counter.values())
    result_list.sort(key=lambda x: x['value'], reverse=True)
    for item in result_list:
        item['total'] = total
        result.append(item)
    return result


def affected_municipalities(data):
    counter = {}
    total = 0
    days = list(data['data_cuba']['casos']['dias'].values())
    diagnosed = [x['diagnosticados'] for x in days if 'diagnosticados' in x]
    for patients in diagnosed:
        for p in patients:
            dpacode = 'dpacode_municipio_deteccion'
            try:
                counter[p[dpacode]]['value'] += 1
                counter[p[dpacode]]['name'] = p['municipio_detección']
                counter[p[dpacode]]['province'] = p['provincia_detección']
            except KeyError:
                counter[p[dpacode]] = {
                    'value': 1,
                    'name': p['municipio_detección'],
                    'province': p['provincia_detección']
                }
            total += 1
    result = []
    result_list = list(counter.values())
    result_list.sort(key=lambda x: x['value'], reverse=True)
    result_list = result_list[:10]
    for item in result_list:
        item['total'] = total
        result.append(item)
    return result


def map_data(data):
    muns = {}
    pros = {}
    days = list(data['data_cuba']['casos']['dias'].values())
    diagnosed = [x['diagnosticados'] for x in days if 'diagnosticados' in x]
    for patients in diagnosed:
        for p in patients:
            try:
                muns[p['dpacode_municipio_deteccion']] += 1
            except KeyError:
                muns[p['dpacode_municipio_deteccion']] = 1
            try:
                pros[p['dpacode_provincia_deteccion']] += 1
            except KeyError:
                pros[p['dpacode_provincia_deteccion']] = 1
    total = 0
    max_muns = 0
    max_pros = 0
    for key in muns:
        if key and muns[key] > max_muns:
            max_muns = muns[key]
    for key in pros:
        if key and pros[key] > max_muns:
            max_pros = pros[key]
        if key:
            total += pros[key]
    return {
        'muns': muns,
        'pros': pros,
        'genInfo': {
            'max_muns': max_muns,
            'max_pros': max_pros,
            'total': total
        }
    }


def top_20_accumulated_countries(data):
    countries_info = comparison_of_accumulated_cases(data)['countries_info']
    result = []
    for key in countries_info:
        value = countries_info[key]
        confirmed = value['confirmed'][-1]
        recovered = value['recovered'][-1]
        deaths = value['deaths'][-1]
        result.append((confirmed, recovered, deaths, key))
    result.sort(reverse=True)
    return list(map(lambda x: {
        'name': x[3],
        'value': x[0],
        'confirmed': x[0],
        'recovered': x[1],
        'deaths': x[2],
    }, result[:20]))


def comparison_of_accumulated_cases(data):
    world = data['data_world']
    confirmed = [0]
    daily = [0]
    recovered = [0]
    deaths = [0]
    actives = []
    _total = 0
    _deaths = 0
    _recover = 0
    _evacuees = 0
    days = list(data['data_cuba']['casos']['dias'].values())
    days.sort(key=lambda x: x['fecha'])
    for day in days:
        confirmed.append(confirmed[-1])
        recovered.append(recovered[-1])
        deaths.append(deaths[-1])
        daily.append(0)
        if day.get('diagnosticados'):
            confirmed[-1] += len(day['diagnosticados'])
            daily[-1] += len(day['diagnosticados'])
        if day.get('recuperados_numero'):
            recovered[-1] += day['recuperados_numero']
        if day.get('muertes_numero'):
            deaths[-1] += day['muertes_numero']
        _total += len(day['diagnosticados']) if 'diagnosticados' in day else 0
        _deaths += day['muertes_numero'] if 'muertes_numero' in day else 0
        _recover += day['recuperados_numero'] if 'recuperados_numero' in day else 0
        _evacuees += day['evacuados_numero'] if 'evacuados_numero' in day else 0
        actives.append(_total - _deaths - _recover - _evacuees)
    world['paises']['Cuba'] = confirmed[1:]
    for key in world['paises_info']:
        _value = world['paises_info'][key]
        _confirmed = _value['confirmed']
        _recovered = _value['recovered']
        _deaths = _value['deaths']
        _daily = [confirmed[0]]
        _active = []
        for i in range(1, len(_confirmed)):
            _daily.append(_confirmed[i] - _confirmed[i - 1])
        for i in range(len(_confirmed)):
            _active.append(_confirmed[i] - _deaths[i] - _recovered[i])
        _value['daily'] = _daily
        _value['active'] = _active
    world['paises_info']['Cuba']['confirmed'] = confirmed[1:]
    world['paises_info']['Cuba']['recovered'] = recovered[1:]
    world['paises_info']['Cuba']['deaths'] = deaths[1:]
    world['paises_info']['Cuba']['daily'] = daily[1:]
    world['paises_info']['Cuba']['active'] = actives
    return {
        'countries': world['paises'],
        'countries_info': world['paises_info'],
        'updated': world['dia-actualizacion']
    }


def updated(data):
    days = list(data['data_cuba']['casos']['dias'].values())
    days.sort(key=lambda x: x['fecha'])
    return days[-1]['fecha']


def note(data):
    return data['data_cuba']['note-text'] if 'note-text' in data['data_cuba'] else ''


def curves_evolution(data):
    dataw = data['data_world']
    ntop = 20
    curves = {}
    def scaleX(x): return 0 if x == 0 else log10(x)
    def scaleY(y): return 0 if y == 0 else log10(y)
    for c, dat in dataw['paises'].items():
        weeksum = 0
        weeks = []
        accum = []
        prevweek = 0
        total = 0
        ctotal = 0
        for i, (day, day1) in enumerate(zip(dat[:-1], dat[1:])):
            ctotal = day1
            if (i + 1) % 7 == 0 and day > 30:
                total = day
                weeksum = total - prevweek
                weeks.append(scaleY(weeksum))
                weeksum = 0
                prevweek = total
                accum.append(scaleX(total))
        curves[c] = {
            'weeks': weeks,
            'cummulative_sum': accum,
            'total': total,
            'ctotal': ctotal
        }
    return {
        i: j
        for i, j in (list(
            sorted(
                curves.items(),
                key=lambda x: x[1]['ctotal'],
                reverse=True
            )
        )[:ntop] + [('Cuba', curves['Cuba'])])
    }
