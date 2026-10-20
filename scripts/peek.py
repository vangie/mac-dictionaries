import sys
from pyglossary.plugin_lib.readmdict import MDX, MDD
for n in sys.argv[1:]:
    m=MDX(f"in/{n}.mdx")
    it=m.items(); c=0; ex=[]
    for k,v in it:
        c+=1
        if c in (100,5000): ex.append((k.decode(),v.decode('utf-8','replace')[:600]))
    print("==",n,c,m.header.get(b'Title'), m.header.get(b'StyleSheet',b'')[:80])
    for e in ex: print(e)
