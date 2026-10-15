function sceneCard(t, d, L) { const c = L.color || ACC; base(c, c + '30');
  // frame behind the overlaid card video (y 300..1260)
  R.append(el('div', null, { position: 'absolute', left: '0', right: '0', top: '300px', height: '960px', boxShadow: `0 0 120px ${c}33` }));
  if (L.label) { const p = pr(t, 0, .35); R.append(el('div', null, { position: 'absolute', left: '0', right: '0', top: '170px', textAlign: 'center', fontWeight: '900', fontSize: '56px', color: c, opacity: p, transform: `translateY(${(1 - p) * -30}px)` }, L.label)); }
}
function sceneClip(t, d, L) { base(L.color || ACC); }
function sceneQuote(t, d, L) { const c = L.color || ACC; base(c, c + '40');
  const [a, b] = (L.text || '').split('|');
  const A = el('div', 'big', { top: '560px', fontSize: (a.length > 14 ? 104 : 130) + 'px', padding: '0 70px' }, a); const p = back((t - .05) / .45);
  A.style.transform = `scale(${.6 + .4 * cl(p, 0, 1.2)})`; A.style.opacity = cl(t / .2); R.append(A);
  if (b) { const B = el('div', 'big', { top: '840px', fontSize: '64px', color: c, padding: '0 80px', lineHeight: '1.15' }, b); const q = pr(t, .35, .4); B.style.opacity = q; B.style.transform = `translateY(${(1 - q) * 30}px)`; R.append(B); }
  if (L.pill) pill(t, Math.min(1.2, d * .5), L.pill, c, null, 1100);
}
KIND.card = sceneCard; KIND.clip = sceneClip; KIND.quote = sceneQuote;
SCRIPT.lines.forEach(L => S.push((t, d) => (KIND[L.scene] || sceneList)(t, d, L)));
