# Per-reader read accuracy on EDU-CIRCUIT-HW vs the expert-transcript gold (run: python eval/edu_read_accuracy.py)
import json,re,sys
sys.path.insert(0,'backend')
R=json.load(open('eval/reports/edu_circuit/readings.json'))
M=[json.loads(l) for l in open('eval/data/edu_circuit/manifest.jsonl')]
num=re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')
def val(s):
    s=(s or '').replace(',','').replace('−','-').replace('$','')
    m=num.search(s); return float(m.group()) if m else None
srcs=['qwen','gemma','chandra>qwen','glm>qwen','paddle>qwen']
st={s:dict(n=0,ok=0,blank_ok=0,blank_n=0,miss=0,ghost=0,wrong=0) for s in srcs}
for m in M:
    r=R.get(m['id']);
    if not r: continue
    for k,g in m['gold'].items():
        gv=val(g)
        for s in srcs:
            x=st[s]; x['n']+=1
            rv=val(r[s]['values'].get(k,''))
            if gv is None:
                x['blank_n']+=1
                if rv is None: x['ok']+=1; x['blank_ok']+=1
                else: x['ghost']+=1
            elif rv is None: x['miss']+=1
            elif abs(rv-gv)<=1e-3*max(1,abs(gv)): x['ok']+=1
            else: x['wrong']+=1
print('| reader | values | read correctly | wrong number | missed (said blank) | invented (gold blank) |')
print('|---|---|---|---|---|---|')
for s in srcs:
    x=st[s]; n=x['n']
    print(f"| {s} | {n} | {x['ok']/n:.1%} | {x['wrong']} | {x['miss']} | {x['ghost']} |")
