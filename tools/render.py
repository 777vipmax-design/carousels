from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, sys, json

import pathlib
T = str(pathlib.Path(__file__).resolve().parent.parent / 'templates') + '/'
TPL = {'A': T + 'A_fon.png', 'B': T + 'B_derzhit.png', 'V': T + 'V_palec.png', 'G': T + 'G_vozmushchenie.png'}
LIMIT = {'A': 1360, 'B': 740, 'V': 740, 'G': 740}  # bottom edge for text
F = '/usr/share/fonts/opentype/inter/Inter-'
def font(w, s): return ImageFont.truetype(F + w + '.otf', s)

WHITE = (255, 255, 255); RED = (255, 59, 48); GREEN = (52, 199, 89); GREY = (170, 172, 178); DIM = (120, 122, 128)
W, H = 1086, 1448
M = 84
TW = W - 2 * M


def tokens(text, base):
    out = []
    for line in text.split('\n'):
        for w in line.split(' '):
            if not w: continue
            col = base
            if '*' in w:
                col = RED; w = w.replace('*', '')
            out.append((w.replace('_', ' '), col))
        out.append(('\n', None))
    return out[:-1]


def layout(text, fnt, base, width):
    lines, cur, cw = [], [], 0
    sp = fnt.getlength(' ')
    for w, c in tokens(text, base):
        if w == '\n':
            lines.append(cur); cur, cw = [], 0; continue
        lw = fnt.getlength(w)
        if cur and cw + sp + lw > width:
            lines.append(cur); cur, cw = [], 0
        cur.append((w, c, lw)); cw += (sp if len(cur) > 1 else 0) + lw
    lines.append(cur)
    return lines


def draw_text(d, x, y, text, fnt, base, width, lh, dry=False):
    lines = layout(text, fnt, base, width)
    sp = fnt.getlength(' ')
    for ln in lines:
        cx = x
        for w, c, lw in ln:
            if not dry: d.text((cx, y), w, font=fnt, fill=c)
            cx += lw + sp
        y += lh
    return y


