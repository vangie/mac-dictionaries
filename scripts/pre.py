import re, html as H
import lxml.html
PY=r"[a-zA-Zāáǎàēéěèīíǐìōóǒòūúǔùüǖǘǚǜńňḿêɡ]+"
ZY=r"[ㄅ-ㄩˉˊˇˋ˙]+"
READ=re.compile(rf"^\s*({PY}(?:\s+{PY})*)\s+({ZY})\s*$")
def E(s): return H.escape(s,quote=False)
def cells(tr): return tr.findall('td')
def txt(td): return td.text_content()
def lines(td):
    h=lxml.html.tostring(td,encoding='unicode')
    h=re.sub(r'^<td[^>]*>|</td>$','',h.strip())
    return [H.unescape(re.sub(r'<[^>]+>','',x)) for x in re.split(r'<br\s*/?>',h)]

def xinhua(k, v):
    doc=lxml.html.fragment_fromstring(v,create_parent='div')
    secs=[]; meta=[]; inmeta=False
    for tr in doc.iter('tr'):
        tds=cells(tr)
        if len(tds)==1: inmeta=True; continue
        if len(tds)<2: continue
        lab=txt(tds[0]).strip()
        if inmeta:
            l=lab.split()[0] if re.search(r'[\u4e00-\u9fff]',lab) else lab
            meta.append((l,txt(tds[1]).strip())); continue
        l=re.split(r'\s|<',lab)[0].replace('解析','解释')
        secs.append((l,lines(tds[1])))
    reads=[]; out=[]
    norm=lambda ls:re.sub(r'\s','',''.join(ls))
    if len(secs)==2 and norm(secs[0][1])==norm(secs[1][1]): secs=secs[:1]
    for li,(lab,ls) in enumerate(secs):
        out.append(f'<div class="sect"><span class="lbl">{E(lab)}</span></div>')
        for raw in ls:
            s=raw.replace('\t',' ').strip().strip('\u3000').strip()
            if not s: continue
            s2=s
            if s2.startswith('◎'): s2=s2[1:].strip()
            if s2==k: continue
            if s2.startswith(k) and READ.match(s2[len(k):].replace('\u3000',' ')):
                s2=s2[len(k):]
            m=READ.match(s2.replace('\u3000',' '))
            if m:
                r=f'{m.group(1)} {m.group(2)}'
                if li==0 and r not in reads: reads.append(r)
                out.append(f'<div class="rd{" b" if li==0 else ""}">{E(r)}</div>'); continue
            # trad form + pinyin e.g. 書 shū
            m=re.match(rf'^(\S{{1,2}})\s+({PY})$',s2)
            if m: out.append(f'<div class="rd">{E(s2)}</div>'); continue
            if s2=='词性变化': out.append(f'<div class="sect"><span class="lbl">词性变化</span></div>'); continue
            m=re.match(r'^〈(.{1,3})〉$',s2)
            if m: out.append(f'<div class="pos"><span class="lbl">{E(m.group(1))}</span></div>'); continue
            if re.match(r'^\[[^\]]*\]',s2):
                out.append(f'<div class="en">{E(s2)}</div>'); continue
            if raw.startswith('     ') or re.search(r'--\s*\S*《',s2) and len(s2)<200 and not re.match(r'^\(\d+\)',s2):
                out.append(f'<div class="cit">{E(s2)}</div>'); continue
            m=re.match(r'^(\(\d+\)|\d+\.)\s*(.*)$',s2)
            if m:
                body=E(m.group(2))
                if re.match(r'^[(（](形声|会意|象形|指事|假借|转注|本义)',m.group(2)): body=f'<span class="ety">{body}</span>'
                body=re.sub(r'\[([^\]]*)\]',r'<span class="en">[\1]</span>',body)
                out.append(f'<div class="sn"><span class="num">{E(m.group(1).strip("().").strip())}</span>{body}</div>'); continue
            out.append(f'<div class="sn plain">{E(s2)}</div>')
    head=f'<div class="head"><span class="hw">{E(k)}</span>'+''.join(f'<span class="py">{E(r)}</span>' for r in reads)+'</div>'
    m=''
    if meta: m='<div class="meta">'+'　'.join(f'{E(a)} {E(b)}' for a,b in meta)+'</div>'
    if len(reads)<=1: out=[o for o in out if not o.startswith('<div class="rd b"')]
    return head+m+''.join(out)

def zh(lab):
    lab=lab.strip().rstrip(':：').strip()
    parts=[p.strip() for p in lab.split('/')]
    ch=[p for p in parts if re.search(r'[\u4e00-\u9fff]',p)]
    if ch:
        p=ch[-1]; p=re.sub(r'\s*[A-Za-z][A-Za-z .()\-]*$','',p).strip() or p
        return p
    return lab
def bujian(k, v):
    v=re.sub(r'(?is)<style.*?</style>','',v).replace("<tr'>","<tr>")
    v=re.sub(r'(?is)<hr>\s*<p><a href=.gdlookup.*?</p>','',v)
    doc=lxml.html.fragment_fromstring(v,create_parent='div')
    out=[f'<div class="head"><span class="hw">{E(k)}</span></div>']
    tbl=doc.find('.//table')
    if tbl is not None:
        for tr in tbl.findall('tr'):
            tds=cells(tr)
            if not tds: continue
            if len(tds)==1:
                inner=tds[0]
                if inner.get('colspan') and not inner.findall('.//div'):
                    lab=zh(lines(inner)[0]); out.append(f'<div class="sect"><span class="lbl">{E(lab)}</span></div>')
                else:
                    h=lxml.html.tostring(inner,encoding='unicode'); h=re.sub(r'^<td[^>]*>|</td>$','',h.strip())
                    out.append(f'<div class="combo">{h}</div>')
                continue
            lab=' '.join(x for x in lines(tds[0]))
            if 'Character' in lab: continue
            h=lxml.html.tostring(tds[1],encoding='unicode'); h=re.sub(r'^<td[^>]*>|</td>$','',h.strip())
            l=zh(lab)
            out.append(f'<div class="row"><span class="k">{E(l)}</span> {h}</div>')
        tbl.drop_tree()
    rest=lxml.html.tostring(doc,encoding='unicode')
    rest=re.sub(r'^<div>|</div>$','',rest.strip())
    rest=rest.replace(' / 异体字  National variants:','异体字：').replace(' Simp.','').replace(' Trad.','').replace(' Jp.','').replace(' Kor.','').replace(' Other','')
    out.append(f'<div class="legend">{rest}</div>')
    return ''.join(out)
