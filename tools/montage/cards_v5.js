// v5 «Сайт, который смотрит на тебя»
CARDS.prompt=function(t){ // b=«кофейня тёплый свет» c=«когда наводишь курсор» d=«и получил готовый сайт»
 const f=frame('','ПРОСТО ОПИСАЛ СЛОВАМИ','Claude · новый чат');intro(t,f);
 const txt='Кофейня. Тёплый свет. Зёрна разлетаются, когда наводишь курсор.';
 const parts=[[T('b'),0,'Кофейня. Тёплый свет. Зёрна разлетаются,'.length],[T('c'),'Кофейня. Тёплый свет. Зёрна разлетаются,'.length,txt.length]];
 let n=0;parts.forEach(p=>{if(t>p[0])n=Math.min(p[2],p[1]+Math.floor((t-p[0])*34))});
 const b=el('div','bub me',{top:'110px',fontSize:'36px',maxWidth:'820px'},txt.slice(0,n)+(t<T('d')?'▌':''));b.style.opacity=prog(t,.3,.3);f.w.append(b);
 if(t>T('d')){const s=el('div',null,{position:'absolute',left:'40px',right:'40px',top:'330px',height:'180px',borderRadius:'20px',background:'radial-gradient(400px 200px at 70% 40%,rgba(255,170,90,.45),#1a0f0a)',display:'flex',alignItems:'center',padding:'0 40px',fontSize:'52px',fontWeight:'900',color:'#F3E3C3'},'Утро начинается <span style="color:#FFB36B;margin-left:14px">с зерна</span>');
  const p=prog(t,T('d'),.4);s.style.opacity=p;s.style.transform=`scale(${.9+.1*p})`;f.w.append(s)}
 pill(t,T('d')+.5,'ГОТОВЫЙ САЙТ');
};
CARDS.tmpl=function(t){ // b=«получишь шаблон как у всех»
 const f=frame('','«СДЕЛАЙ КРАСИВЫЙ САЙТ»','результат');intro(t,f);
 const g='#3a3d48';
 const page=el('div',null,{position:'absolute',left:'40px',right:'40px',top:'100px',height:'420px',borderRadius:'16px',background:'#e9eaee',padding:'30px',opacity:prog(t,.4,.4)});
 page.innerHTML=`<div style="display:flex;justify-content:space-between"><div style="width:140px;height:26px;background:#9aa0ac;border-radius:6px"></div><div style="display:flex;gap:14px">${'<div style="width:70px;height:20px;background:#b8bcc6;border-radius:5px"></div>'.repeat(3)}</div></div>
 <div style="margin-top:50px;width:520px;height:46px;background:${g};border-radius:8px"></div><div style="margin-top:16px;width:380px;height:22px;background:#9aa0ac;border-radius:6px"></div>
 <div style="margin-top:30px;width:200px;height:56px;background:#4a7bd8;border-radius:10px"></div>
 <div style="display:flex;gap:20px;margin-top:40px">${'<div style="flex:1;height:90px;background:#cfd2da;border-radius:10px"></div>'.repeat(3)}</div>`;f.w.append(page);
 if(t>T('b')){for(let i=0;i<3;i++){const c=el('div',null,{position:'absolute',left:(560+i*36)+'px',top:(150+i*36)+'px',width:'300px',height:'200px',borderRadius:'14px',background:'#d9dbe1',border:'3px solid #fff',boxShadow:'0 10px 30px rgba(0,0,0,.4)',opacity:prog(t,T('b')+.3+i*.25,.25)});f.w.append(c)}}
 pill(t,T('b')+1.2,'ШАБЛОН КАК У ВСЕХ','#FF3B30','#fff');
};
CARDS.tmpl2=function(t){ // b=«получишь вот это»
 const f=frame('','ПРОМТ С ДЕТАЛЯМИ','промт');intro(t,f);
 const rows=[['НАСТРОЕНИЕ','тёплый свет, уют, утро',.3],['ДВИЖЕНИЕ','зёрна разлетаются от курсора',1.0],['ДЕТАЛИ','пар над чашкой, меню всплывает',1.7]];
 rows.forEach((r,i)=>{if(t<r[2])return;const p=prog(t,r[2],.3);const e=el('div','row',{top:(110+i*120)+'px',opacity:p,transform:`translateX(${(1-p)*100}px)`},`<span style="color:${ACC};font-weight:900;min-width:250px">${r[0]}</span><span style="font-weight:600;color:#c9ccd8">${r[1]}</span>`);f.w.append(e)});
 pill(t,T('b'),'↓ ВОТ ЭТО');
};
