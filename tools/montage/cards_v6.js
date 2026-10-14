// v6 «Субагенты»
CARDS.agents=function(t){ // b=«это его помощники…» c=«и они работают одновременно»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const role=el('div','role');role.append(el('div','rname',null,'СУБАГЕНТЫ'));role.style.opacity=prog(t,0,.4);R.append(role);
 const cx=540;const c=el('div',null,{position:'absolute',left:(cx-150)+'px',top:'170px',width:'300px',height:'120px',borderRadius:'30px',background:ACC,color:'#0b0c10',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'44px',fontWeight:'900',boxShadow:`0 0 ${40+20*Math.sin(t*4)}px ${ACC}`},'Claude Code');c.style.opacity=prog(t,.2,.4);R.append(c);
 for(let i=0;i<4;i++){const s=T('b')+i*.3;if(t<s)continue;const p=prog(t,s,.35);const x=70+i*240;
  const n=el('div',null,{position:'absolute',left:x+'px',top:'420px',width:'210px',height:'330px',borderRadius:'26px',background:'#202331',border:`3px solid ${ACC}`,opacity:p,transform:`translateY(${(1-p)*-80}px)`,padding:'24px 20px'});
  const run=t>T('c')?cl((t-T('c'))/(2.2+i*.3)):0;
  n.innerHTML=`<div style="font-size:30px;font-weight:900">Агент ${i+1}</div><div style="font-size:22px;color:#9aa0b4;font-weight:700;margin-top:6px">своя задача</div>
  <div style="position:absolute;left:20px;right:20px;bottom:30px;height:22px;border-radius:11px;background:#2a2d3a"><div style="height:100%;width:${run*100}%;border-radius:11px;background:${ACC}"></div></div>`;R.append(n);
  const ln=el('div',null,{position:'absolute',left:(x+105)+'px',top:'290px',width:'4px',height:(130*p)+'px',background:ACC,opacity:.6});R.append(ln)}
 if(t>T('c')){const p=el('div','pill',null,'ОДНОВРЕМЕННО');p.style.opacity=prog(t,T('c'),.3);R.append(p)}
};
CARDS.team=function(t){ // b=«второй» c=«третий» d=«а главный»
 const f=frame('','КОМАНДА ИЗ АГЕНТОВ','параллельно');intro(t,f);
 const rows=[['✎','Пишет текст',.2],['✓','Проверяет факты',T('b')],['⚠','Ищет ошибки',T('c')],['★','Главный: собирает лучший результат',T('d')]];
 rows.forEach((r,i)=>{if(t<r[2])return;const p=prog(t,r[2],.3);const main=i==3;
  const e=el('div','row',{top:(100+i*112)+'px',opacity:p,transform:`translateX(${(1-p)*100}px)`,border:main?`3px solid ${ACC}`:'none'},`<span style="width:56px;height:56px;border-radius:14px;background:${main?ACC:'#2a2d3a'};color:${main?'#111':ACC};display:flex;align-items:center;justify-content:center;font-weight:900">${r[0]}</span>${r[1]}`);
  if(!main&&t>r[2]+.6){const c=el('div','chk',null,'готово');c.style.opacity=prog(t,r[2]+.6,.25);e.append(c)}f.w.append(e)});
};
CARDS.speed=function(t){ // b=«один делает за целый день» c=«а команда за час»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const h=el('div','big',{top:'70px',fontSize:'60px'},'КАК С КОМАНДОЙ');h.style.opacity=prog(t,0,.3);R.append(h);
 const bar=(y,label,col,s,speed,endTxt)=>{if(t<s)return;const p=prog(t,s,.3);const w=cl((t-s)*speed);
  const b=el('div',null,{position:'absolute',left:'70px',right:'70px',top:y+'px',opacity:p});
  b.innerHTML=`<div style="display:flex;justify-content:space-between;font-size:40px;font-weight:900;margin-bottom:16px"><span>${label}</span><span style="color:${col}">${w>=1?endTxt:Math.round(w*100)+'%'}</span></div><div style="height:56px;border-radius:28px;background:#232634"><div style="height:100%;width:${w*100}%;border-radius:28px;background:${col}"></div></div>`;R.append(b)};
 bar(260,'Один агент','#9aa0b4',T('b'),.12,'весь день');
 bar(520,'Команда агентов',ACC,T('c'),.9,'за час');
};
CARDS.limit=function(t){ // b=«поэтому важно»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const ok=t>T('b');
 const v=ok?.12+.58*prog(t,T('b'),.8):1-cl((t-.2)/1.8)*.88;
 const col=ok?'#34C759':(v<.35?'#FF3B30':'#FFC24D');
 const h=el('div','big',{top:'70px',fontSize:'56px'},ok?'С НАСТРОЙКОЙ — ЛИМИТ ЖИВ':'БЕЗДУМНО');h.style.color=ok?'#34C759':'#FF3B30';R.append(h);
 const g=el('div',null,{position:'absolute',left:'110px',right:'110px',top:'200px',height:'90px',borderRadius:'45px',background:'#232634',overflow:'hidden'});
 g.append(el('div',null,{height:'100%',width:(Math.min(1,v)*100)+'%',background:col,borderRadius:'45px'}));R.append(g);
 R.append(el('div','big',{top:'310px',fontSize:'40px',color:'#c9ccd8'},`ЛИМИТ: ${Math.round(Math.min(1,v)*100)}%`));
 if(!ok){for(let i=0;i<10;i++){const s=.2+i*.15;if(t<s)continue;R.append(el('div','tag',{left:(80+(i%5)*190)+'px',top:(420+Math.floor(i/5)*90)+'px',background:'#3a1d1d',color:'#FF6B6B',opacity:prog(t,s,.2)},'агент '+(i+1)))}}
 else{['3 агента','чёткие задачи','без лишних кругов'].forEach((s,i)=>{const s0=T('b')+.3+i*.4;if(t<s0)return;R.append(el('div','tag',{left:'110px',top:(420+i*80)+'px',background:'#1d3a24',color:'#34C759',fontSize:'34px',opacity:prog(t,s0,.25)},'✓ '+s))})}
};
