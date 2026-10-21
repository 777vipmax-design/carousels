"""Замазать личные данные на слайдах разборов: python3 tools/stories/redact.py"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
D = 'media/stories/main3/src/'
F = '/usr/share/fonts/opentype/inter/'
med = lambda s: ImageFont.truetype(F + 'Inter-Medium.otf', s)
semi = lambda s: ImageFont.truetype(F + 'Inter-SemiBold.otf', s)
bold = lambda s: ImageFont.truetype(F + 'Inter-Bold.otf', s)

def text_color(a, y0, y1, x0, x1):
    sub = a[y0:y1, x0:x1].reshape(-1, 3)
    return tuple(int(v) for v in sub[sub.sum(1).argmax()])

def line(im, a, y0, y1, x0, x1, new, size=17, fnt=semi):
    bg = tuple(int(v) for v in a[y0 - 2, x1 - 4])
    col = text_color(a, y0, y1, x0, x1)
    d = ImageDraw.Draw(im)
    d.rectangle([x0, y0 - 3, x1, y1 + 4], fill=bg)
    d.text((x0, (y0 + y1) / 2), new, font=fnt(size), fill=col, anchor='lm')

def pill(im, a, x0, y0, y1, label):
    col = tuple(int(v) for v in a[y0 + 20, x0 + 10])
    d = ImageDraw.Draw(im)
    d.rectangle([x0 - 2, y0 - 2, 700, y1 + 2], fill=tuple(int(v) for v in a[y0 - 6, 720]))
    f = bold(20)
    # буквы с разрядкой, как в оригинале
    w = sum(d.textlength(ch, font=f) + 1.5 for ch in label)
    d.rounded_rectangle([x0, y0, x0 + w + 32, y1], radius=(y1 - y0) // 2, fill=col)
    x = x0 + 16
    for ch in label:
        d.text((x, (y0 + y1) / 2), ch, font=f, fill=(26, 22, 18), anchor='lm')
        x += d.textlength(ch, font=f) + 1.5

def go(name, ops):
    im = Image.open(D + name + '.png').convert('RGB')
    a = np.asarray(im).astype(int)
    for op in ops:
        op(im, a)
    im.save(D + name + '_r.png')

go('shop1', [lambda im, a: pill(im, a, 56, 510, 552, 'SEO-АУДИТ · МАГАЗИН КЛИЕНТА'),
             lambda im, a: line(im, a, 1162, 1181, 90, 525, 'Два разных названия бренда на сайте'),
             lambda im, a: line(im, a, 1136, 1157, 580, 1015, 'Офлайн-магазин в Москве')])
go('shop2', [])
go('shop3', [lambda im, a: line(im, a, 974, 991, 724, 1015, '+ офлайн-магазин', size=15)])
go('law1', [lambda im, a: pill(im, a, 56, 510, 552, 'SEO-АУДИТ · САЙТ КЛИЕНТА'),
            lambda im, a: line(im, a, 1191, 1212, 580, 1015, 'Большой опыт и регалии юриста')])
go('law2', []); go('law3', [])
