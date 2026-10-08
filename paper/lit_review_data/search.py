import json,urllib.request,urllib.parse,time,re,xml.etree.ElementTree as ET,sys
UA={'User-Agent':'lit-review-script/1.0 (academic)'}
def fetch(u,tries=4):
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=90).read()
        except Exception as e:
            print('  retry',i,e,file=sys.stderr); time.sleep(5*(i+1))
    return None
DATE='submittedDate:[202301010000 TO 202610062359]'
# (family, arXiv query, S2 bulk query, OpenAlex search)
Q=[
 ('Q1-core', 'abs:(LLM OR "language model") AND abs:(human) AND abs:(scarcity OR commons OR "common-pool" OR survival OR "resource dilemma")',
  '("large language model" | LLM) + (human | participants) + (scarcity | commons | "common-pool" | survival)',
  'LLM agents human participants resource scarcity commons'),
 ('Q2-matched', 'abs:(LLM OR "language model") AND abs:("human participants" OR "human subjects" OR "human players" OR "human data") AND abs:("social dilemma" OR "public goods" OR "prisoner" OR "trust game" OR "cooperation")',
  '(LLM | "language model") + ("human participants" | "human subjects" | "human players") + ("social dilemma" | "public goods" | cooperation)',
  'LLM agents versus human participants social dilemma cooperation comparison'),
 ('Q3-deception', 'abs:(LLM OR "language model") AND abs:(deception OR deceptive OR lying) AND abs:(game OR "social dilemma" OR negotiation) AND abs:(human)',
  '(LLM | "language model") + (deception | deceptive | lying) + (game | negotiation) + human',
  'LLM agent deception game human comparison'),
 ('Q4-distinguish', 'abs:("Turing test" OR distinguishab* OR "human-likeness" OR "human likeness" OR "detect AI") AND abs:(LLM OR "language model") AND abs:(game OR behavio* OR agent)',
  '("Turing test" | distinguishability | "human-likeness") + (LLM | "language model") + (game | behavioral)',
  'behavioral Turing test LLM agents game distinguish human'),
 ('Q5-llm-commons', 'abs:(LLM OR "language model") AND abs:(agents OR "multi-agent") AND abs:("common-pool" OR commons OR "resource scarcity" OR "scarce resource" OR "tragedy of the commons" OR sustainability)',
  '(LLM | "language model") + (agents | "multi-agent") + ("common-pool" | commons | "resource scarcity" | "tragedy of the commons")',
  'LLM multi-agent commons common-pool resource sustainability'),
]
out=[];log=[]
for fam,aq,sq,oq in Q:
    # arXiv
    u='https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':f'({aq}) AND {DATE}','max_results':300,'sortBy':'relevance'})
    raw=fetch(u); n=0
    if raw:
        ns={'a':'http://www.w3.org/2005/Atom','o':'http://a9.com/-/spec/opensearch/1.1/'}
        r=ET.fromstring(raw); tot=r.find('o:totalResults',ns).text
        for e in r.findall('a:entry',ns):
            out.append(dict(src='arXiv',fam=fam,arxiv=e.find('a:id',ns).text.split('/abs/')[-1].split('v')[0],doi=None,title=' '.join(e.find('a:title',ns).text.split()),year=e.find('a:published',ns).text[:4],venue='arXiv',abstract=' '.join(e.find('a:summary',ns).text.split())));n+=1
        log.append((fam,'arXiv',aq,tot,n))
    time.sleep(3.5)
    # Semantic Scholar bulk
    u='https://api.semanticscholar.org/graph/v1/paper/search/bulk?'+urllib.parse.urlencode({'query':sq,'year':'2023-2026','fields':'title,year,externalIds,venue,abstract'})
    raw=fetch(u); n=0
    if raw:
        d=json.loads(raw)
        for p in d.get('data',[])[:1000]:
            x=p.get('externalIds') or {}
            out.append(dict(src='S2',fam=fam,arxiv=x.get('ArXiv'),doi=(x.get('DOI') or '').lower() or None,title=p['title'],year=str(p.get('year')),venue=p.get('venue') or '',abstract=p.get('abstract') or ''));n+=1
        log.append((fam,'SemanticScholar',sq,d.get('total'),n))
    time.sleep(3.5)
    # OpenAlex
    u='https://api.openalex.org/works?'+urllib.parse.urlencode({'search':oq,'filter':'from_publication_date:2023-01-01,to_publication_date:2026-10-06','per-page':200,'mailto':'lit-review@example.org'})
    raw=fetch(u); n=0
    if raw:
        d=json.loads(raw)
        for w in d['results']:
            ii=w.get('abstract_inverted_index') or {}
            ab=' '.join(k for k,_ in sorted(((k,p) for k,ps in ii.items() for p in ps),key=lambda z:z[1]))
            doi=(w.get('doi') or '').replace('https://doi.org/','').lower() or None
            ax=None
            if doi and doi.startswith('10.48550/arxiv.'): ax=doi.split('arxiv.')[1]
            out.append(dict(src='OpenAlex',fam=fam,arxiv=ax,doi=doi,title=w.get('title') or '',year=str(w.get('publication_year')),venue=((w.get('primary_location') or {}).get('source') or {}).get('display_name') or '',abstract=ab));n+=1
        log.append((fam,'OpenAlex',oq,d['meta']['count'],n))
    time.sleep(1)
json.dump(out,open('raw_hits.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump(log,open('search_log.json','w'),ensure_ascii=False)
for l in log: print(l[0],l[1],'total=',l[3],'retrieved=',l[4])
print('raw records',len(out))
