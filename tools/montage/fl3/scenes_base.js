// Универсальные сцены: каждая строка сценария (SCRIPT.lines) = одна сцена.
// Типы: hook, list, chat, code, number, cta. Цвет сцены — поле color.
const ACC = (SCRIPT.color || '#FF7A45');
function sceneHook(t, d, L) {
  const c = L.color || ACC; base(c, c + '40');
  bigt(t, .05, L.title || '', 220, L.title && L.title.length > 12 ? 110 : 150);
  if (L.sub) { const b = el('div', 'big', { top: '420px', fontSize: '64px', color: c }, L.sub); b.style.opacity = pr(t, .4, .4); R.append(b); }
  (L.chips || []).forEach((x, i) => {
    const s = .7 + i * .2; if (t < s) return; const col = i % 2, row = Math.floor(i / 2);
    const e = el('div', 'chip', { left: (110 + col * 520) + 'px', top: (620 + row * 240) + 'px', width: '340px', height: '200px', fontSize: '34px', borderColor: c, transform: `scale(${back((t - s) / .4)})` }, x);
    R.append(e);
  });
  if (L.badge) pill(t, 1.6, L.badge, '#34C759', null, 1150);
}
function sceneList(t, d, L) {
  const c = L.color || ACC; base(c); hdr(t, L.num || '', L.title || '', L.tag);
  const w = win(t, L.window || '', .15);
  (L.items || []).forEach((x, i) => {
    const s = .4 + i * Math.min(.5, (d * .6) / Math.max(1, L.items.length)); if (t < s) return; const q = pr(t, s, .3);
    w.append(el('div', null, { position: 'absolute', left: '36px', right: '36px', top: (110 + i * 130) + 'px', height: '110px', borderRadius: '20px', background: '#1f2230', display: 'flex', alignItems: 'center', gap: '24px', padding: '0 30px', fontSize: '34px', fontWeight: '800', opacity: q, transform: `translateX(${(1 - q) * 100}px)` },
      `<span style="color:${c};font-size:40px">✓</span>${x}`));
  });
  if (L.pill) pill(t, d * .75, L.pill, c);
}
function sceneChat(t, d, L) {
  const c = L.color || ACC; base(c); hdr(t, L.num || '', L.title || '', L.tag);
  const w = win(t, L.window || 'Claude', .15);
  const q = L.prompt || ''; const qs = .35, qd = q.length / 32;
  w.append(el('div', 'bub me', { top: '110px', background: c }, typed(q, t, qs, 32) + (t < qs + qd ? '▌' : '')));
  if (L.answer && t > qs + qd + .3) {
    w.append(el('div', 'bub', { left: '30px', top: '360px', background: '#232634', color: '#eef0f6', whiteSpace: 'pre-wrap' }, typed(L.answer, t, qs + qd + .3, 45)));
  }
  if (L.pill) pill(t, d * .78, L.pill, c);
}
function sceneCode(t, d, L) {
  const c = L.color || ACC; base(c); hdr(t, L.num || '', L.title || '', L.tag);
  const w = win(t, L.window || 'терминал', .15);
  const full = (L.code || '').replace(/\\n/g, '\n'); const n = Math.floor(cl((t - .4) * 40, 0, full.length));
  w.append(el('div', 'mono', { position: 'absolute', left: '40px', right: '40px', top: '120px', fontSize: '32px', lineHeight: '1.5', whiteSpace: 'pre-wrap', color: '#e8e2cf' }, full.slice(0, n).replace(/</g, '&lt;') + (t % .8 < .4 ? '▌' : '')));
  if (L.pill) pill(t, d * .75, L.pill, c);
}
function sceneNumber(t, d, L) {
  const c = L.color || ACC; base(c, c + '40'); hdr(t, L.num || '', L.title || '');
  const v = Number(L.value || 0) * pr(t, .2, Math.min(1.8, d * .5));
  const txt = (L.decimals ? v.toFixed(L.decimals) : Math.round(v).toLocaleString('ru-RU')) + (L.suffix || '');
  R.append(el('div', 'big', { top: '640px', fontSize: '170px', color: c }, txt));
  if (L.label) R.append(el('div', 'big', { top: '850px', fontSize: '50px', color: '#9aa0b4', opacity: pr(t, 1, .4) }, L.label));
}
function sceneCta(t, d, L) { cta(t, d, L.word || 'СЛОВО', L.items || [], L.color || ACC); }
const KIND = { hook: sceneHook, list: sceneList, chat: sceneChat, code: sceneCode, number: sceneNumber, cta: sceneCta };

