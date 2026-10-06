import json,re
R=json.load(open('raw_hits.json',encoding='utf-8'))
def nt(t): return re.sub(r'[^a-z0-9]','',(t or '').lower())
recs=[];idx={};dupe={'doi':0,'arxiv':0,'exact_title':0,'norm_title':0}
for r in R:
    keys=[('doi',r['doi']),('arxiv',r['arxiv']),('exact_title',(r['title'] or '').strip().lower()),('norm_title',nt(r['title'])[:80])]
    hit=None
    for k,v in keys:
        if v and (k,v) in idx: hit=(k,idx[(k,v)]);break
    if hit:
        dupe[hit[0]]+=1; m=recs[hit[1]]
        m['srcs'].add(r['src']); m['fams'].add(r['fam'])
        for f in ('doi','arxiv'):
            if not m[f] and r[f]: m[f]=r[f]
        if len(r['abstract'])>len(m['abstract']): m['abstract']=r['abstract']
        if m['venue'] in ('','arXiv','arXiv (Cornell University)') and r['venue'] not in ('','arXiv','arXiv.org','arXiv (Cornell University)'): m['venue']=r['venue']
        i=hit[1]
    else:
        m=dict(r,srcs={r['src']},fams={r['fam']}); recs.append(m); i=len(recs)-1
    for k,v in keys:
        if v: idx[(k,v)]=i
print('raw',len(R),'unique',len(recs),'dupes removed',dupe)
# automated eligibility pre-screen on title+abstract
LLM=r'\b(llms?|large language models?|language models?|gpt-?\d|generative agents?|lm-based|foundation models?)\b'
HUM=r'\b(human (participants?|subjects?|players?|data|baseline|behaviou?rs?|counterparts?|decisions?)|participants|humans)\b'
GAME=r'(social dilemma|public goods?|prisoner|trust game|ultimatum|dictator|common[- ]pool|commons|scarc|surviv|cooperat|deception|deceptive|negotiat|game theor|behaviou?ral game|economic game|repeated game|turing test|resource)'
keep=[]
for m in recs:
    t=(m['title']+' . '+m['abstract']).lower()
    m['pre']= bool(re.search(LLM,t)) and bool(re.search(HUM,t)) and bool(re.search(GAME,t))
    if m['pre']: keep.append(m)
print('pass pre-screen',len(keep),'excluded',len(recs)-len(keep))
for m in recs: m['srcs']=sorted(m['srcs']); m['fams']=sorted(m['fams'])
json.dump(recs,open('dedup.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump(dupe,open('dedup_counts.json','w'))
with open('screen_titles.txt','w',encoding='utf-8') as f:
    for n,m in enumerate(keep): f.write(f"{n}\t{m['year']}\t{m['arxiv'] or m['doi'] or '-'}\t{m['title'][:150]}\n")
