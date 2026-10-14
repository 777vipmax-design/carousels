// v4 «Я не программист, но сделал сайт»
function step(x,y,w,ic,title,sub,on,col){const b=el('div',null,{position:'absolute',left:x+'px',top:y+'px',width:w+'px',height:'250px',borderRadius:'26px',background:on?'#202331':'#16181f',border:`3px solid ${on?col:'#262935'}`,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'14px',transition:'none'});
 b.innerHTML=`<div style="width:90px;height:90px;border-radius:50%;background:${on?col:'#2a2d3a'};display:flex;align-items:center;justify-content:center;font-size:46px;font-weight:900;color:#111">${ic}</div><div style="font-size:34px;font-weight:900">${title}</div><div style="font-size:24px;color:#9aa0b4;font-weight:700">${sub}</div>`;return b}
CARDS.site=function(t){ // b=«сам выполняет» c=«принимает оплату»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const role=el('div','role');role.append(el('div','rname',null,'САЙТ РАБОТАЕТ САМ'));role.style.opacity=prog(t,0,.4);R.append(role);
 const S=[[0.3,'↓','ЗАКАЗ','принял'],[T('b'),'✦','НЕЙРОСЕТЬ','выполнила'],[T('c'),'₽','ОПЛАТА','получена']];
 S.forEach((s,i)=>{const on=t>s[0];const b=step(50+i*335,260,310,s[1],s[2],s[3],on,ACC);b.style.opacity=.35+.65*prog(t,s[0],.3);R.append(b);
  if(i<2){const a=el('div',null,{position:'absolute',left:(360+i*335)+'px',top:'365px',fontSize:'40px',fontWeight:'900',color:t>S[i+1][0]?ACC:'#3a3f55'},'→');R.append(a)}});
 const n=Math.floor(cl((t-T('c'))*3,0,99));
 if(t>T('c')){const c=el('div','big',{top:'620px',fontSize:'44px',color:'#c9ccd8'},`работает <span style="color:${ACC}">без меня</span> — днём и ночью`);c.style.opacity=prog(t,T('c'),.4);R.append(c)}
};
CARDS.brief=function(t){ // b=«вот что должен делать» c=«вот как выглядит заказ» d=«вот куда приходят деньги»
 const f=frame('','ТЗ — ПРОСТО СЛОВАМИ','Claude');intro(t,f);
 const M=[[T('b'),'Сайт: человек пишет пожелания — получает песню'],[T('c'),'Заказ: анкета → текст → оплата → готово'],[T('d'),'Деньги: приходят на мой кошелёк']];
 M.forEach((m,i)=>{if(t<m[0])return;const p=prog(t,m[0],.3);const b=el('div','bub me',{top:(100+i*130)+'px',fontSize:'30px',opacity:p,transform:`translateY(${(1-p)*30}px)`},m[1]);f.w.append(b)});
 if(t<T('b')){const h=el('div',null,{position:'absolute',left:'40px',top:'120px',fontSize:'40px',fontWeight:'800',color:'#9aa0b4'},'как простому разработчику…');h.style.opacity=prog(t,.3,.4);f.w.append(h)}
};
CARDS.dev=function(t){
 const f=frame('','КОД ПИШЕТ САМ','order.py');intro(t,f);
 const code=['def create_order(data):','    order = Order(**data)','    lyrics = ai.write(order)','    pay_link = payment.link(order)','    return pay_link'];
 const box=el('div','mono',{position:'absolute',left:'30px',right:'30px',top:'95px',fontSize:'30px',lineHeight:'1.6',whiteSpace:'pre'});
 let h='';code.forEach((l,i)=>{const s=.3+i*.35;if(t<s)return;const err=i==3&&t<2.6;const fixed=i==3&&t>=2.6;
  h+=`<div style="background:${err&&t>2.0?'rgba(255,59,48,.25)':fixed?'rgba(52,199,89,.18)':'transparent'};border-radius:6px;padding:0 8px">${l}${err&&t>2.0?'  <span style="color:#FF3B30">← ошибка</span>':''}${fixed?'  <span style="color:#34C759">✓ исправлено</span>':''}</div>`});
 box.innerHTML=h;f.w.append(box);
 pill(t,2.9,'✓ ТЕСТЫ ПРОЙДЕНЫ');
};
CARDS.hard=function(t){ // b=«там я задавал вопросы» c=«но он объяснял»
 const f=frame('','СЕРВЕР И ОПЛАТА','Claude');intro(t,f);
 const Qs=['Что такое DNS?','Куда вставить ключ?','Почему не приходит оплата?'];
 Qs.forEach((q,i)=>{const s=T('b')+i*.45;if(t<s)return;const p=prog(t,s,.3);f.w.append(el('div','bub me',{top:(95+i*100)+'px',fontSize:'30px',opacity:p*(t>T('c')?.45:1)},q))});
 if(t<T('b')){['сервер','домен','HTTPS','оплата','уведомления'].forEach((w,i)=>{const p=prog(t,.3+i*.15,.3);f.w.append(el('div','tag',{left:(40+(i%3)*290)+'px',top:(120+Math.floor(i/3)*110)+'px',background:'#2a2d3a',color:'#fff',fontSize:'36px',opacity:p},w))})}
 if(t>T('c')){const a=el('div','bub ai',{top:'400px',fontSize:'30px'},'Объясняю по шагам: 1) открой… 2) вставь… 3) проверь ✓');a.style.opacity=prog(t,T('c'),.3);f.w.append(a)}
 pill(t,T('c')+1.4,'РАЗОБРАЛСЯ ДАЖЕ Я');
};
CARDS.cost=function(t){ // b=«сейчас вечер и подписка»
 R.innerHTML='';R.append(el('div','bg'),el('div','grid'));
 const box=(y,label,big,sub,col,s)=>{const b=el('div',null,{position:'absolute',left:'70px',right:'70px',top:y+'px',height:'300px',borderRadius:'30px',background:'#1c1f2b',border:`3px solid ${col}`,padding:'30px 44px'});
  b.innerHTML=`<div style="font-size:34px;font-weight:800;color:#9aa0b4">${label}</div><div style="font-size:84px;font-weight:900;color:${col};margin-top:6px">${big}</div><div style="font-size:36px;font-weight:700;margin-top:6px">${sub}</div>`;const p=prog(t,s,.4);b.style.opacity=p;b.style.transform=`translateY(${(1-p)*40}px)`;R.append(b)};
 box(60,'РАНЬШЕ (по моей оценке)','СОТНИ ТЫСЯЧ ₽','+ штат программистов','#FF3B30',.2);
 box(420,'СЕЙЧАС','ВЕЧЕР','+ подписка на нейросети',ACC,T('b'));
};
