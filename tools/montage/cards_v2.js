// v2 «Этот ролик смонтировал Claude»
CARDS.raw=function(t){ // params: b (=«со всеми оговорками»), c (=«и отдал ему»)
 const f=frame('','СЫРОЕ ВИДЕО','IMG_8330.MOV');intro(t,f);
 const rec=el('div',null,{position:'absolute',left:'40px',top:'110px',display:'flex',alignItems:'center',gap:'16px',fontSize:'40px',fontWeight:'900'});
 const dot=el('div',null,{width:'30px',height:'30px',borderRadius:'50%',background:'#FF3B30',opacity:(Math.sin(t*6)>0?1:.25)});
 rec.append(dot,el('span','mono',null,'REC  '+fmt(Math.min(192,t*48))));f.w.append(rec);
 const tr=el('div','track',{top:'220px',height:'200px',background:'#1b1e2a'});f.w.append(tr);
 const W=wave(70,3),bad=[[9,15,'э-э…'],[27,35,'пауза'],[46,55,'дубль 2']];
 W.forEach((h,i)=>{const p=prog(t,.3+i*.02,.2);const isBad=bad.some(b=>i>=b[0]&&i<b[1]);
  const red=isBad&&t>T('b');tr.append(el('div',null,{position:'absolute',left:(14+i*11.8)+'px',width:'8px',borderRadius:'4px',
   height:(h*170*p)+'px',top:(100-h*85*p)+'px',background:red?'#FF3B30':ACC}))});
 if(t>T('b'))bad.forEach((b,k)=>{const q=prog(t,T('b')+k*.25,.3);const g=el('div','tag',{left:(14+b[0]*11.8)+'px',top:'440px',background:'#FF3B30',color:'#fff',opacity:q,transform:`translateY(${(1-q)*20}px)`},b[2]);f.w.append(g)});
 if(t>T('c')){const q=prog(t,T('c'),.35);const up=el('div',null,{position:'absolute',left:'0',right:'0',bottom:'0',height:'560px',background:'rgba(14,15,20,.88)',display:'flex',alignItems:'center',justifyContent:'center',gap:'30px',fontSize:'52px',fontWeight:'900',opacity:q});
  up.innerHTML=`<span class="mono" style="font-size:40px;background:#232634;padding:16px 24px;border-radius:16px">IMG_8330.MOV</span><span style="color:${ACC};font-size:70px">→</span><span style="background:${ACC};color:#111;padding:16px 28px;border-radius:16px">Claude</span>`;
  up.style.transform=`translateX(${(1-q)*80}px)`;f.w.append(up)}
};
CARDS.cut=function(t){ // b = «вырезал лишнее»
 const f=frame('','МОНТАЖ','таймлайн');intro(t,f);
 const W=wave(70,3),bad=[[9,15],[27,35],[46,55]];
 const tl=T('b'),pc=prog(t,tl,1.2);
 const tr=el('div','track',{top:'150px',height:'200px',background:'#1b1e2a'});f.w.append(tr);
 let x=14;W.forEach((h,i)=>{const isBad=bad.some(b=>i>=b[0]&&i<b[1]);
  let op=1,w=8,step=11.8;if(isBad){op=1-pc;step=11.8*(1-pc);w=8*(1-pc)}
  const scan=t>.4&&isBad;tr.append(el('div',null,{position:'absolute',left:x+'px',width:w+'px',borderRadius:'4px',height:(h*170)+'px',top:(100-h*85)+'px',background:scan?'#FF3B30':ACC,opacity:op}));x+=step});
 const ph=el('div',null,{position:'absolute',top:'140px',height:'220px',width:'6px',background:'#fff',borderRadius:'3px',left:(20+cl((t-.3)/(tl-.2||1))*870)+'px',boxShadow:'0 0 20px #fff',opacity:1-pc});f.w.append(ph);
 const len=192-(192-46)*pc;
 const c=el('div',null,{position:'absolute',left:'40px',top:'400px',fontSize:'64px',fontWeight:'900'},`<span class="mono">${fmt(len)}</span> <span style="font-size:36px;color:#9aa0b4">длина ролика</span>`);f.w.append(c);
 pill(t,tl+1.0,'ЛИШНЕЕ ВЫРЕЗАНО');
};
CARDS.subs=function(t){
 const f=frame('','СУБТИТРЫ','авто');intro(t,f);
 const words=['СЛОВО','В','СЛОВО','С','ТВОИМ','ГОЛОСОМ'];
 const box=el('div',null,{position:'absolute',left:'40px',right:'40px',top:'130px',height:'300px',borderRadius:'22px',background:'linear-gradient(180deg,#2a2d3a,#15171f)',display:'flex',alignItems:'center',justifyContent:'center',flexWrap:'wrap',gap:'0 22px',padding:'0 40px',fontSize:'72px',fontWeight:'900'});
 words.forEach((w,i)=>{const s=.4+i*.18;const sp=el('span',null,{opacity:t>s?1:0,color:i==4||i==5?ACC:'#fff'},w);box.append(sp)});f.w.append(box);
 const lab=el('div',null,{position:'absolute',left:'40px',top:'470px',fontSize:'32px',fontWeight:'700',color:'#9aa0b4'},'без точек · крупно · подсветка ключевых слов');lab.style.opacity=prog(t,1.2,.4);f.w.append(lab);
 pill(t,1.0,'САМ');
};
CARDS.fx=function(t){ // b=«сделал музыку», c=«добавил анимацию»
 const f=frame('','ВСТАВКИ','эта самая карточка');intro(t,f);
 const items=[['ВСТАВКИ',0.3],['МУЗЫКА',T('b')],['АНИМАЦИЯ',T('c')]];
 items.forEach((it,i)=>{const p=prog(t,it[1],.35);const r=el('div','row',{top:(110+i*120)+'px',opacity:p,transform:`translateX(${(1-p)*120}px)`},`<span style="color:${ACC}">●</span>${it[0]}`);
  if(i==1){const eq=el('div',null,{display:'flex',gap:'6px',alignItems:'flex-end',height:'50px',marginLeft:'20px'});for(let k=0;k<7;k++)eq.append(el('div',null,{width:'10px',borderRadius:'3px',background:ACC,height:(12+38*Math.abs(Math.sin(t*7+k*1.3)))+'px'}));r.append(eq)}
  if(t>it[1]+.35){const c=el('div','chk',null,'✓ готово');c.style.opacity=prog(t,it[1]+.35,.25);r.append(c)}f.w.append(r)});
 if(t>.5){const a=el('div','tag',{right:'70px',top:'60px',background:'#fff',color:'#111'},'↓ это и есть вставка');a.style.opacity=prog(t,.5,.3);R.append(a)}
};
CARDS.before=function(t){ // b = «или полторы-две тысячи»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const h=el('div','big',{top:'70px',fontSize:'56px',color:'#9aa0b4'},'РАНЬШЕ');h.style.opacity=prog(t,0,.3);R.append(h);
 const a=el('div',null,{position:'absolute',left:'70px',right:'70px',top:'180px',height:'250px',borderRadius:'30px',background:'#1c1f2b',border:'2px solid #2a2d3a',display:'flex',alignItems:'center',gap:'36px',padding:'0 44px'});
 const pa=prog(t,.2,.4);a.style.opacity=pa;a.style.transform=`translateY(${(1-pa)*40}px)`;
 a.innerHTML=`<div style="flex:none;width:150px;height:150px;border-radius:50%;background:#FFD60A;display:flex;align-items:center;justify-content:center;font-size:70px;font-weight:900;color:#111">☾</div><div><div style="font-size:72px;font-weight:900">ВЕЧЕР</div><div style="font-size:36px;color:#9aa0b4;font-weight:700">на монтаж одного ролика</div></div>`;R.append(a);
 const b=el('div',null,{position:'absolute',left:'70px',right:'70px',top:'470px',height:'250px',borderRadius:'30px',background:'#1c1f2b',border:'2px solid #2a2d3a',display:'flex',alignItems:'center',gap:'36px',padding:'0 44px'});
 const pb=prog(t,T('b'),.4);b.style.opacity=pb;b.style.transform=`translateY(${(1-pb)*40}px)`;
 b.innerHTML=`<div style="flex:none;width:150px;height:150px;border-radius:50%;background:#FF7A45;display:flex;align-items:center;justify-content:center;font-size:70px;font-weight:900;color:#111">₽</div><div><div style="font-size:72px;font-weight:900">1 500–2 000 ₽</div><div style="font-size:36px;color:#9aa0b4;font-weight:700">монтажёру — за каждый ролик</div></div>`;R.append(b);
 pill(t,T('c'),'× КАЖДЫЙ РАЗ','#FF3B30','#fff');
};
CARDS.work=function(t){ // b = «а он за тебя может»
 const f=frame('','ЧАТ → ИСПОЛНИТЕЛЬ','Claude');intro(t,f);
 const q=el('div','bub me',{top:'100px'},'Что такое монтаж?');q.style.opacity=prog(t,.3,.3)*(t>T('b')?.35:1);f.w.append(q);
 if(t>T('b')){const st=el('div',null,{position:'absolute',right:'40px',top:'130px',width:'400px',height:'6px',background:'#FF3B30',transform:`scaleX(${prog(t,T('b'),.3)})`,transformOrigin:'right'});f.w.append(st);
  const m=el('div','bub me',{top:'210px'},'Смонтируй это видео');m.style.opacity=prog(t,T('b')+.2,.3);f.w.append(m);
  ['паузы вырезаны','субтитры','музыка','анимация'].forEach((s,i)=>{const s0=T('b')+.7+i*.35;if(t<s0)return;const r=el('div',null,{position:'absolute',left:'40px',top:(330+i*58)+'px',fontSize:'34px',fontWeight:'800'},`<span style="color:#34C759">✓</span> ${s}`);r.style.opacity=prog(t,s0,.25);f.w.append(r)})}
 pill(t,T('b')+2.3,'ГОТОВО: reel.mp4');
};