def check_icon(d, x, y, s, col):
    d.ellipse((x, y, x + s, y + s), fill=col)
    d.line([(x + s * .27, y + s * .52), (x + s * .44, y + s * .69), (x + s * .74, y + s * .34)], fill=(17, 18, 20), width=max(3, s // 9), joint='curve')


def render(spec, out, dry=False):
    tpl = spec['tpl']
    im = Image.open(TPL[tpl]).convert('RGB')
    if tpl != 'A':
        # soften top so text reads cleanly
        pass
    d = ImageDraw.Draw(im)
    y = spec.get('top', 120)
    # page badge
    if not dry:
        bf = font('SemiBold', 26)
        b = spec['page']
        d.text((W - M - bf.getlength(b), 60), b, font=bf, fill=DIM)
    for el in spec['els']:
        k = el[0]
        if k == 'gap': y += el[1]
        elif k == 'num':
            f = font('Black', 120);
            if not dry: d.text((M - 4, y - 20), el[1], font=f, fill=RED)
            y += 118
        elif k == 'kicker':
            f = font('Bold', 30)
            if not dry: d.text((M, y), el[1].upper(), font=f, fill=RED)
            y += 52
        elif k == 'title':
            s = el[2] if len(el) > 2 else 66
            y = draw_text(d, M, y, el[1], font('Black', s), WHITE, TW, int(s * 1.1), dry)
        elif k == 'body':
            s = el[2] if len(el) > 2 else 46
            col = el[3] if len(el) > 3 else (225, 226, 230)
            y = draw_text(d, M, y, el[1], font('Medium', s), col, TW, int(s * 1.32), dry)
        elif k == 'stat':
            ss = el[3] if len(el) > 3 else 150
            txt = el[1].replace('_', ' ')
            f = font('Black', ss)
            if not dry: d.text((M - 6, y - int(ss * .2)), txt, font=f, fill=RED)
            sw = f.getlength(txt) + 34
            cf = font('SemiBold', 38)
            if el[2] and sw > TW * 0.45:
                # caption under the number when the number is wide
                y = draw_text(d, M, y + int(ss * .85), el[2], cf, WHITE, TW, 48, dry) + 6
            elif el[2]:
                yy = draw_text(d, M + sw, y + 8, el[2], cf, WHITE, TW - sw, 48, dry)
                y = max(y + int(ss * .85), yy)
            else:
                y += int(ss * .85)
            y += 8
        elif k == 'src':
            y = draw_text(d, M, y, el[1], font('Medium', 27), (140,142,148), TW, 36, dry)
        elif k == 'check':
            s = el[2] if len(el) > 2 else 42
            f = font('Bold', s)
            box_top = y
            ty = draw_text(d, M + 34 + 62, y + 30, el[1], f, WHITE, TW - 34 - 62 - 30, int(s * 1.3), True)
            hgt = ty - y + 30 - int(s * .3) + 4
            if not dry:
                d.rounded_rectangle((M, box_top, W - M, box_top + hgt), radius=26, fill=(23, 36, 27), outline=GREEN, width=3)
                check_icon(d, M + 30, box_top + 28, 50, GREEN)
                draw_text(d, M + 34 + 62, y + 30, el[1], f, WHITE, TW - 34 - 62 - 30, int(s * 1.3))
            y = box_top + hgt
        elif k == 'bubble':
            f = font('Black', 130)
            tw = f.getlength(el[1]); bw = tw + 120; bh = 190
            x0 = (W - bw) / 2
            if not dry:
                d.rounded_rectangle((x0, y, x0 + bw, y + bh), radius=40, fill=(30, 31, 35), outline=RED, width=4)
                d.polygon([(x0 + 70, y + bh - 2), (x0 + 70, y + bh + 40), (x0 + 120, y + bh - 2)], fill=(30, 31, 35))
                d.line([(x0 + 70, y + bh), (x0 + 70, y + bh + 40), (x0 + 120, y + bh)], fill=RED, width=4)
                d.text((x0 + 60, y + 18), el[1], font=f, fill=RED)
            y += bh + 40
        elif k == 'center':
            s = el[2] if len(el) > 2 else 40
            f = font(el[3] if len(el) > 3 else 'Bold', s)
            for ln in layout(el[1], f, WHITE, TW):
                lw = sum(t[2] for t in ln) + f.getlength(' ') * (len(ln) - 1)
                cx = (W - lw) / 2
                for w, c, l in ln:
                    if not dry: d.text((cx, y), w, font=f, fill=c)
                    cx += l + f.getlength(' ')
                y += int(s * 1.3)
        elif k == 'row':
            # small action row with bullet bar
            rs = el[2] if len(el) > 2 else 34
            f = font('SemiBold', rs)
            if not dry: d.rounded_rectangle((M, y + int(rs*.22), M + 8, y + int(rs*1.18)), radius=4, fill=RED)
            y = draw_text(d, M + 30, y, el[1], f, WHITE, TW - 30, int(rs*1.3), dry) + int(rs*.5)
    if y > LIMIT[tpl] and not dry:
        print('OVERFLOW', out, y, LIMIT[tpl])
    if not dry:
        im.save(out, optimize=True)
    return y


if __name__ == '__main__':
    slides = json.load(open(sys.argv[1]))
    od = sys.argv[2]; os.makedirs(od, exist_ok=True)
    for i, s in enumerate(slides, start=2):
        if 'top' not in s:
            h = render(s, None, dry=True) - 120
            area = (1300 if s['tpl']=='A' else LIMIT[s['tpl']]) - 120
            s['top'] = 120 + max(0, (area - h) // 2) if s['tpl']=='A' else 130
        y = render(s, f'{od}/{i:02d}.png')
        print(i, s['tpl'], 'bottom', y)
