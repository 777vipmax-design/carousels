// find-skills (ПОИСК)
S.push(function(t,d){base('#B388FF','#B388FF40');
 bigt(t,.05,'СКИЛЛ,',170,120);bigt(t,.25,'КОТОРЫЙ НАХОДИТ',310,78);bigt(t,.45,'СКИЛЛЫ',410,130).style.color='#B388FF';
 for(let i=0;i<24;i++){const c=i%6,r=Math.floor(i/6);const s=.6+i*.03;if(t<s)continue;const hit=i==14;
  R.append(el('div',null,{position:'absolute',left:(80+c*155)+'px',top:(640+r*155)+'px',width:'135px',height:'135px',borderRadius:'22px',background:hit&&t>1.6?'#B388FF':'#1c1e2a',border:'2px solid '+(hit&&t>1.6?'#fff':'#2b2e3c'),transform:`scale(${back((t-s)/.3)*(hit&&t>1.6?1.15:1)})`,opacity:t>1.6&&!hit?.35:1})) }
 const lx=80+(Math.sin(t*2.4)*.5+.5)*700,ly=640+(Math.cos(t*1.7)*.5+.5)*400;const mx=t>1.6?80+2*155+20:lx,my=t>1.6?640+2*155+20:ly;
 R.append(el('div',null,{position:'absolute',left:mx+'px',top:my+'px',fontSize:'150px',filter:'drop-shadow(0 10px 30px rgba(0,0,0,.6))'},'🔍'));
});
S.push(function(t,d){base('#B388FF');hdr(t,'','ТЫСЯЧИ СКИЛЛОВ');
 const off=(t*700)%160;
 for(let i=0;i<60;i++){const c=i%5,r=Math.floor(i/5);const y=380+r*160-off;if(y<330||y>1250)continue;
  R.append(el('div',null,{position:'absolute',left:(70+c*190)+'px',top:y+'px',width:'170px',height:'140px',borderRadius:'18px',background:'#1c1e2a',border:'2px solid #2b2e3c',padding:'16px'},`<div style="height:14px;width:70%;background:#3a3d4c;border-radius:7px"></div><div style="height:12px;width:50%;background:#2b2e3c;border-radius:6px;margin-top:12px"></div>`))}
 pill(t,d*.5,'ИСКАТЬ ВРУЧНУЮ — ДОЛГО','#FF3B30','#fff');
});
S.push(function(t,d){base('#B388FF');hdr(t,'','FIND-SKILLS','vercel-labs/skills');const w=win(t,'Claude Code',.15);
 w.append(el('div','bub me',{top:'110px',background:'#B388FF'},typed('Хочу делать презентации из PDF-отчётов',t,.4,32)+(t<1.8?'▌':'')));
 if(t>2.0)w.append(el('div',null,{position:'absolute',left:'40px',top:'330px',fontSize:'30px',fontWeight:'800',color:'#B388FF',opacity:pr(t,2.0,.3)},'⚙ использую скилл find-skills…'));
});
S.push(function(t,d){base('#B388FF');hdr(t,'','ИЩЕТ ЛУЧШИЙ');const w=win(t,'результаты поиска',.15);
 const r=[['pdf-to-slides','★ 4.9','12K',1],['deck-maker','★ 4.2','3K',0],['slides-lite','★ 3.8','900',0]];
 r.forEach((x,i)=>{const s=.4+i*.3;if(t<s)return;const q=pr(t,s,.3);const best=x[3]&&t>1.6;
  w.append(el('div',null,{position:'absolute',left:'36px',right:'36px',top:(110+i*150)+'px',height:'125px',borderRadius:'20px',background:best?'#241d38':'#1f2230',border:best?'3px solid #B388FF':'2px solid transparent',display:'flex',alignItems:'center',padding:'0 28px',gap:'26px',opacity:q},`<div class="mono" style="font-size:32px;font-weight:700">${x[0]}</div><div style="font-size:28px;color:#FFC24D;font-weight:800">${x[1]}</div><div style="font-size:26px;color:#9aa0b4;font-weight:700">⬇ ${x[2]}</div>${best?`<div style="margin-left:auto;font-size:24px;font-weight:900;background:#B388FF;color:#0a0b0f;padding:6px 14px;border-radius:12px;transform:scale(${back((t-1.6)/.3)})">ЛУЧШИЙ</div>`:''}`))});
 w.append(el('div',null,{position:'absolute',left:'40px',bottom:'40px',fontSize:'24px',color:'#6b7080',fontWeight:'600'},'пример выдачи'));
});
S.push(function(t,d){base('#34C759');hdr(t,'','ОДНОЙ КОМАНДОЙ');const w=win(t,'терминал',.15);
 const cmd='$ npx skills add …/pdf-to-slides';w.append(el('div','mono',{position:'absolute',left:'40px',top:'130px',fontSize:'36px',color:'#e8e2cf'},typed(cmd,t,.3,30)+(t<1.5?'▌':'')));
 if(t>1.5){const k=pr(t,1.5,.8);w.append(el('div',null,{position:'absolute',left:'40px',right:'40px',top:'260px',height:'26px',borderRadius:'13px',background:'#1f2230'},`<div style="height:100%;width:${k*100}%;background:#34C759;border-radius:13px"></div>`))}
 if(t>2.4)w.append(el('div','big',{top:'380px',fontSize:'70px',color:'#34C759',transform:`scale(${back((t-2.4)/.4)})`},'✓ УСТАНОВЛЕНО'));
});
S.push(function(t,d){base('#B388FF','#B388FF40');hdr(t,'','УСТАНОВОК');
 const n=Math.round(3800000*pr(t,.2,1.8));R.append(el('div','big',{top:'620px',fontSize:'170px',color:'#B388FF'},(n/1e6).toFixed(1).replace('.',',')+' МЛН'));
 R.append(el('div','big',{top:'830px',fontSize:'50px',color:'#9aa0b4',opacity:pr(t,1.2,.4)},'по данным каталога skills.sh'));
});
S.push(function(t,d){cta(t,d,'ПОИСК',['команда установки','10 запросов для поиска','топ скиллов для работы'],'#B388FF')});
