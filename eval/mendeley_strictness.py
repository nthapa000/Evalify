# Where the type-C grader differs from the teacher: per question and per teacher mark (run: python eval/mendeley_strictness.py)
import json,collections
G=json.load(open('eval/reports/mendeley_sweep/grades.json'))
M={json.loads(l)['sheet_id']:json.loads(l) for l in open('eval/data/mendeley/manifest.jsonl')}
cfg='gemma-v2';pair='qwen+glm'
perq=collections.defaultdict(list);conf=collections.Counter();flags=collections.Counter()
for k,v in G.items():
    s,q,c,p=k.split('|')
    if c!=cfg or p!=pair: continue
    t=M[s]['gold'].get(q,{}).get('marks')
    if t is None: continue
    perq[q].append((t,v['marks']));conf[(t,v['marks'])]+=1
    if v.get('error'): flags['error']+=1
    if v.get('transcript_problem'): flags['transcript_problem']+=1
print('flags',dict(flags))
print('teacher mark -> model mark counts')
for t in sorted({a for a,_ in conf}):
    print(t, {m:n for (a,m),n in sorted(conf.items()) if a==t})
print('q n teacher_mean model_mean bias')
for q in sorted(perq,key=lambda x:int(x[1:])):
    l=perq[q];tm=sum(a for a,_ in l)/len(l);mm=sum(b for _,b in l)/len(l)
    print(q,len(l),round(tm,2),round(mm,2),round(mm-tm,2))
