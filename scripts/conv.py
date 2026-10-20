import sys, re, os, html
from collections import OrderedDict
from pyglossary.plugin_lib.readmdict import MDX, MDD
import lxml.html, lxml.etree as ET

def parse_ss(s):
    lines=s.replace('\r','').split('\n'); d={}; i=0
    while i+2<len(lines)+1:
        k=lines[i].strip()
        if k.isdigit():
            d[k]=(lines[i+1] if i+1<len(lines) else '', lines[i+2] if i+2<len(lines) else ''); i+=3
        else: i+=1
    return d

def expand(txt, ss):
    if not ss: return txt
    parts=re.split(r'`(\d+)`', txt)
    out=[parts[0]]; end=''
    for j in range(1,len(parts),2):
        out.append(end); b,e=ss.get(parts[j],('',''))
        out.append(b); out.append(parts[j+1]); end=e
    out.append(end); return ''.join(out)

def xid(i): return f"e{i}"

def fix(h, links, imgdir):
    h=re.sub(r'(?is)<script.*?</script>','',h).replace("<tr'>",'<tr>')
    styles=re.findall(r'(?is)<style[^>]*>(.*?)</style>',h)
    h=re.sub(r'(?is)<style.*?</style>','',h)
    try: frag=lxml.html.fragment_fromstring(h, create_parent='div')
    except Exception: frag=lxml.html.fragment_fromstring(html.escape(h), create_parent='div')
    for el in frag.iter():
        if not isinstance(el.tag,str): continue
        for a in list(el.attrib):
            if a.startswith('on') or not re.match(r'^[A-Za-z_][\w.-]*$',a): del el.attrib[a]
        if not re.match(r'^[A-Za-z][\w.-]*$',el.tag): el.tag='span'
        if el.tag=='a':
            hr=el.get('href','')
            if hr.startswith('entry://'):
                t=hr[8:].split('#')[0]; el.set('href', 'x-dictionary:r:'+links.get(t,'')) if t in links else el.set('href','x-dictionary:d:'+t)
            elif hr.startswith(('javascript','gdlookup','bword','sound')): el.attrib.pop('href',None)
        if el.tag=='img':
            s=el.get('src','').replace('\\','/').lstrip('/')
            if s.startswith(('http','data:')): continue
            el.set('src', 'Images/'+s)
            imgdir.add(s)
        restyle(el)
    s=ET.tostring(frag, method='xml', encoding='unicode')
    s=s.replace('&nbsp;','\u00a0')
    s=re.sub(r'<span/>','',s)
    s=re.sub(r'<(span|a|div|b|i|sup|sub|p|td|tr|table|u|em|strong)(\s[^<>]*?)?/>',lambda m:f'<{m.group(1)}{m.group(2) or ""}></{m.group(1)}>',s)
    s=re.sub(r'(<span class="lbl">[^<]*</span>)\s*[：:]',r'\1',s)
    return s, styles


GRAY={'#a0a0a0','#696969','#8080c0','#989898','#c0c0c0','#808080','#a9a9a9','gray','grey'}
LBLC={'#000088','#600060'}
KEEP=('margin','text-indent','display','padding-left','float','width','height','vertical-align','text-align','line-height','white-space')
KEEPNAMED=False
def _color(el):
    c=(el.get('color') or '').lower()
    m=re.search(r'(?:^|;)\s*color\s*:\s*([^;]+)',el.get('style',''),re.I)
    if m: c=m.group(1).strip().lower()
    return c
def restyle(el):
    st=el.get('style','')
    c=_color(el)
    badge = bool(re.search(r'background|border\s*:',st,re.I)) and el.tag=='span' and len((el.text or '').strip())<=6 and not re.search(r'display\s*:\s*block',st)
    cls=None
    if el.tag=='font':
        sz=el.get('size','')
        t=(el.text or '')
        if c in LBLC or (c=='#ff4500' and t.startswith('【')) or (c=='#ff4500' and '★' in t): cls='lbl'
        elif sz.startswith('+'): cls='hw'
        elif c in GRAY or sz.startswith('-'): cls='sec'
        el.tag='span'
        if cls=='lbl':
            if el.text: el.text=el.text.lstrip('【')
            last=el[-1] if len(el) else None
            if last is not None and last.tail: last.tail=last.tail.rstrip('】')
            elif el.text: el.text=el.text.rstrip('】')
    elif badge: cls='lbl'
    elif c in GRAY: cls='sec'
    if cls: el.set('class',(el.get('class','')+' '+cls).strip())
    keep=[]
    for p in st.split(';'):
        if ':' not in p: continue
        k,v=p.split(':',1); k=k.strip().lower()
        if k.startswith(KEEP) and not cls=='lbl': keep.append(f'{k}:{v.strip()}')
        elif KEEPNAMED and k=='color' and not v.strip().startswith('#'): keep.append(f'color:{v.strip()}')
    if keep: el.set('style',';'.join(keep))
    else: el.attrib.pop('style',None)
    for a in ('color','face','size','bgcolor','bordercolor','border','background'):
        el.attrib.pop(a,None)
    if el.tag=='hr':
        el.tag='span'; el.attrib.clear(); el.set('class','sep')
