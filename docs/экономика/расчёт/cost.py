import json, math, csv, collections
d = json.load(open('/home/claude/work/cards.json'))
SHEET = 2.75*1.83; HDF_SHEET = 2.5*2.07; WASTE = 1.15
P_SHEET = {'W': 14300, 'K': 16600}          # смета ДСП Центра 14.11
P_DECOR = 16800                              # Дуб Бунратти, смета; для O, C, G — как декор (допущение)
P_HDF = 7000; P_CUT = 2000
P_EDGE = 155 + 195                           # кромка ПВХ ср. (110 и 200) + наклейка 195 (прайс dspc.kz)
P_HINGE = 600                                # Samet Master soft close 581 / Boyard 295–695
P_DRAWER = {'эконом': 1402, 'стандарт': 2901, 'комфорт': 10816}   # artmebel.kz
ASSY = {'KIT': 39990, 'WRD': 19990}          # eco-service.kz; остальное — 10 000 (profi.kz «от 10 000»)
DELIVERY = 5000                              # допущение
HOLE = 220; HOLES_PER_PART = 3               # прайс dspc.kz; 3 отв./деталь — по комоду NST-101 (~200 отв. на 66 дет.)
RU = {'tube':'металл (труба)','fabric':'ткань/обивка','stone':'камень','glass':'стекло','mirror':'зеркало','beam':'брус/массив','worktop':'столешница',
      'hw:handle':'ручки','hw:rod':'штанга','hw:led':'подсветка','hw:gola':'профиль Gola','hw:sliding_set':'система купе','hw:lift':'подъёмник кровати',
      'hw:flap_lift':'подъёмник фасада','hw:leg':'ножки','hw:caster':'колёса','hw:sink':'раковина','hw:faucet':'смеситель','hw:hinge_glass':'петли стекла',
      'hw:alu':'алюм. профиль','hw:cable_tray':'кабель-канал','hw:cable_box':'лючок','hw:charger':'зарядка','hw:sconce':'бра','hw:hook':'крючки',
      'hw:bracket':'кронштейны','hw:lock':'замок','hw:slat':'ламели'}
rows = []
for m in d:
    c = m['card']; area = collections.defaultdict(float); thick = set(); hdf = 0; edge = 0; miss = collections.OrderedDict()
    for l in c['materials']:
        k = l['key'].split(':'); t = k[0]
        if t in ('board', 'front'):
            th = int(k[1]); col = k[2]
            layers = 1 if th <= 18 else math.ceil(th/16)       # толще 18 — склейка из 16 мм
            if th not in (16, 18): thick.add(th)
            area[col] += l['qty']*layers
        elif t == 'hdf': hdf += l['qty']
        elif t == 'edge': edge += l['qty']
        else: miss[RU.get(t, t)] = 1
    hinge = drawers = 0
    for l in c['components']:
        if l['key'] == 'hw:hinge': hinge = l['qty']
        elif l['key'] == 'hw:drawer_set': drawers = l['qty']
        else: miss[RU.get(l['key'], l['key'])] = 1
    parts = next((l['qty'] for l in c['operations'] if l['key'] == 'OP-DRILL'), 0) + 5*drawers
    area['W'] += 0.5*drawers; edge += 2.0*drawers      # короб ящика из белой ЛДСП 16 (по комоду NST-101: 0,5 м² и 2 м кромки на ящик)
    price = lambda col: P_SHEET.get(col, P_DECOR)
    sheets = {col: math.ceil(a*WASTE/SHEET) for col, a in area.items()}
    hs = math.ceil(hdf*WASTE/HDF_SHEET) if hdf else 0
    mat_one = sum(n*price(col) for col, n in sheets.items()) + hs*P_HDF
    cut_one = (sum(sheets.values()) + hs)*P_CUT
    mat_batch = sum(a*WASTE/SHEET*(price(col)+P_CUT) for col, a in area.items()) + (hdf*WASTE/HDF_SHEET*(P_HDF+P_CUT) if hdf else 0)
    e = edge*1.1*P_EDGE
    assy = ASSY.get(m['category'], 10000) + DELIVERY
    misc = 0.04*(mat_one + e)
    base_one = mat_one + cut_one + e + misc + hinge*P_HINGE + assy
    base_batch = mat_batch + e + misc + hinge*P_HINGE + assy
    r = dict(sku=m['sku'], name=m['name'], cat=m['category'], size='×'.join(map(str, m['size'])),
             sheets=sum(sheets.values()), hdf=hs, edge=round(edge, 1), drawers=int(drawers), hinges=int(hinge),
             dspc=round(mat_one+cut_one+e), drill=round(parts*HOLES_PER_PART*HOLE),
             miss=', '.join(miss), thick=','.join(map(str, sorted(thick))))
    for lv, p in P_DRAWER.items():
        r['one_'+lv] = round((base_one + drawers*p)/1000)*1000
        r['batch_'+lv] = round((base_batch + drawers*p)/1000)*1000
    rows.append(r)
json.dump(rows, open('/home/claude/work/cost.json', 'w'), ensure_ascii=False)
out = '/home/claude/arvello-engine/docs/экономика/'
with open(out+'2026-11-14_себестоимость_36_моделей.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['Артикул','Модель','Категория','Габарит Ш×Г×В, мм','Листов ЛДСП','Листов ХДФ','Кромка, м','Ящиков','Петель','ДСП Центр: плита+распил+кромка, ₸','Присадка в ДСП Центре (опция), ₸',
                'Итого один заказ: эконом','стандарт','комфорт','Итого партией: эконом','стандарт','комфорт','Не посчитано (нет цены / не ДСП Центр)','Толщины не 16 мм (склейка)'])
    for r in rows: w.writerow([r['sku'],r['name'],r['cat'],r['size'],r['sheets'],r['hdf'],r['edge'],r['drawers'],r['hinges'],r['dspc'],r['drill'],r['one_эконом'],r['one_стандарт'],r['one_комфорт'],r['batch_эконом'],r['batch_стандарт'],r['batch_комфорт'],r['miss'],r['thick']])
f = lambda x: f'{x//1000}'
import sys
for r in rows: print(r['sku'], r['name'], r['size'], r['sheets'], r['hdf'], r['drawers'], r['hinges'], f(r['dspc']), '|', f(r['one_эконом']), f(r['one_стандарт']), f(r['one_комфорт']), '| партия', f(r['batch_эконом']), '| прис', f(r['drill']), '|', r['miss'], '|', r['thick'])
