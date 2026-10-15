// ИИ-ОФИС (ОФИС)
const OA=[['СЕКРЕТАРЬ','#4FD1FF','✉'],['МАРКЕТОЛОГ','#FF5FD2','✎'],['АНАЛИТИК','#34C759','▦'],['ПОДДЕРЖКА','#FFC24D','☎'],['ДИРЕКТОР','#FF7A45','★']];
S.push(function(t,d){base('#FF7A45','#FF7A4540');
 bigt(t,.05,'ИИ-ОФИС',200,170);
 const b=el('div','big',{top:'390px',fontSize:'56px',color:'#FF7A45'},'5 агентов · без отпусков');b.style.opacity=pr(t,.5,.4);R.append(b);
 OA.forEach((a,i)=>{const s=.6+i*.2;if(t<s)return;const k=back((t-s)/.45);const col=i%2,row=Math.floor(i/2);
  const x=i==4?380:110+col*540,y=560+row*250+(i==4?0:0);const yy=i==4?1060:y;
  const e=el('div','chip',{left:x+'px',top:yy+'px',width:'330px',height:'210px',fontSize:'32px',borderColor:a[1]},`<div style="font-size:62px;color:${a[1]};line-height:1.1">${a[2]}</div>${a[0]}<div style="position:absolute;top:18px;right:20px;width:18px;height:18px;border-radius:50%;background:#34C759;box-shadow:0 0 12px #34C759;opacity:${(t*2%1)<.6?1:.4}"></div>`);
  e.style.transform=`scale(${cl(k,0,1.2)}) translateY(${(1-k)*80}px)`;e.style.opacity=cl((t-s)/.15);R.append(e)});

});
S.push(function(t,d){base('#FF7A45');hdr(t,'','КАК ЭТО УСТРОЕНО');const w=win(t,'агент · настройки',.15);
 const rows=[['Роль','Секретарь'],['Инструкции','разбирай почту, пиши вежливо, коротко'],['Доступ','почта · календарь'],['Модель','Claude']];
 rows.forEach((r,i)=>{const s=.4+i*.35;if(t<s)return;const q=pr(t,s,.3);w.append(el('div',null,{position:'absolute',left:'40px',right:'40px',top:(120+i*150)+'px',height:'120px',borderRadius:'22px',background:'#1f2230',display:'flex',alignItems:'center',padding:'0 30px',gap:'26px',opacity:q,transform:`translateX(${(1-q)*120}px)`},`<span style="color:#FF7A45;font-weight:900;font-size:30px;min-width:230px">${r[0]}</span><span style="font-size:32px;font-weight:700">${typed(r[1],t,s+.15,40)}</span>`))});
 pill(t,d*.75,'1 АГЕНТ = 1 РОЛЬ');
});
function inbox(t,d){base('#4FD1FF');hdr(t,'01','СЕКРЕТАРЬ','почта');const w=win(t,'Входящие',.15);
 const m=[['Поставщик','Счёт за октябрь','СЧЕТА'],['Клиент Анна','Когда будет готово?','СРОЧНО'],['Рассылка','Скидки недели','ПОТОМ'],['Партнёр','Встреча в четверг?','ВСТРЕЧИ']];
 m.forEach((x,i)=>{const s=.35+i*.18;if(t<s)return;const q=pr(t,s,.3);const tg=t>1.2+i*.2;
  w.append(el('div',null,{position:'absolute',left:'36px',right:'36px',top:(110+i*118)+'px',height:'100px',borderRadius:'18px',background:'#1f2230',display:'flex',alignItems:'center',padding:'0 26px',gap:'20px',opacity:q},`<div style="font-size:30px;font-weight:800;min-width:250px">${x[0]}</div><div style="font-size:26px;color:#9aa0b4;font-weight:600">${x[1]}</div>${tg?`<div style="margin-left:auto;font-size:22px;font-weight:900;padding:6px 14px;border-radius:12px;background:${i==1?'#FF3B30':'#4FD1FF'};color:#0a0b0f;transform:scale(${back((t-1.2-i*.2)/.3)})">${x[2]}</div>`:''}`))});
 const ds=d*.55;if(t>ds){const q=pr(t,ds,.4);w.append(el('div',null,{position:'absolute',left:'36px',right:'36px',top:'600px',borderRadius:'22px',background:'#14303d',border:'2px solid #4FD1FF',padding:'24px 28px',fontSize:'30px',lineHeight:'1.35',fontWeight:'600',opacity:q,transform:`translateY(${(1-q)*60}px)`},`<div style="color:#4FD1FF;font-weight:900;font-size:24px;margin-bottom:8px">ЧЕРНОВИК ОТВЕТА · Анне</div>${typed('Анна, добрый день! Всё будет готово в пятницу до 18:00 — пришлю сразу.',t,ds+.3,40)}`))}
}
S.push(inbox);
S.push(function(t,d){base('#FF5FD2');hdr(t,'02','МАРКЕТОЛОГ','контент-план');const w=win(t,'План на неделю',.15);
 const days=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'],tp=['Рилс','Пост','Сторис','Рилс','Карусель','Сторис','Рилс'],c=['#FF5FD2','#4FD1FF','#FFC24D','#FF5FD2','#34C759','#FFC24D','#FF5FD2'];
 days.forEach((x,i)=>{const s=.4+i*.17;const q=pr(t,s,.3);const r=el('div',null,{position:'absolute',left:'36px',right:'36px',top:(105+i*104)+'px',height:'88px',borderRadius:'16px',background:'#1f2230',display:'flex',alignItems:'center',padding:'0 24px',gap:'22px',opacity:.35+.65*q},`<div style="font-weight:900;font-size:30px;width:60px;color:#9aa0b4">${x}</div>`);
  if(t>s){r.innerHTML+=`<div style="font-size:24px;font-weight:900;padding:6px 16px;border-radius:12px;background:${c[i]};color:#0a0b0f;transform:scale(${back((t-s)/.3)})">${tp[i]}</div><div style="height:14px;border-radius:7px;background:#3a3d4c;width:${380*q}px"></div>`}
  w.append(r)});
 pill(t,d*.72,'ТЕКСТЫ НА НЕДЕЛЮ');
});
S.push(function(t,d){base('#34C759');hdr(t,'03','АНАЛИТИК','отчёт');const w=win(t,'выгрузка.csv → отчёт',.15);
 const raw='дата;товар;сумма\n01.10;А;12400\n01.10;Б;8300\n02.10;А;15100\n02.10;В;4200\n03.10;Б;9900';
 const k=pr(t,1.4,.5);const code=el('div','mono',{position:'absolute',left:'40px',top:'110px',fontSize:'30px',lineHeight:'1.5',whiteSpace:'pre',color:'#9aa0b4',opacity:1-k*.85,filter:`blur(${k*4}px)`},typed(raw,t,.3,60));w.append(code);
 if(t>1.4){const r=el('div',null,{position:'absolute',left:'36px',right:'36px',top:'110px',borderRadius:'22px',background:'#13261b',border:'2px solid #34C759',padding:'28px',opacity:k,transform:`scale(${.9+.1*k})`});
  r.innerHTML=`<div style="font-size:26px;font-weight:900;color:#34C759">ОТЧЁТ · 1–3 ОКТЯБРЯ</div><div style="display:flex;gap:16px;align-items:flex-end;height:180px;margin:24px 0">${[62,100,45].map((h,i)=>`<div style="flex:1;height:${h*pr(t,1.7+i*.15,.5)}%;background:${i==1?'#34C759':'#2f6b45'};border-radius:10px"></div>`).join('')}</div>`+
  ['Товар А — лидер продаж','Товар В отстаёт — проверить цену','Среда — лучший день'].map((x,i)=>`<div style="font-size:30px;font-weight:700;margin-top:14px;opacity:${pr(t,2.3+i*.3,.3)}">→ ${x}</div>`).join('');w.append(r)}
});
S.push(function(t,d){base('#FFC24D');hdr(t,'04','ПОДДЕРЖКА','база знаний');const w=win(t,'Чат с клиентом',.15);
 const q='Здравствуйте! Вы доставляете в выходные?';const b1=el('div','bub',{left:'30px',top:'110px',background:'#232634',color:'#eef0f6'},typed(q,t,.3,40));w.append(b1);
 if(t>1.6){const kb=el('div',null,{position:'absolute',right:'40px',top:'300px',fontSize:'24px',fontWeight:'800',color:'#FFC24D',opacity:pr(t,1.6,.3)},'📄 база знаний · доставка');w.append(kb)}
 if(t>2.0){const b2=el('div','bub',{right:'30px',top:'360px',background:'#FFC24D',color:'#111'},typed('Да! В субботу и воскресенье с 10 до 18, по городу бесплатно от 2 000 ₽.',t,2.0,45));w.append(b2)}
 pill(t,d*.78,'ОТВЕТ ЗА СЕКУНДЫ');
});
S.push(function(t,d){base('#FF7A45','#FF7A4540');hdr(t,'05','ДИРЕКТОР','раздаёт задачи');
 const cx=540,cy=760;const sv=document.createElementNS('http://www.w3.org/2000/svg','svg');sv.setAttribute('width',1080);sv.setAttribute('height',1300);sv.style.position='absolute';sv.style.left='0';sv.style.top='0';R.append(sv);
 const pts=[[200,520],[880,520],[200,1000],[880,1000]];
 pts.forEach((p,i)=>{const s=.4+i*.15;if(t<s)return;const k=pr(t,s,.4);const x2=cx+(p[0]-cx)*k,y2=cy+(p[1]-cy)*k;
  sv.innerHTML+=`<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="${OA[i][1]}" stroke-width="5" stroke-dasharray="14 10" stroke-dashoffset="${-t*60}"/>`;
  const ph=((t*1.2+i*.25)%1);sv.innerHTML+=`<circle cx="${cx+(p[0]-cx)*ph}" cy="${cy+(p[1]-cy)*ph}" r="10" fill="${OA[i][1]}"/>`;
  const e=el('div','chip',{left:(p[0]-130)+'px',top:(p[1]-80)+'px',width:'260px',height:'160px',fontSize:'26px',borderColor:OA[i][1],transform:`scale(${back((t-s)/.4)})`},`<div style="font-size:48px;color:${OA[i][1]}">${OA[i][2]}</div>${OA[i][0]}`);R.append(e)});
 const c=el('div','chip',{left:(cx-150)+'px',top:(cy-150)+'px',width:'300px',height:'300px',fontSize:'40px',borderColor:'#FF7A45',background:'linear-gradient(145deg,#2a1d17,#1b1c26)',transform:`scale(${back(t/.4)})`},'<div style="font-size:90px;color:#FF7A45">★</div>ДИРЕКТОР');R.append(c);
 const ms=d*.6;if(t>ms){const q=pr(t,ms,.4);R.append(el('div',null,{position:'absolute',left:'90px',right:'90px',top:'1090px',borderRadius:'26px',background:'#1c1e2a',border:'2px solid #FF7A45',padding:'22px 28px',fontSize:'30px',fontWeight:'700',lineHeight:'1.35',opacity:q,transform:`translateY(${(1-q)*60}px)`},'<span style="color:#FF7A45;font-weight:900">ИТОГ ДНЯ:</span> 12 писем разобрано · план готов · отчёт отправлен · 31 ответ клиентам'))}
});
S.push(function(t,d){cta(t,d,'ОФИС',['схема ИИ-офиса','инструкции для 5 агентов','как запустить за вечер'],'#FF7A45')});
