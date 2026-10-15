
// 0 HOOK
S.push(function(t,d){base('#FF7A45','#FF7A4540');
 const a=el('div','big',{top:'190px',fontSize:'150px'},'5 СКИЛЛОВ');const p=back((t-.05)/.45);a.style.transform=`scale(${.6+.4*p})`;a.style.opacity=cl(t/.2);R.append(a);
 const b=el('div','big',{top:'360px',fontSize:'70px',color:'#FF7A45'},'= ЦЕЛАЯ КОМАНДА');const q=pr(t,.5,.4);b.style.opacity=q;b.style.transform=`translateY(${(1-q)*40}px)`;R.append(b);
 // center card
 const c=el('div','chip',{left:'390px',top:'760px',width:'300px',height:'300px',fontSize:'52px',background:'linear-gradient(145deg,#2a1d17,#1b1c26)',borderColor:'#FF7A45'},'<div style="font-size:90px;color:#FF7A45">✳</div>CLAUDE');
 const cp=back((t-.2)/.5);c.style.transform=`scale(${cl(cp,0,2)})`;R.append(c);
 const pos=[[90,560],[730,560],[40,1000],[780,1000],[410,1080]];
 ROLES.forEach((r,i)=>{const s=.7+i*.18;if(t<s)return;const k=back((t-s)/.45);const [x,y]=pos[i];
  const e=el('div','chip',{left:x+'px',top:y+'px',width:'260px',height:'200px',fontSize:'30px',borderColor:r[1]},`<div style="font-size:64px;color:${r[1]};line-height:1.1">${r[3]}</div>${r[0]}`);
  const fx=540-130,fy=910-100;e.style.transform=`translate(${(fx-x)*(1-k)}px,${(fy-y)*(1-k)}px) scale(${.3+.7*cl(k,0,1.2)}) rotate(${(1-k)*(i%2?20:-20)}deg)`;e.style.opacity=cl((t-s)/.15);R.append(e)});
 if(t>1.6){const f=el('div',null,{position:'absolute',left:'50%',top:'468px',transform:`translateX(-50%) scale(${back((t-1.6)/.4)}) rotate(-4deg)`,background:'#34C759',color:'#0a0b0f',fontWeight:'900',fontSize:'48px',padding:'14px 36px',borderRadius:'40px'},'БЕСПЛАТНО');R.append(f)}
});
// 1 OFFICIAL + toggles
S.push(function(t,d){base('#FF7A45','#FF7A4530');
 const a=el('div','big',{top:'170px',fontSize:'78px'},'ОФИЦИАЛЬНЫЕ');const p=pr(t,0,.4);a.style.opacity=p;a.style.transform=`translateY(${(1-p)*-40}px)`;R.append(a);
 const b=el('div','big',{top:'265px',fontSize:'44px',color:'#9aa0b4',fontWeight:'700'},'от создателей Claude');b.style.opacity=pr(t,.2,.4);R.append(b);
 const w=win(t,'Настройки › Навыки',.2);
 ROLES.forEach((r,i)=>{const s=.5+i*.12;if(t<s)return;const q=pr(t,s,.35);
  const on=t>(d*.45+i*(d*.08));const k=pr(t,d*.45+i*(d*.08),.18);
  const row=el('div',null,{position:'absolute',left:'40px',right:'40px',top:(120+i*140)+'px',height:'116px',borderRadius:'22px',background:'#1f2230',display:'flex',alignItems:'center',padding:'0 30px',gap:'24px',opacity:q,transform:`translateX(${(1-q)*120}px)`});
  row.innerHTML=`<div style="width:64px;height:64px;border-radius:16px;background:${r[1]}22;color:${r[1]};font-size:40px;display:flex;align-items:center;justify-content:center">${r[3]}</div>
  <div><div class="mono" style="font-size:34px;font-weight:700">${r[2]}</div><div style="font-size:24px;color:#9aa0b4;font-weight:600">${r[0].toLowerCase()}</div></div>
  <div style="margin-left:auto;width:110px;height:60px;border-radius:30px;background:${on?'#34C759':'#3a3d4c'};position:relative"><div style="position:absolute;top:6px;left:${6+44*k}px;width:48px;height:48px;border-radius:50%;background:#fff;box-shadow:0 4px 10px rgba(0,0,0,.4)"></div></div>`;
  w.append(row)});
 if(t>d*.88){const f=el('div',null,{position:'absolute',left:'50%',top:'1240px',transform:`translateX(-50%) scale(${back((t-d*.88)/.3)})`,background:'#fff',color:'#0a0b0f',fontWeight:'900',fontSize:'46px',padding:'14px 36px',borderRadius:'40px'},'⏱ ЗА МИНУТУ');R.append(f)}
});
// 2 DESIGNER
S.push(function(t,d){base('#FF7A45');header(t,0);const w=win(t,'Claude · новый чат',.15);
 const txt='Лендинг для студии йоги — без шаблонов';const b=el('div','bub me',{top:'110px'},typed(txt,t,.35,30)+(t<1.8?'▌':''));w.append(b);
 const s=1.8;if(t>s){const pg=el('div',null,{position:'absolute',left:'36px',right:'36px',top:'270px',bottom:'36px',borderRadius:'22px',overflow:'hidden',background:'#f4efe6',color:'#1d1a16'});w.append(pg);
  const q=pr(t,s,.4);pg.style.opacity=q;pg.style.transform=`scale(${.92+.08*q})`;
  const blob=el('div',null,{position:'absolute',right:'-80px',top:'-60px',width:'520px',height:'520px',borderRadius:'50%',background:'radial-gradient(circle at 35% 35%,#ffb38a,#e2603a 60%,#b8402a)',transform:`scale(${pr(t,s+.2,.6)}) translate(${Math.sin(t*1.3)*12}px,${Math.cos(t)*10}px)`});pg.append(blob);
  const nav=el('div',null,{position:'absolute',left:'40px',right:'40px',top:'34px',display:'flex',justifyContent:'space-between',fontSize:'24px',fontWeight:'700',opacity:pr(t,s+.3,.3)},'<span style="letter-spacing:6px">PRANA</span><span style="opacity:.6">Расписание · Цены · Контакты</span>');pg.append(nav);
  const h=el('div',null,{position:'absolute',left:'40px',top:'150px',fontFamily:'"DejaVu Serif",serif',fontSize:'92px',lineHeight:'1',fontWeight:'700',letterSpacing:'-2px'});
  const words=['Дыши.','Тянись.','Живи.'];h.innerHTML=words.map((x,i)=>`<div style="opacity:${pr(t,s+.45+i*.22,.3)};transform:translateY(${(1-pr(t,s+.45+i*.22,.3))*40}px)">${i==2?'<i style="color:#e2603a">'+x+'</i>':x}</div>`).join('');pg.append(h);
  const btn=el('div',null,{position:'absolute',left:'40px',top:'470px',background:'#1d1a16',color:'#f4efe6',fontSize:'28px',fontWeight:'800',padding:'20px 34px',borderRadius:'40px',opacity:pr(t,s+1.2,.3),transform:`scale(${.8+.2*back((t-s-1.2)/.4)})`},'Первое занятие бесплатно →');pg.append(btn);
  for(let i=0;i<3;i++){const c=el('div',null,{position:'absolute',left:(40+i*305)+'px',top:'590px',width:'280px',height:'200px',borderRadius:'20px',background:['#e9dfcf','#1d1a16','#e2603a'][i],color:i?'#f4efe6':'#1d1a16',padding:'24px',fontSize:'28px',fontWeight:'800',opacity:pr(t,s+1.4+i*.15,.3),transform:`translateY(${(1-pr(t,s+1.4+i*.15,.3))*60}px)`},['Хатха','Виньяса','Медитация'][i]);pg.append(c)}
 }
});
// 3 SLIDES
S.push(function(t,d){base('#4FD1FF');header(t,1);const w=win(t,'Презентация.pptx',.15);
 const titles=[['Итоги квартала','+34%'],['Рынок','3 сегмента'],['План','5 шагов'],['Команда','12 человек'],['Бюджет','график'],['Вывод','растём']];
 titles.forEach((s,i)=>{const st=.5+i*.28;if(t<st)return;const k=back((t-st)/.45);const col=i%3,row=Math.floor(i/3);
  const x=36+col*300,y=130+row*320;const e=el('div',null,{position:'absolute',left:x+'px',top:y+'px',width:'280px',height:'290px',borderRadius:'18px',background:i==0?'linear-gradient(135deg,#0e3b52,#4FD1FF)':'#f5f7fb',color:i==0?'#fff':'#14202b',padding:'24px',boxShadow:'0 20px 40px rgba(0,0,0,.4)'});
  e.innerHTML=`<div style="font-size:30px;font-weight:900">${s[0]}</div><div style="font-size:${i==0?54:40}px;font-weight:900;margin-top:20px;color:${i==0?'#fff':'#1b8fc0'}">${s[1]}</div>`+
   (i==4?'<div style="display:flex;gap:10px;align-items:flex-end;height:110px;margin-top:10px">'+[40,70,55,95].map(h=>`<div style="flex:1;height:${h*pr(t,st+.3,.5)}%;background:#4FD1FF;border-radius:6px"></div>`).join('')+'</div>':'<div style="margin-top:24px;height:14px;width:80%;background:#d5dbe5;border-radius:7px"></div><div style="margin-top:12px;height:14px;width:60%;background:#d5dbe5;border-radius:7px"></div>');
  e.style.transform=`translate(${(1-k)*(540-x-150)}px,${(1-k)*600}px) rotate(${(1-k)*(i%2?14:-14)}deg) scale(${.5+.5*cl(k,0,1.1)})`;e.style.opacity=cl((t-st)/.15);w.append(e)});
 if(t>d*.8){const f=el('div',null,{position:'absolute',left:'50%',top:'1240px',transform:`translateX(-50%) scale(${back((t-d*.8)/.3)})`,background:'#4FD1FF',color:'#0a0b0f',fontWeight:'900',fontSize:'46px',padding:'14px 36px',borderRadius:'40px'},'ГОТОВЫЙ .PPTX');R.append(f)}
});
// 4 ANALYST
S.push(function(t,d){base('#34C759');header(t,2);const w=win(t,'Продажи.xlsx',.15);
 const m=['Янв','Фев','Мар','Апр','Май','Июн'],v=[120,135,128,162,181,204];
 const tb=el('div',null,{position:'absolute',left:'36px',right:'36px',top:'110px',borderRadius:'16px',overflow:'hidden',fontSize:'28px',fontWeight:'700'});w.append(tb);
 const hd=el('div',null,{display:'flex',background:'#1e7a3c',color:'#fff'},'<div style="flex:1;padding:14px 20px">Месяц</div><div style="flex:1;padding:14px 20px">Выручка</div><div style="flex:1;padding:14px 20px">Рост</div>');tb.append(hd);
 m.forEach((x,i)=>{const st=.4+i*.12;const q=pr(t,st,.25);const r=el('div',null,{display:'flex',background:i%2?'#f2f6f3':'#fff',color:'#18261d',opacity:q});
  r.innerHTML=`<div style="flex:1;padding:12px 20px">${x}</div><div class="mono" style="flex:1;padding:12px 20px">${Math.round(v[i]*q)} 000</div><div class="mono" style="flex:1;padding:12px 20px;color:${i&&v[i]<v[i-1]?'#d33':'#1e9a4a'}">${i?((v[i]/v[i-1]-1)*100).toFixed(0)+'%':'—'}</div>`;tb.append(r)});
 const cs=1.4;if(t>cs){const ch=el('div',null,{position:'absolute',left:'36px',right:'36px',top:'540px',height:'290px',borderRadius:'16px',background:'#11141b',border:'2px solid #262935',display:'flex',alignItems:'flex-end',gap:'22px',padding:'30px 40px',opacity:pr(t,cs,.3)});w.append(ch);
  v.forEach((x,i)=>{const h=(x/204)*200*pr(t,cs+.15+i*.1,.5);ch.append(el('div',null,{flex:'1',height:h+'px',borderRadius:'10px 10px 4px 4px',background:i==5?'#34C759':'#2f6b45'}))})}
 if(t>d*.75){const f=el('div',null,{position:'absolute',left:'50%',top:'1240px',transform:`translateX(-50%) scale(${back((t-d*.75)/.3)})`,background:'#34C759',color:'#0a0b0f',fontWeight:'900',fontSize:'46px',padding:'14px 36px',borderRadius:'40px'},'ИЗ ОДНОЙ ФРАЗЫ');R.append(f)}
});
// 5 ARTIST
S.push(function(t,d){base('#FF5FD2');header(t,3);
 const pw=640,ph=860,x0=220,y0=360;const p=pr(t,.1,.5);
 const po=el('div',null,{position:'absolute',left:x0+'px',top:y0+'px',width:pw+'px',height:ph+'px',borderRadius:'10px',background:'#f1ebe0',overflow:'hidden',boxShadow:'0 40px 120px rgba(0,0,0,.7)',transform:`translateY(${(1-p)*160}px) rotate(${(1-p)*-6}deg)`,opacity:cl(t/.25)});R.append(po);
 const sh=[[.4,'circle','#FF5FD2',120,140,380],[.7,'circle','#1d1a2e',330,300,230],[1.0,'rect','#FFC24D',60,560,520],[1.3,'circle','#4FD1FF',420,90,140]];
 sh.forEach(s=>{const k=back((t-s[0])/.5);if(t<s[0])return;const e=el('div',null,{position:'absolute',left:s[3]+'px',top:s[4]+'px',width:s[5]+'px',height:(s[1]=='rect'?18:s[5])+'px',borderRadius:s[1]=='rect'?'9px':'50%',background:s[2],mixBlendMode:'multiply',transform:`scale(${cl(k,0,1.2)})`});po.append(e)});
 const ttl=el('div',null,{position:'absolute',left:'50px',bottom:'60px',fontSize:'110px',fontWeight:'900',color:'#1d1a2e',letterSpacing:'-3px',lineHeight:'.9',opacity:pr(t,1.6,.3),transform:`translateY(${(1-pr(t,1.6,.4))*50}px)`},'ВЕСНА<br><span style="font-size:40px;letter-spacing:8px;font-weight:700">ФЕСТИВАЛЬ · 2027</span>');po.append(ttl);
 if(t>d*.72){['PNG','PDF'].forEach((x,i)=>{const f=el('div',null,{position:'absolute',left:(330+i*230)+'px',top:'1235px',transform:`scale(${back((t-d*.72-i*.12)/.3)})`,background:'#FF5FD2',color:'#0a0b0f',fontWeight:'900',fontSize:'46px',padding:'14px 36px',borderRadius:'40px'},x);R.append(f)})}
});
// 6 SKILL CREATOR
S.push(function(t,d){base('#FFC24D');header(t,4);const w=win(t,'my-skill / SKILL.md',.15);
 const lines=['---','name: отчёт-для-клиента','description: делает отчёт','  в моём стиле за 1 минуту','---','# Шаги','1. Возьми данные','2. Посчитай итоги','3. Оформи по шаблону'];
 const full=lines.join('\n');const n=Math.floor(cl((t-.4)*48,0,full.length));
 const code=el('div','mono',{position:'absolute',left:'40px',right:'40px',top:'110px',fontSize:'32px',lineHeight:'1.5',whiteSpace:'pre',color:'#e8e2cf'});
 code.innerHTML=full.slice(0,n).split('\n').map(l=>l.startsWith('name')||l.startsWith('description')?l.replace(/^(\w+):/,'<span style="color:#FFC24D">$1:</span>'):(l.startsWith('#')?'<span style="color:#FF7A45">'+l+'</span>':l)).join('\n')+(t%0.8<0.4?'▌':'');w.append(code);
 const ns=d*.62;if(t>ns){const k=back((t-ns)/.5);const c=el('div','chip',{left:'260px',top:'560px',width:'440px',height:'170px',fontSize:'38px',borderColor:'#FFC24D',background:'#2a2416',transform:`scale(${cl(k,0,1.2)}) rotate(${(1-k)*-10}deg)`},'<div style="font-size:30px;color:#FFC24D">+ НОВЫЙ НАВЫК</div>ТВОЙ СКИЛЛ');w.append(c)}
 if(t>d*.8){const f=el('div',null,{position:'absolute',left:'50%',top:'1240px',transform:`translateX(-50%) scale(${back((t-d*.8)/.3)})`,background:'#FFC24D',color:'#0a0b0f',fontWeight:'900',fontSize:'44px',padding:'14px 36px',borderRadius:'40px'},'НАУЧИ ЧЕМУ УГОДНО');R.append(f)}
});
// 7 CTA
S.push(function(t,d){base('#FF7A45','#FF7A4540');
 const a=el('div','big',{top:'240px',fontSize:'64px',color:'#c9ccd8'},'НАПИШИ В КОММЕНТАРИЯХ');a.style.opacity=pr(t,0,.3);R.append(a);
 const box=el('div',null,{position:'absolute',left:'90px',right:'90px',top:'420px',height:'190px',borderRadius:'95px',background:'#1c1e2a',border:'3px solid #FF7A45',display:'flex',alignItems:'center',padding:'0 60px',fontSize:'110px',fontWeight:'900',letterSpacing:'4px',boxShadow:'0 0 80px #FF7A4555'});
 const p=back((t-.1)/.45);box.style.transform=`scale(${cl(p,0,1.2)})`;box.innerHTML=typed('СКИЛЛЫ',t,.5,9)+(t<1.3||t%0.8<0.4?'<span style="color:#FF7A45">|</span>':'');R.append(box);
 const items=['5 скиллов','инструкция: как включить','примеры запросов'];
 items.forEach((x,i)=>{const s=1.2+i*.25;if(t<s)return;const q=pr(t,s,.3);R.append(el('div',null,{position:'absolute',left:'140px',top:(700+i*120)+'px',fontSize:'48px',fontWeight:'800',opacity:q,transform:`translateX(${(1-q)*-80}px)`},`<span style="color:#34C759;margin-right:20px">✓</span>${x}`))});
 if(t>d*.6){const k=back((t-d*.6)/.4);const s=el('div',null,{position:'absolute',left:'50%',top:'1130px',transform:`translateX(-50%) scale(${cl(k,0,1.2)})`,background:'#fff',color:'#0a0b0f',fontWeight:'900',fontSize:'50px',padding:'18px 44px',borderRadius:'44px',display:'flex',gap:'18px',alignItems:'center'},'<span style="font-size:54px">🔖</span> СОХРАНИ');R.append(s)}
});

