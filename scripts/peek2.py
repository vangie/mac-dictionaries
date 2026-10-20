from pyglossary.plugin_lib.readmdict import MDX, MDD
for n in ['kangxi','moe']:
    m=MDX(f"in/{n}.mdx"); print(n, repr(m.header.get(b'StyleSheet',b'').decode()[:3000]))
m=MDX("in/bujian.mdx")
c=0
for k,v in m.items():
    if not v.startswith(b'@@@'):
        c+=1
        if c in (3,2000): print(k.decode(), v.decode()[:1500])
for n in ['kangxi','moe']:
    d=MDD(f"in/{n}.mdd"); ks=[k for k,v in d.items()]; print(n,len(ks),[x.decode() for x in ks[:8]])
import re
m=MDX("in/kangxi.mdx"); s=set()
for k,v in m.items():
    for x in re.findall(rb'[^`]*\.(?:png|jpg|gif|svg|css|js)',v)[:2]: s.add(x[-80:])
    if len(s)>10: break
print(s)
