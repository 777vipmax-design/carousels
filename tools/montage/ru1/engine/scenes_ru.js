// Сцены для рилсов по русификации: eq (ноутбук + флешка = ...), map (точки-заявки по городам)
function usbIcon(c){return `<div style="position:relative;width:150px;height:70px;margin:0 auto"><div style="position:absolute;left:0;top:0;width:110px;height:70px;border-radius:14px;background:${c}"></div><div style="position:absolute;left:108px;top:14px;width:42px;height:42px;border-radius:4px;background:#c9ccd8"></div><div style="position:absolute;left:122px;top:24px;width:8px;height:8px;background:#555"></div><div style="position:absolute;left:122px;top:38px;width:8px;height:8px;background:#555"></div></div>`}
function sceneEq(t, d, L) {
  const c = L.color || ACC; base(c, c + '40');
  const card = (x, icon, name, s) => { if (t < s) return; const p = back((t - s) / .45);
    R.append(el('div', 'chip', { left: x + 'px', top: '330px', width: '380px', height: '330px', borderColor: c, transform: `scale(${cl(p, 0, 1.2)})`, gap: '30px' },
      (icon === 'usb' ? usbIcon(c) : `<div style="font-size:130px;line-height:1">${icon}</div>`) + `<div style="font-size:52px">${name}</div>`)); };
  card(90, L.a[0], L.a[1], .05);
  if (t > .35) { const e = el('div', 'big', { top: '420px', fontSize: '130px', color: c }, '+'); e.style.opacity = pr(t, .35, .2); R.append(e); }
  card(610, L.b[0], L.b[1], .45);
  if (t > .8) { const e = el('div', 'big', { top: '720px', fontSize: '150px', color: '#fff' }, '='); e.style.opacity = pr(t, .8, .2); R.append(e); }
  if (L.res && t > 1.1) { const sz = Math.min(150, Math.floor(940 / (L.res.length * .68))); const e = bigt(t, 1.1, L.res, 920, sz, c); e.style.whiteSpace = 'nowrap'; }
  if (L.sub && t > 1.6) { const b = el('div', 'big', { top: '1110px', fontSize: '50px', color: '#c9ccd8', padding: '0 80px' }, L.sub); b.style.opacity = pr(t, 1.6, .4); R.append(b); }
}
const RU = [[28,60],[30,69],[40,68],[60,70],[80,73],[100,77],[120,73],[140,72],[160,70],[180,68],[178,64],[160,60],[142,47],[135,43],[131,43],[130,48],[120,53],[105,50],[88,49],[80,51],[70,55],[60,51],[50,51],[47,42],[40,44],[38,47],[32,52],[28,56]];
const MX = lon => 40 + (lon - 26) / 156 * 1000, MY = lat => 1230 - (lat - 42) / 36 * 880;
function inPoly(x, y, P) { let r = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, yi] = P[i], [xj, yj] = P[j]; if ((yi > y) != (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) r = !r; } return r; }
const DOTS = []; for (let lon = 27; lon < 181; lon += 3.2) for (let lat = 42; lat < 78; lat += 1.5) if (inPoly(lon, lat, RU)) DOTS.push([MX(lon), MY(lat)]);
function sceneMap(t, d, L) {
  const c = L.color || ACC; base(c, c + '30'); if (L.title) hdr(t, L.num || '', L.title, L.tag);
  const m = el('div', null, { position: 'absolute', inset: '0', opacity: pr(t, 0, .4) });
  DOTS.forEach(([x, y]) => m.append(el('div', null, { position: 'absolute', left: x + 'px', top: y + 'px', width: '7px', height: '7px', borderRadius: '50%', background: 'rgba(255,255,255,.16)' })));
  R.append(m);
  const pins = L.pins || []; const step = Math.min(.55, (d * .7) / Math.max(1, pins.length));
  pins.forEach((p, i) => { const [name, lon, lat, dx, dy, txt] = p; const s = .3 + i * step; if (t < s) return;
    const x = MX(lon), y = MY(lat), q = back((t - s) / .35), k = cl(q, 0, 1.2);
    const pulse = 1 + .5 * ((t - s) % 1.2) / 1.2;
    R.append(el('div', null, { position: 'absolute', left: (x - 16) + 'px', top: (y - 16) + 'px', width: '32px', height: '32px', borderRadius: '50%', background: c, boxShadow: `0 0 30px ${c}`, transform: `scale(${k})` }));
    R.append(el('div', null, { position: 'absolute', left: (x - 16) + 'px', top: (y - 16) + 'px', width: '32px', height: '32px', borderRadius: '50%', border: `3px solid ${c}`, opacity: 2 - pulse * 1.33, transform: `scale(${pulse * 1.6})` }));
    const lx = x + (dx || 0), ly = y + (dy || -110);
    if (dx || dy) { const tx = lx, ty = ly + 30, len = Math.hypot(tx - x, ty - y), ang = Math.atan2(ty - y, tx - x) * 180 / Math.PI;
      R.append(el('div', null, { position: 'absolute', left: x + 'px', top: y + 'px', width: (len * cl(k)) + 'px', height: '3px', background: c + '99', transformOrigin: '0 50%', transform: `rotate(${ang}deg)` })); }
    const b = el('div', null, { position: 'absolute', left: lx + 'px', top: ly + 'px', transform: `translate(-50%,0) scale(${k})`, background: 'rgba(28,30,42,.95)', border: `2px solid ${c}`, borderRadius: '22px', padding: '8px 20px', whiteSpace: 'nowrap', textAlign: 'center', boxShadow: '0 16px 40px rgba(0,0,0,.5)' },
      `<div style="font-weight:900;font-size:32px">${name}</div>` + (txt ? `<div style="font-weight:700;font-size:28px;color:${c}">${txt}</div>` : ''));
    R.append(b); });
  if (L.pill) pill(t, d * .8, L.pill, c, null, 1235);
}
KIND.eq = sceneEq; KIND.map = sceneMap;
