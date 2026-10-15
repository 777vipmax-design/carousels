// ИИ ищет клиентов (КЛИЕНТЫ)
function mapbg(op){const m=el('div',null,{position:'absolute',left:'60px',right:'60px',top:'560px',height:'640px',borderRadius:'36px',overflow:'hidden',background:'#121620',border:'2px solid #2b2e3c',opacity:op});
 m.innerHTML='<svg width="960" height="640" style="position:absolute;inset:0"><path d="M0 200 Q300 150 480 260 T960 220" stroke="#22283a" stroke-width="26" fill="none"/><path d="M200 0 Q260 300 180 640" stroke="#22283a" stroke-width="20" fill="none"/><path d="M700 0 Q640 320 760 640" stroke="#22283a" stroke-width="22" fill="none"/><path d="M0 480 L960 430" stroke="#22283a" stroke-width="16"/></svg>';R.append(m);return m}
const PINS=[[160,120],[420,90],[700,160],[300,300],[560,260],[820,330],[120,430],[460,470],[680,520],[880,120]];
S.push(function(t,d){base('#34C759','#34C75940');
 bigt(t,.05,'CLAUDE НАХОДИТ',180,92);bigt(t,.3,'КЛИЕНТОВ',300,140).style.color='#34C759';
 const m=mapbg(pr(t,.3,.4));
 PINS.forEach((p,i)=>{const s=.8+i*.12;if(t<s)return;const k=back((t-s)/.4);m.append(el('div',null,{position:'absolute',left:(p[0]-25)+'px',top:(p[1]-60*k)+'px',fontSize:'56px',transform:`scale(${cl(k,0,1.2)})`},'📍'))});
 pill(t,2.4,'+ ЛИЧНОЕ ПРЕДЛОЖЕНИЕ КАЖДОМУ','#34C759',null,1240);
});
S.push(function(t,d){base('#34C759');hdr(t,'01','ЗАДАЧА');const w=win(t,'Claude · новый чат',.15);
 w.append(el('div','bub me',{top:'110px',background:'#34C759'},typed('Найди 20 компаний моей ниши в моём городе',t,.35,32)+(t<1.8?'▌':'')));
 if(t>1.9){const l=['Студия «Линия» · 4,6 ★','Салон «Мята» · 4,1 ★','«Барбер №1» · 4,8 ★','«Красота+» · 3,9 ★'];l.forEach((x,i)=>{const s=1.9+i*.15;if(t<s)return;w.append(el('div',null,{position:'absolute',left:'36px',right:'36px',top:(300+i*105)+'px',height:'90px',borderRadius:'16px',background:'#1f2230',display:'flex',alignItems:'center',padding:'0 26px',gap:'18px',fontSize:'30px',fontWeight:'700',opacity:pr(t,s,.25)},`📍 ${x}`))});
  w.append(el('div',null,{position:'absolute',left:'40px',top:'730px',fontSize:'26px',color:'#9aa0b4',fontWeight:'700',opacity:pr(t,2.6,.3)},'… и ещё 16 компаний · пример'))}
});
S.push(function(t,d){base('#34C759');hdr(t,'02','ИЗУЧАЕТ КАЖДУЮ');const w=win(t,'Салон «Мята»',.15);
 const r=[['Сайт','🌐'],['Отзывы','★'],['Соцсети','📸']];
 r.forEach((x,i)=>{const s=.4+i*.4;const k=pr(t,s,.9);w.append(el('div',null,{position:'absolute',left:'40px',right:'40px',top:(140+i*170)+'px'},`<div style="display:flex;justify-content:space-between;font-size:34px;font-weight:800"><span>${x[1]} ${x[0]}</span><span style="color:#34C759">${k>=1?'✓ изучено':Math.round(k*100)+'%'}</span></div><div style="height:22px;border-radius:11px;background:#1f2230;margin-top:16px"><div style="height:100%;width:${k*100}%;border-radius:11px;background:#34C759"></div></div>`))});
});
S.push(function(t,d){base('#FF3B30');hdr(t,'03','ЧЕГО НЕ ХВАТАЕТ');const w=win(t,'Салон «Мята» · находки',.15);
 const r=['нет онлайн-записи','на отзывы не отвечают','фото работ двухлетней давности'];
 r.forEach((x,i)=>{const s=.4+i*.35;if(t<s)return;const q=pr(t,s,.3);w.append(el('div',null,{position:'absolute',left:'36px',right:'36px',top:(130+i*150)+'px',height:'120px',borderRadius:'20px',background:'#2a1516',border:'2px solid #FF3B30',display:'flex',alignItems:'center',gap:'24px',padding:'0 30px',fontSize:'34px',fontWeight:'800',opacity:q,transform:`translateX(${(1-q)*100}px)`},`<span style="color:#FF3B30;font-size:44px">!</span>${x}`))});
});
S.push(function(t,d){base('#34C759');hdr(t,'04','ПИШЕТ ЛИЧНО');const w=win(t,'Письмо · Салон «Мята»',.15);
 const txt='Здравствуйте! Видел ваши отзывы — клиенты хвалят мастеров, но жалуются, что сложно записаться. Могу настроить онлайн-запись за 3 дня. Показать, как это будет выглядеть у вас?';
 w.append(el('div',null,{position:'absolute',left:'44px',right:'44px',top:'120px',fontSize:'36px',lineHeight:'1.45',fontWeight:'600'},typed(txt,t,.3,42).replace('клиенты хвалят мастеров','<span style="background:#34C75944">клиенты хвалят мастеров</span>').replace('сложно записаться','<span style="background:#34C75944">сложно записаться</span>')));
 pill(t,d*.78,'НЕ ШАБЛОН','#34C759');
});
S.push(function(t,d){base('#34C759');hdr(t,'05','ТЫ ПРОВЕРЯЕШЬ');const w=win(t,'Черновики · 20',.15);
 const r=['Салон «Мята»','Студия «Линия»','«Барбер №1»','«Красота+»'];
 r.forEach((x,i)=>{const s=.3+i*.12;if(t<s)return;const sent=t>1.2+i*.45;
  w.append(el('div',null,{position:'absolute',left:'36px',right:'36px',top:(110+i*130)+'px',height:'110px',borderRadius:'18px',background:'#1f2230',display:'flex',alignItems:'center',padding:'0 26px',fontSize:'32px',fontWeight:'700',opacity:pr(t,s,.25)},`${x}<div style="margin-left:auto;font-size:26px;font-weight:900;padding:10px 20px;border-radius:14px;background:${sent?'#34C759':'#3a3d4c'};color:${sent?'#0a0b0f':'#fff'}">${sent?'✓ отправлено':'проверить'}</div>`))});
 pill(t,d*.7,'БЕЗ СПАМА','#fff');
});
S.push(function(t,d){cta(t,d,'КЛИЕНТЫ',['готовый запрос целиком','как выбрать нишу и город','шаблон первого письма'],'#34C759')});
