import json,sys
def gen(S,end,spec):
    o=[]
    def a(t,k,v=.6,d=None):
        e={"t":round(max(0,t),2),"kind":k,"vol":v}
        if d:e["dur"]=d
        o.append(e)
    for s in S[1:]: a(s-.15,"whoosh",.6)
    for i,items in enumerate(spec):
        s=S[i];d=(S[i+1] if i+1<len(S) else end)-s
        for it in items:
            t=-it[0]*d if it[0]<0 else it[0]
            a(s+t,it[1],it[2] if len(it)>2 else .6,it[3] if len(it)>3 else None)
    return o
def cta():
    return [(.1,'pop',.7),(.5,'type',.5,.6),(1.2,'click',.6),(1.45,'click',.6),(1.7,'click',.6),(-.6,'ding',.5)]
V={
'office':([0,6.752,12.082,17.018,21.421,25.554,29.594,36.175],44.153,[
 [(.05,'pop',.7)]+[(.6+i*.2,'pop',.55) for i in range(5)]+[(1.9,'ding',.5)],
 [(.55,'type',.4,3.0),(-.75,'pop',.7)],
 [(1.2+i*.2,'click',.55) for i in range(4)]+[(-.55,'type',.4,1.6)],
 [(.4+i*.17,'pop',.45) for i in range(7)]+[(-.72,'pop',.7)],
 [(.3,'type',.4,1.0),(1.4,'whoosh',.4),(2.3,'pop',.5),(2.6,'pop',.5),(2.9,'pop',.5)],
 [(.3,'type',.4,1.0),(1.6,'click',.6),(2.0,'type',.4,1.6),(-.78,'pop',.7)],
 [(.0,'pop',.7)]+[(.4+i*.15,'pop',.5) for i in range(4)]+[(-.6,'ding',.5)],
 cta()]),
'insta':([0,5.886,10.129,13.985,18.542,22.752,27.628],34.327,[
 [(.05,'pop',.7),(.4,'pop',.7)]+[(.8+i*.24,'pop',.45) for i in range(5)],
 [(.35+i*.18,'pop',.45) for i in range(7)],
 [(.35,'type',.4,3.2)],
 [(.4,'click',.5),(.65,'click',.5),(.9,'click',.5),(1.15,'click',.5),(-.7,'pop',.7)],
 [(.4+i*.3,'pop',.55) for i in range(5)]+[(.85+i*.3,'click',.5) for i in range(5)]+[(-.75,'ding',.5)],
 [(.4+i*.12,'pop',.4) for i in range(5)]+[(-.5,'type',.4,1.5)],
 cta()]),
'rea':([0,4.133,10.664,18.587,24.414,29.176,35.262,40.822],47.629,[
 [(.05,'pop',.7),(1.0,'whoosh',.7),(1.1,'slam',.5)],
 [(.4,'pop',.5),(.55,'pop',.5),(.7,'pop',.5),(.8,'type',.35,1.5),(1.6,'pop',.7),(1.75,'pop',.7)],
 [(.2,'pop',.6)]+[(.3+i*.2,'pop',.5) for i in range(4)]+[(1.0+i*.2,'whoosh',.35) for i in range(4)]+[(-.5,'type',.4,1.0)],
 [(.3,'type',.35,.8),(1.5,'ding',.45),(2.2,'ding',.45)],
 [(.4+i*.4,'pop',.6) for i in range(4)]+[(-.7,'ding',.5)],
 [(.3+i*.2,'pop',.55) for i in range(4)]+[(1.4,'pop',.7),(1.7,'pop',.7)],
 [(.3+i*.3,'click',.6) for i in range(4)],
 cta()]),
'find':([0,4.322,8.846,14.824,20.95,24.366,28.55],35.675,[
 [(.05,'pop',.7),(.25,'pop',.6),(.45,'pop',.7),(1.6,'ding',.5)],
 [(.0,'shuffle',.35,2.0),(-.5,'pop',.7)],
 [(.4,'type',.4,1.3),(2.0,'click',.5)],
 [(.4,'pop',.5),(.7,'pop',.5),(1.0,'pop',.5),(1.6,'ding',.5)],
 [(.3,'type',.45,1.1),(2.4,'ding',.55)],
 [(.2,'type',.25,1.8),(2.0,'pop',.7)],
 cta()]),
'clients':([0,4.677,9.645,14.131,16.992,22.62,29.236],37.192,[
 [(.05,'pop',.7),(.3,'pop',.7)]+[(.8+i*.24,'pop',.45) for i in range(5)]+[(2.4,'ding',.5)],
 [(.35,'type',.4,1.3)]+[(1.9+i*.15,'pop',.45) for i in range(4)],
 [(1.3,'click',.6),(1.7,'click',.6),(2.1,'click',.6)],
 [(.4,'pop',.6),(.75,'pop',.6),(1.1,'pop',.6)],
 [(.3,'type',.35,4.0),(-.78,'pop',.7)],
 [(1.2+i*.45,'click',.6) for i in range(4)]+[(-.7,'pop',.7)],
 cta()]),
}
out={k:gen(*v) for k,v in V.items()}
json.dump(out,open('/home/claude/montage/fl2/sfx.json','w'))
print({k:len(v) for k,v in out.items()})
