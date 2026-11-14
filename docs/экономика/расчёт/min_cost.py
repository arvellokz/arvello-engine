import json, math, collections
d = json.load(open('/home/claude/work/cards.json'))
SHEET=2.75*1.83; HDF_SHEET=2.5*2.07; WASTE=1.15
P_SHEET={'W':14300,'K':16600}; P_DECOR=16800; P_HDF=7000; P_CUT=2000
P_EDGE=155+195
P_HINGE=666            # Samet INVO с доводчиком, artmebel 14.11
P_DRAWER=3307          # Samet Slidea 450, artmebel 14.11 (эконом)
HOLE=30; HOLES_PER_PART=5   # по движку: комод NST-101 — 346 отв. (без пилотных под шурупы) / ~70 деталей
ASSY={'KIT':39990,'WRD':19990}; DELIVERY=5000
TOP_PER_M=23500/3      # столешница 38 мм 3000×600, Евромаркет
ROD=1035+2*105; SLIDE_SET=24798
rows=[]
for m in d:
    c=m['card']; area=collections.defaultdict(float); hdf=edge=0; miss=[]
    for l in c['materials']:
        k=l['key'].split(':'); t=k[0]
        if t in('board','front'):
            th=int(k[1]); layers=1 if th<=18 else math.ceil(th/16); area[k[2]]+=l['qty']*layers
        elif t=='hdf': hdf+=l['qty']
        elif t=='edge': edge+=l['qty']
        elif t=='worktop': pass
        else: miss.append(t)
    hinge=drawers=0; extra=0; extra_names=[]
    for l in c['components']:
        if l['key']=='hw:hinge': hinge=l['qty']
        elif l['key']=='hw:drawer_set': drawers=l['qty']
        elif l['key']=='hw:rod': extra+=ROD*max(1,math.ceil(l['qty'])); extra_names.append('штанга')
        elif l['key']=='hw:sliding_set': extra+=SLIDE_SET; extra_names.append('купе')
        else: miss.append(l['key'])
    if any(l['key'].startswith('worktop') for l in c['materials']) or m['category']=='KIT':
        w=m['size'][0]/1000; extra+=math.ceil(w/3)*23500; extra_names.append('столешница')
        miss=[x for x in miss if x!='worktop']
    parts=next((l['qty'] for l in c['operations'] if l['key']=='OP-DRILL'),0)+5*drawers
    area['W']+=0.5*drawers; edge+=2.0*drawers
    price=lambda col:P_SHEET.get(col,P_DECOR)
    mat=sum(a*WASTE/SHEET*(price(col)+P_CUT) for col,a in area.items())+(hdf*WASTE/HDF_SHEET*(P_HDF+P_CUT) if hdf else 0)
    e=edge*1.1*P_EDGE; misc=0.04*(mat+e)
    holes=parts*HOLES_PER_PART*HOLE
    hw=hinge*P_HINGE+drawers*P_DRAWER+extra
    assy=ASSY.get(m['category'],10000)+DELIVERY
    tot=mat+e+misc+holes+hw+assy
    rows.append(dict(sku=m['sku'],name=m['name'],cat=m['category'],size='×'.join(map(str,m['size'])),mat=round(mat),edge=round(e),holes=round(holes),hw=round(hw),assy=assy,tot=round(tot/1000)*1000,miss=sorted(set(miss)),extra=extra_names,dr=int(drawers),hi=int(hinge)))
json.dump(rows,open('min.json','w'),ensure_ascii=False)
for r in sorted(rows,key=lambda r:(r['cat'],r['tot'])):
    print(r['cat'],r['sku'],r['name'],r['size'],'| плита',r['mat']//1000,'кромка',r['edge']//1000,'отв',r['holes']//1000,'фурн',r['hw']//1000,'сб+дост',r['assy']//1000,'| ИТОГО',r['tot']//1000,'|',','.join(r['extra']),'| нет:',','.join(r['miss']))