def clean(c): return ''.join(ch for ch in c if ch in '\t\n\r' or ord(ch)>=0x20 and not 0xD800<=ord(ch)<=0xDFFF and ch not in '\ufffe\uffff')

T2S=None
PRE=None
def run(names, out, title, ident):
    entries=OrderedDict(); alias={}
    ss={}
    for n in names:
        m=MDX(f"in/{n}.mdx"); ss=parse_ss(m.header.get(b'StyleSheet',b'').decode('utf-8','replace'))
        for k,v in m.items():
            k=k.decode('utf-8','replace').strip(); v=v.decode('utf-8','replace').strip()
            if not k: continue
            if v.startswith('@@@LINK='):
                alias.setdefault(v[8:].strip(),[]).append(k); continue
            if PRE: v=PRE(k,v)
            entries.setdefault(k,[]).append(expand(v,ss) if ss else (v.replace('\r\n','\n').replace('\n','<br/>') if '<' not in v[:5] else v))
    links={k:xid(i) for i,k in enumerate(entries)}
    imgs=set(); css=OrderedDict()
    os.makedirs(out,exist_ok=True)
    with open(f"{out}/dict.xml",'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')
        for k,vs in entries.items():
            body=[]
            for v in vs:
                b,st=fix(clean(v),links,imgs); body.append(b)
                for s in st: css[s]=1
            idx={k}|set(alias.get(k,[]))
            if T2S: idx|={T2S.convert(x) for x in list(idx)}
            ek=html.escape(clean(k),quote=True)
            f.write(f'<d:entry id="{links[k]}" d:title="{ek}">')
            for x in idx: f.write(f'<d:index d:value="{html.escape(clean(x),quote=True)}" d:title="{ek}"/>')
            f.write((f'<h1 class="hw">{html.escape(clean(k))}</h1>' if HW else '')+''.join(body)+'</d:entry>\n')
        f.write('</d:dictionary>\n')
    base=open('base.css').read()
    open(f"{out}/dict.css",'w').write(base+'\n'+'\n'.join(css))
    open(f"{out}/dict.plist",'w').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleDevelopmentRegion</key><string>zh_CN</string>
<key>CFBundleIdentifier</key><string>com.vangie.cndict.{ident}</string>
<key>CFBundleName</key><string>{title}</string>
<key>CFBundleDisplayName</key><string>{title}</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>DCSDictionaryCopyright</key><string>Personal use. Source: lxs602/Chinese-Mandarin-Dictionaries</string>
<key>DCSDictionaryManufacturerName</key><string>vangie</string>
<key>DCSDictionaryUseSystemAppearance</key><true/>
</dict></plist>''')
    print(out, len(entries), sum(len(v) for v in alias.values()), len(imgs))
    return imgs

if __name__=='__main__':
    ident,title,*names=sys.argv[1:]
    HW = ident=='zdic'
    import conv as _c
    globals()['KEEPNAMED'] = ident=='bujian'
    import pre
    PRE={'xinhua':pre.xinhua,'bujian':pre.bujian}.get(ident)
    if ident in ('xinhua','bujian'): HW=False
    T2S=None
    if ident in ('moe','idiom','kangxi'):
        from opencc import OpenCC; T2S=OpenCC('t2s')
    imgs=run(names, f"out/{ident}", title, ident)
    for n in names:
        if os.path.exists(f"in/{n}.mdd") and not os.environ.get('NOIMG'):
            d=MDD(f"in/{n}.mdd"); os.makedirs(f"out/{ident}/OtherResources/Images",exist_ok=True); c=0
            for k,v in d.items():
                p=k.decode('utf-8','replace').replace('\\','/').lstrip('/')
                if p in imgs or True:
                    fp=f"out/{ident}/OtherResources/Images/{p}"; os.makedirs(os.path.dirname(fp),exist_ok=True); open(fp,'wb').write(v); c+=1
            print('images',c)
