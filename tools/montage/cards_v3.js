// v3 «Ты используешь Claude на 10%»
function ico(txt,bg,col){return `<div style="width:84px;height:84px;border-radius:22px;background:${bg};display:flex;align-items:center;justify-content:center;font-size:44px;font-weight:900;color:${col||'#111'}">${txt}</div>`}
CARDS.meter=function(t){ // hook gauge: 10% → 100%  b = «вот что он умеет»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const v=t<T('b')?10*prog(t,.2,.8):10+90*prog(t,T('b'),1.6);
 const h=el('div','big',{top:'150px',fontSize:'210px',color:t<T('b')?'#FF3B30':ACC},Math.round(v)+'%');R.append(h);
 const bar=el('div',null,{position:'absolute',left:'110px',right:'110px',top:'470px',height:'60px',borderRadius:'30px',background:'#232634'});
 bar.append(el('div',null,{height:'100%',width:v+'%',borderRadius:'30px',background:t<T('b')?'#FF3B30':ACC}));R.append(bar);
 const l=el('div','big',{top:'580px',fontSize:'50px',color:'#c9ccd8'},t<T('b')?'используешь, если просто задаёшь вопросы':'вот что он умеет на самом деле');R.append(l);
};
CARDS.make=function(t){ // 01 готовые вещи; b = «страницу калькулятор» c=«таблицу презентацию» d=«сразу рабочие»
 const f=frame('01','ГОТОВЫЕ ВЕЩИ','Claude · артефакты');intro(t,f);
 const items=[['Страница','▤','#4FD1FF'],['Калькулятор','±','#FFD60A'],['Таблица','▦','#34C759'],['Презентация','▶','#FF7A45']];
 items.forEach((it,i)=>{const s=(i<2?T('b'):T('c'))+(i%2)*.45;if(t<s)return;const p=prog(t,s,.4);
  const c=el('div',null,{position:'absolute',left:(30+i*225)+'px',top:'120px',width:'205px',height:'300px',borderRadius:'24px',background:'#202331',border:'2px solid #2f3344',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'26px',opacity:p,transform:`translateY(${(1-p)*60}px) scale(${.8+.2*p})`});
  c.innerHTML=ico(it[1],it[2])+`<div style="font-size:28px;font-weight:800">${it[0]}</div>`;f.w.append(c)});
 const n=el('div',null,{position:'absolute',left:'40px',top:'460px',fontSize:'34px',fontWeight:'800',color:'#9aa0b4'},'не текст — готовый файл, можно открыть и пользоваться');n.style.opacity=prog(t,T('d'),.4);f.w.append(n);
 pill(t,T('d')+.3,'СРАЗУ РАБОЧИЕ — ПО ССЫЛКЕ');
};
CARDS.skill=function(t){ // 02 скиллы; b=«один раз даёшь инструкцию» c=«и он делает»
 const f=frame('02','СКИЛЛЫ','навык сотрудника');intro(t,f);
 const doc=el('div','mono',{position:'absolute',left:'40px',top:'110px',width:'380px',height:'330px',borderRadius:'20px',background:'#202331',padding:'26px',fontSize:'26px',lineHeight:'1.5',color:'#c9ccd8'});
 doc.innerHTML=`<div style="color:${ACC};font-weight:700">SKILL.md</div>`+typed('1. Тон — как у меня\n2. Структура — как в шаблоне\n3. Проверь цифры',t,T('b'),30).replace(/\n/g,'<br>');
 doc.style.opacity=prog(t,.3,.3);f.w.append(doc);
 if(t>T('c')){for(let i=0;i<4;i++){const s=T('c')+.25+i*.35;if(t<s)continue;const p=prog(t,s,.3);
  const r=el('div',null,{position:'absolute',left:'470px',top:(115+i*82)+'px',width:'420px',height:'66px',borderRadius:'16px',background:'#202331',display:'flex',alignItems:'center',padding:'0 22px',fontSize:'28px',fontWeight:'800',gap:'14px',opacity:p,transform:`translateX(${(1-p)*80}px)`});
  r.innerHTML=`<span style="color:#34C759">✓</span> задача №${i+1} <span style="margin-left:auto;color:#9aa0b4;font-size:24px">одинаково</span>`;f.w.append(r)}}
 pill(t,T('c')+1.8,'КАЖДЫЙ РАЗ ОДИНАКОВО ХОРОШО');
};
CARDS.code=function(t){ // 03 Claude Code; b=«ты объясняешь словами»
 const f=frame('03','CLAUDE CODE','terminal');intro(t,f);
 const term=el('div','mono',{position:'absolute',left:'30px',right:'30px',top:'100px',bottom:'30px',fontSize:'30px',lineHeight:'1.55',color:'#d7dae5',whiteSpace:'pre'});
 const lines=[['> сделай сайт для кофейни с меню и заказом',.4,ACC],['  создаю index.html',1.6,'#9aa0b4'],['  создаю menu.js',2.0,'#9aa0b4'],['  создаю order.py',2.4,'#9aa0b4'],['  запускаю проверку…',2.9,'#9aa0b4'],['✓ сайт готов: localhost:3000',3.5,'#34C759']];
 let html='';lines.forEach((l,i)=>{if(t<l[1])return;const txt=i==0?typed(l[0],t,l[1],28):l[0];html+=`<div style="color:${l[2]}">${txt}</div>`});
 term.innerHTML=html+(Math.sin(t*8)>0?'▌':'');f.w.append(term);
 pill(t,T('b'),'ТЫ — СЛОВАМИ, ОН — ДЕЛАЕТ');
};
CARDS.connect=function(t){ // 04 подключения; b=«почта календарь документы» c=«сам заходит»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const role=el('div','role');role.append(el('div','num',null,'04'),el('div','rname',null,'ПОДКЛЮЧЕНИЯ'));role.style.opacity=prog(t,0,.4);R.append(role);
 const cx=540,cy=470;const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('width','1080');svg.setAttribute('height','960');svg.style.position='absolute';svg.style.left='0';svg.style.top='0';R.append(svg);
 const nodes=[['Почта','@',220,270],['Календарь','31',860,270],['Документы','▤',780,730]];
 nodes.forEach((n,i)=>{const s=T('b')+i*.35;if(t<s)return;const p=prog(t,s,.4);const live=t>T('c');
  const ln=document.createElementNS('http://www.w3.org/2000/svg','line');ln.setAttribute('x1',cx);ln.setAttribute('y1',cy);ln.setAttribute('x2',cx+(n[2]-cx)*p);ln.setAttribute('y2',cy+(n[3]-cy)*p);ln.setAttribute('stroke',live?ACC:'#3a3f55');ln.setAttribute('stroke-width','8');ln.setAttribute('stroke-dasharray',live?'18 14':'0');ln.setAttribute('stroke-dashoffset',String(-t*120));svg.append(ln);
  const b=el('div',null,{position:'absolute',left:(n[2]-120)+'px',top:(n[3]-80)+'px',width:'240px',height:'160px',borderRadius:'26px',background:live?'#1e2b33':'#202331',border:`3px solid ${live?ACC:'#2f3344'}`,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'8px',opacity:p});
  b.innerHTML=`<div style="font-size:54px;font-weight:900;color:${ACC}">${n[1]}</div><div style="font-size:30px;font-weight:800">${n[0]}</div>`;R.append(b)});
 const c=el('div',null,{position:'absolute',left:(cx-110)+'px',top:(cy-70)+'px',width:'220px',height:'140px',borderRadius:'30px',background:ACC,color:'#0b0c10',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'46px',fontWeight:'900',boxShadow:`0 0 ${40+20*Math.sin(t*4)}px ${ACC}`},'Claude');c.style.opacity=prog(t,.2,.4);R.append(c);
 if(t>T('c')){const p=el('div','pill',{left:'70px',right:'auto',bottom:'40px'},'САМ ЗАХОДИТ И РАБОТАЕТ');p.style.opacity=prog(t,T('c'),.3);R.append(p)}
};
CARDS.browser=function(t){ // 05 браузер; b=«может сам заходить» c=«пока ты пьёшь кофе»
 const f=frame('05','БРАУЗЕР','заявка.рф/форма');intro(t,f);
 const fields=[['Имя','Руслан'],['Телефон','+7 900 000-00-00'],['Комментарий','Нужна консультация']];
 const st=T('b');
 fields.forEach((fd,i)=>{const y=120+i*105;const lab=el('div',null,{position:'absolute',left:'50px',top:y+'px',fontSize:'24px',color:'#9aa0b4',fontWeight:'700'},fd[0]);f.w.append(lab);
  const box=el('div',null,{position:'absolute',left:'50px',right:'50px',top:(y+32)+'px',height:'58px',borderRadius:'12px',background:'#0f1117',border:'2px solid #2f3344',padding:'10px 18px',fontSize:'28px',fontWeight:'700'});
  box.textContent=typed(fd[1],t,st+.3+i*.8,26);f.w.append(box)});
 const btn=el('div',null,{position:'absolute',left:'50px',top:'440px',padding:'14px 40px',borderRadius:'14px',background:t>st+2.9?'#34C759':ACC,color:'#0b0c10',fontSize:'30px',fontWeight:'900'},t>st+2.9?'✓ Отправлено':'Отправить');f.w.append(btn);
 // cursor
 const path=[[700,60],[300,170],[300,275],[300,380],[140,465]];const k=cl((t-st)/2.9)*(path.length-1);const i0=Math.floor(k),fr=k-i0;const a=path[i0],b=path[Math.min(path.length-1,i0+1)];
 const cur=el('div',null,{position:'absolute',left:(a[0]+(b[0]-a[0])*ease(fr))+'px',top:(a[1]+(b[1]-a[1])*ease(fr))+'px',width:0,height:0,borderLeft:'18px solid #fff',borderTop:'12px solid transparent',borderBottom:'12px solid transparent',transform:'rotate(-30deg)',filter:'drop-shadow(0 2px 4px #000)'});f.w.append(cur);
 if(t>T('c')){const p=el('div','pill',{background:'#FFD60A'},'ПОКА ТЫ ПЬЁШЬ КОФЕ');p.style.opacity=prog(t,T('c'),.3);R.append(p)}
};
