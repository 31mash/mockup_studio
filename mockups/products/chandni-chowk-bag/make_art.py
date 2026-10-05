"""Chandni Chowk bag artwork, laid out on the bag's real surfaces (1 unit = 0.1 mm).

- front.html: the front panel, a Hindi newspaper page (an op-ed on India-Pakistan
  cricket, as in the photo, with the neighbouring columns cut off by the bag's
  edges, as when a bag is cut from a bigger page), overprinted with the blue
  'Chandni Chowk to the Sky' rubber stamp. Top of the image = the top fold.
- flap.svg: the folded-over flap as seen from above: the page's running header.
  Top of the image = the fold, bottom = the flap's free edge.
- back.html: the back panel, seen from behind, upright: another page (a food
  story from old Delhi with a halftone photo, and small ads).

Run: python3 products/chandni-chowk-bag/make_art.py && node tools/raster.mjs products/chandni-chowk-bag/art
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

from brand.indigo import FONT, plane_svg  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm (1 unit = 0.1 mm = 1 CSS px in the HTML pages)
W, L = dims.W * U, dims.L * U
ART = os.path.join(HERE, 'art')
os.makedirs(ART, exist_ok=True)

PAPER = '#e9e8e3'  # newsprint, flat print colour
INK = '#2a2b2e'  # newspaper black on newsprint
RULE = '#626367'
STAMP = '#22508f'  # rubber-stamp blue, the photo's slightly greyed denim blue (multiplied over the paper)

BODY = 'Tiro Devanagari Hindi'
HEAD = 'Noto Serif Devanagari'

# ---------------------------------------------------------------- copy
# The op-ed of the photo: "Sooner or later, relations will mend", by a former
# Test cricketer, on whether India should tour Pakistan.
HEADLINE = 'देर-सबेर सुधर जाएंगे रिश्ते'
BYLINE = ('सुधीर खन्ना', 'पूर्व टेस्ट क्रिकेटर')
OPED = [
    'आम तौर पर माना जाता है कि खेल को खेल की तरह ही देखा जाना चाहिए और उसमें राजनीति या कूटनीति का प्रवेश नहीं होने देना चाहिए। '
    'लेकिन जब सवाल खिलाड़ियों की सुरक्षा का हो, तो बात बदल जाती है।',
    'अगले साल की शुरुआत में होने वाले भारत-पाकिस्तान क्रिकेट मुकाबलों को लेकर जो असमंजस बना हुआ है, उसकी सबसे बड़ी वजह यही है। '
    'सुरक्षा और दूसरी समस्याओं के बारे में आखिरी फैसला सरकार ही करती है। अगर सरकार की राय में यह दौरा भारतीय क्रिकेटरों की '
    'सुरक्षा की दृष्टि से अभी ठीक नहीं है, तो इस बारे में कोई भी फैसला लेने का अधिकार सरकार पर ही छोड़ दिया जाना चाहिए।',
    'यह दुर्भाग्यपूर्ण है, लेकिन अभी हालात बहुत उलझे हुए हैं। दोनों देशों के बीच अविश्वास की खाई बहुत गहरी हो गई है और इसे पाटे '
    'बगैर आपसी रिश्ते सुधारना बहुत मुश्किल है।',
    'फिर भी यह मान लेना गलत होगा कि यह सिलसिला हमेशा के लिए थम जाएगा। ऐसा हुआ तो एशिया का क्रिकेट कमज़ोर हो जाएगा। पहले भी '
    'ऐसे मौके आए हैं, जब किसी आतंकवादी हमले या सरहद पर तनाव के चलते दोनों देशों के बीच क्रिकेट मुकाबले रद्द करने की नौबत आई। '
    'हर बार कुछ समय बाद रिश्ते पटरी पर लौटे और मैदान फिर से दर्शकों से भर गए।',
    'मेरा मानना है कि खिलाड़ी हमेशा दोस्ती के सबसे अच्छे दूत रहे हैं। मैदान पर मुकाबला कितना भी कड़ा हो, मैच के बाद दोनों टीमों '
    'के खिलाड़ी एक-दूसरे से गले मिलते हैं। यही भावना दोनों देशों के लोगों को भी जोड़ती है। उम्मीद रखनी चाहिए कि हालात सुधरते ही '
    'यह सिलसिला फिर शुरू होगा। देर-सबेर ऐसा होना ही है।',
]
# The column cut off on the left: city news, a reader-debate box, more news.
CITY = [
    'राजधानी में इस साल सड़क हादसों में कमी आई है। यातायात पुलिस के मुताबिक नियम तोड़ने वालों पर सख्ती और जागरूकता अभियानों '
    'का असर अब दिखने लगा है। पिछले साल की तुलना में दुर्घटनाओं की संख्या करीब बीस फीसदी घटी है। पुलिस ने शहर के प्रमुख चौराहों '
    'पर नए कैमरे लगाए हैं, जिन पर करीब चार करोड़ रुपये खर्च हुए हैं।',
]
DEBATE = ('बहस', 'खेलें या नहीं')
WATER = [
    'क्या भारतीय टीम को पाकिस्तान का दौरा करना चाहिए? इस मुद्दे पर अपनी राय हमें लिखकर भेजें। चुनिंदा पत्र अगले रविवार के अंक '
    'में प्रकाशित किए जाएंगे।',
    'गर्मी शुरू होने से पहले ही शहर के कई इलाकों में पानी की किल्लत होने लगी है। लोगों का कहना है कि कई दिनों से नलों में पानी '
    'नहीं आया और उन्हें टैंकरों के भरोसे रहना पड़ रहा है। जल बोर्ड के अधिकारियों ने जल्द ही हालात सुधरने का भरोसा दिलाया है। '
    'उनका कहना है कि नई पाइपलाइन का काम अगले महीने तक पूरा हो जाएगा।',
]
# The column cut off on the right.
WEATHER_HEAD = 'ठंड ने दी दस्तक'
SCHOOLS = [
    'शिक्षा विभाग ने सभी सरकारी स्कूलों में पुस्तकालय खोलने का फैसला किया है। इसके लिए हर स्कूल को किताबें खरीदने के लिए अलग '
    'से बजट दिया जाएगा। विभाग का मानना है कि इससे बच्चों में पढ़ने की आदत बढ़ेगी।',
]
WEATHER = [
    'सुबह और शाम के समय हल्की धुंध छाने लगी है। मौसम विभाग के अनुसार अगले सप्ताह तापमान में और गिरावट आएगी। पहाड़ों पर हुई '
    'बर्फबारी का असर मैदानी इलाकों में भी दिखने लगा है। डॉक्टरों ने बुजुर्गों और बच्चों को खास एहतियात बरतने की सलाह दी है।',
]
# Below the fold rule: three more pieces.
SAFETY = [
    'कोई उल्लेखनीय सुधार नहीं हुआ है। आज भी महिलाओं के लिए सार्वजनिक स्थानों पर सुरक्षा को लेकर चिंता बनी हुई है। आबादी के '
    'हिसाब से देश में पुलिसकर्मियों की संख्या बहुत कम है। कई राज्यों में महिलाओं के खिलाफ अपराध भी बढ़ रहे हैं। विशेषज्ञों का '
    'कहना है कि केवल कानून बनाना काफी नहीं है।',
]
FOCUS = ('फोकस समस्याओं पर हो', [
    'पिछले दिनों जब एक संगठन पर आतंकवादियों से जुड़े होने का आरोप लगा, तब से मीडिया ने उस पर जमकर फोकस किया तथा इस मुद्दे को '
    'लगातार उछाला। लेकिन महंगाई, बिजली और पानी जैसी आम आदमी की असली समस्याएं चर्चा से बाहर हो गईं।',
])
PAIN = ('पीर पराई', [
    'किसी ने ठीक कहा है कि जाके पैर न फटी बिवाई, वो क्या जाने पीर पराई! सच यही है कि जिसने कभी दुख नहीं झेला, वह दूसरों का '
    'दर्द नहीं समझ सकता।',
])
# Running header on the flap.
HEADER = ('5', 'विचार', 'नई दिल्ली, रविवार, 14 मार्च')

# Back: a food story from old Delhi, with a halftone photo, and small ads.
FOOD_HEAD = 'चांदनी चौक की गलियों में स्वाद का सफर'
FOOD = [
    'पुरानी दिल्ली का चांदनी चौक सदियों से अपने पकवानों के लिए मशहूर है। यहां की तंग गलियों में सुबह होते ही गरम-गरम समोसे, '
    'कचौरी और जलेबी की खुशबू फैल जाती है। दूर-दूर से लोग यहां सिर्फ खाने के लिए आते हैं।',
    'दुकानदारों का कहना है कि उनके कई पकवानों की विधि पीढ़ियों से चली आ रही है। आलू का मसाला आज भी हाथ से कूटे गए मसालों से '
    'बनता है और समोसे देसी घी में धीमी आंच पर तले जाते हैं। शाम ढलते ही बाजार की रौनक और बढ़ जाती है और हर कोने पर चाट के '
    'ठेलों के आसपास भीड़ जुट जाती है।',
    'इतिहासकार बताते हैं कि यह बाजार मुगल काल में बसाया गया था। तब इसके बीच से एक नहर बहती थी, जिसके पानी में चांद की रोशनी '
    'झिलमिलाती थी। कहा जाता है कि इसी से इसका नाम चांदनी चौक पड़ा।',
]
CAPTION = 'जामा मस्जिद के पास शाम के समय बाजार की रौनक।'
METRO = ('मेट्रो की नई लाइन जल्द', [
    'राजधानी में मेट्रो की नई लाइन पर अगले महीने से यात्री सेवा शुरू हो जाएगी। इससे पुरानी दिल्ली आने-जाने वाले लाखों लोगों '
    'को राहत मिलेगी। अधिकारियों के मुताबिक नई लाइन पर हर पांच मिनट में एक ट्रेन चलेगी और स्टेशनों पर पार्किंग की सुविधा भी होगी।',
    'व्यापारियों का कहना है कि इससे बाजार में ग्राहकों की संख्या बढ़ेगी। अभी त्योहारों के दिनों में यहां की सड़कों पर इतनी भीड़ '
    'हो जाती है कि पैदल चलना भी मुश्किल हो जाता है। लोगों को उम्मीद है कि मेट्रो से सड़कों पर वाहनों का दबाव भी कम होगा।',
])
ADS = [
    ('आवश्यकता है', 'प्रतिष्ठित कंपनी को अनुभवी लेखाकार और कार्यालय सहायक चाहिए। इच्छुक उम्मीदवार अपना बायोडाटा भेजें।'),
    ('किराये के लिए', 'करोल बाग में दो कमरों का फ्लैट, बिजली-पानी की पूरी सुविधा। केवल परिवार वाले संपर्क करें।'),
    ('शिक्षा', 'दसवीं और बारहवीं के छात्रों के लिए गणित और विज्ञान की विशेष कक्षाएं। नया सत्र अगले सोमवार से।'),
]


# ---------------------------------------------------------------- page kit


def paras(ps):
    return ''.join(f'<p>{p}</p>' for p in ps)


def css():
    return f"""
#art {{ position: relative; overflow: hidden; background: {PAPER}; }}
#art > svg {{ position: absolute; left: 0; top: 0; }}
.col {{ position: absolute; overflow: hidden; font-family: '{BODY}'; font-size: 37px; line-height: 54px;
        color: {INK}; text-align: justify; text-justify: inter-word; hyphens: none; text-wrap: pretty; }}
.col p {{ margin: 0; text-indent: 40px; }}
.col p.first {{ text-indent: 0; }}
.multi {{ column-count: 2; column-gap: 40px; column-fill: auto; column-rule: 1.3px solid {RULE}; }}
.multi3 {{ column-count: 3; column-gap: 40px; column-fill: auto; column-rule: 1.3px solid {RULE}; }}
.hl {{ position: absolute; font-family: '{HEAD}'; font-weight: 700; color: {INK}; text-align: center;
       white-space: nowrap; line-height: 1; }}
.by {{ text-align: center; font-family: '{HEAD}'; font-weight: 700; font-size: 35px; line-height: 46px;
       margin: 2px 0 20px; text-indent: 0; }}
.by span {{ display: block; font-weight: 400; font-size: 30px; line-height: 40px; }}
.by:after {{ content: ''; display: block; width: 120px; margin: 10px auto 0; border-top: 1.3px solid {RULE}; }}
.vr {{ position: absolute; width: 0; border-left: 1.3px solid {RULE}; }}
.hr {{ position: absolute; height: 0; border-top: 2.2px solid {RULE}; }}
.stamp {{ position: absolute; left: 0; top: 0; mix-blend-mode: multiply; }}
.ad {{ position: absolute; border: 2px solid {INK}; padding: 14px 18px; box-sizing: border-box; overflow: hidden;
       font-family: '{BODY}'; font-size: 33px; line-height: 46px; color: {INK}; text-align: justify; }}
.ad b {{ display: block; font-family: '{HEAD}'; font-weight: 800; font-size: 36px; text-align: center;
         margin-bottom: 6px; line-height: 50px; }}
"""


def page(w, h, body, px=4096):
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{css()}</style></head>
<body><div id="art" data-width="{px}" style="width:{w:.0f}px;height:{h:.0f}px">
{body}
</div></body></html>
"""


def col(x, y, w, h, inner, cls='col', style=''):
    return f'<div class="{cls}" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px;{style}">{inner}</div>'


def hl(text, cx, top, size, weight=700, w=1400):
    return (f'<div class="hl" style="left:{cx - w / 2:.0f}px;top:{top:.0f}px;width:{w:.0f}px;'
            f'font-size:{size}px;font-weight:{weight}">{text}</div>')


def vr(x, y0, y1):
    return f'<div class="vr" style="left:{x:.1f}px;top:{y0:.0f}px;height:{y1 - y0:.0f}px"></div>'


def hr(x0, x1, y, weight=2.2):
    return f'<div class="hr" style="left:{x0:.0f}px;top:{y:.1f}px;width:{x1 - x0:.0f}px;border-top-width:{weight}px"></div>'


def grain(w, h, seed=4):
    """A faint mottle in the newsprint, like recycled fibre."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">'
        f'<filter id="mottle{seed}" x="0" y="0" width="100%" height="100%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" seed="{seed}"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.35  0 0 0 0 0.33  0.16 0 0 0 -0.06"/>'
        '</filter>'
        f'<rect width="{w:.0f}" height="{h:.0f}" filter="url(#mottle{seed})"/></svg>'
    )


# ---------------------------------------------------------------- the stamp


def _brush(p0, p1, w0, w1):
    """A straight brush stroke from p0 to p1, tapering from w0 to w1, with
    round ends (so strokes meeting at a corner make a rounded corner)."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    nx, ny = -dy / n, dx / n
    a, b = w0 / 2, w1 / 2
    return (
        f'<path d="M{x0 + nx * a:.1f},{y0 + ny * a:.1f} L{x1 + nx * b:.1f},{y1 + ny * b:.1f} '
        f'L{x1 - nx * b:.1f},{y1 - ny * b:.1f} L{x0 - nx * a:.1f},{y0 - ny * a:.1f} Z"/>'
        f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="{a:.1f}"/><circle cx="{x1:.1f}" cy="{y1:.1f}" r="{b:.1f}"/>'
    )


def _along(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def stamp_svg(w, h, cx, cy, rot):
    """The 'Chandni Chowk to the Sky' rubber stamp: a hand-cut frame (brush
    edges, a couple of breaks where the rubber did not print), the dotted
    IndiGo plane and the name in IndiGo's rounded lettering, all in one blue
    ink with a slightly ragged edge and a few dry specks."""
    TL, TR, BR, BL = (-418, -528), (414, -548), (424, 536), (-410, 548)
    s = []
    s.append(_brush(TL, _along(TL, TR, 0.47), 36, 31))
    s.append(_brush(_along(TL, TR, 0.45), TR, 33, 29))
    s.append(_brush(TR, _along(TR, BR, 0.62), 29, 27))
    s.append(_brush(_along(TR, BR, 0.60), _along(TR, BR, 0.87), 27, 24))
    s.append(_brush(_along(TR, BR, 0.905), _along(TR, BR, 0.975), 22, 21))
    s.append(_brush(TL, _along(TL, BL, 0.30), 31, 26))
    s.append(_brush(_along(TL, BL, 0.325), BL, 23, 29))
    s.append(_brush(BL, _along(BL, BR, 0.52), 29, 27))
    s.append(_brush(_along(BL, BR, 0.50), _along(BL, BR, 0.705), 27, 24))
    s.append(_brush(_along(BL, BR, 0.74), _along(BL, BR, 0.80), 23, 23))
    for t in (0.845, 0.885):
        s.append(_brush(_along(BL, BR, t), _along(BL, BR, t + 0.016), 25, 25))
    frame = ''.join(s)
    words = (
        f'<text x="0" y="379" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="90">Chandni Chowk</text>'
        f'<text x="6" y="473" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="90" letter-spacing="5">to the Sky</text>'
    )
    plane = plane_svg(-8, -132, 462, color=STAMP, dot=0.36)
    return (
        f'<svg class="stamp" xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">'
        '<filter id="ink" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.07" numOctaves="4" seed="11" result="rough"/>'
        '<feDisplacementMap in="SourceGraphic" in2="rough" scale="10" xChannelSelector="R" yChannelSelector="G" result="edge"/>'
        '<feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="3" seed="5" result="speck"/>'
        '<feColorMatrix in="speck" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  8 0 0 0 -2.05" result="mask"/>'
        '<feComposite in="edge" in2="mask" operator="in"/>'
        '</filter>'
        '<filter id="edge" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.07" numOctaves="4" seed="11" result="rough"/>'
        '<feDisplacementMap in="SourceGraphic" in2="rough" scale="7" xChannelSelector="R" yChannelSelector="G"/>'
        '</filter>'
        f'<g filter="url(#ink)"><g transform="translate({cx:.1f},{cy:.1f}) rotate({rot})" fill="{STAMP}">{frame}</g></g>'
        f'<g filter="url(#edge)"><g transform="translate({cx:.1f},{cy:.1f}) rotate({rot})" fill="{STAMP}">{plane}{words}</g></g></svg>'
    )


# ---------------------------------------------------------------- front


def front():
    b = []
    b.append(grain(W, L, 4))
    # Column grid (cm): A (cut off on the left) | B | C | D (cut off on the right).
    A0, A1 = -4.0, 1.25
    B0, B1 = 1.65, 6.9
    C0, C1 = 7.3, 12.55
    D0, D1 = 12.95, 18.2
    top, fold = dims.F + 0.16, 13.55  # first line just under the flap's edge; the page's fold rule
    lead = dims.F + 1.2  # the op-ed's first line
    cm = lambda v: v * U  # noqa: E731

    # Lead op-ed across B and C, headline first.
    b.append(hl(HEADLINE, cm((B0 + C1) / 2), cm(dims.F + 0.36), 58, 700))
    by = f'<div class="by">{BYLINE[0]}<span>{BYLINE[1]}</span></div>'
    # The debate box on the left reaches into column B: B's lines wrap round it.
    box_top, box_h = 5.85, 1.62
    wrap = (f'<div style="float:left;width:0;height:{cm(box_top - lead):.0f}px"></div>'
            f'<div style="float:left;clear:left;width:{cm(2.85 - B0):.0f}px;height:{cm(box_h):.0f}px"></div>')
    op = wrap + by + ''.join(f'<p class="{"first" if i == 0 else ""}">{p}</p>' for i, p in enumerate(OPED))
    b.append(col(cm(B0), cm(lead), cm(C1 - B0), cm(fold - 0.2 - lead), op, cls='col multi'))

    # Column A: news, the debate box, more news.
    b.append(col(cm(A0), cm(top), cm(A1 - A0), cm(box_top - 0.12 - top), paras(CITY)))
    b.append(hl(DEBATE[0], cm(1.22), cm(box_top + 0.22), 46, 800, w=400))
    b.append(hr(cm(-0.6), cm(2.7), cm(box_top + 0.95), 1.6))
    b.append(hl(DEBATE[1], cm(1.22), cm(box_top + 1.1), 33, 700, w=400))
    b.append(col(cm(A0), cm(box_top + box_h + 0.08), cm(A1 - A0), cm(fold - 0.2 - box_top - box_h - 0.08), paras(WATER)))

    # Column D: schools, then a small weather piece under a rule.
    b.append(col(cm(D0), cm(top), cm(D1 - D0), cm(4.72 - top), paras(SCHOOLS)))
    b.append(hr(cm(D0), cm(D1), cm(4.85), 1.6))
    b.append(hl(WEATHER_HEAD, cm((D0 + D1) / 2), cm(4.98), 40, 800, w=600))
    b.append(col(cm(D0), cm(5.66), cm(D1 - D0), cm(fold - 0.2 - 5.66), paras(WEATHER)))

    # Column rules.
    b.append(vr(cm((A1 + B0) / 2), cm(top), cm(box_top - 0.1)))
    b.append(vr(cm((A1 + B0) / 2), cm(box_top + box_h + 0.1), cm(fold - 0.15)))
    b.append(vr(cm((C1 + D0) / 2), cm(top), cm(fold - 0.15)))

    # The fold rule and the bottom stories: a new grid.
    b.append(hr(-10, W + 10, cm(fold), 2.4))
    E0, E1 = -2.2, 3.05
    F0, F1 = 3.45, 9.4
    G0, G1 = 9.8, 15.1
    low = fold + 0.25
    b.append(col(cm(E0), cm(low), cm(E1 - E0), cm(L / U - low + 1), paras(SAFETY)))
    b.append(vr(cm((E1 + F0) / 2), cm(low), L + 10))
    b.append(hl(FOCUS[0], cm((F0 + F1) / 2), cm(16.2), 42, 800, w=700))
    b.append(col(cm(F0), cm(16.9), cm(F1 - F0), cm(L / U - 16.9 + 1), paras(FOCUS[1]).replace('<p>', '<p class="first">', 1)))
    b.append(vr(cm((F1 + G0) / 2), cm(16.2), L + 10))
    b.append(hl(PAIN[0], cm((G0 + G1) / 2), cm(16.2), 42, 800, w=600))
    b.append(col(cm(G0), cm(16.9), cm(G1 - G0), cm(L / U - 16.9 + 1), paras(PAIN[1]).replace('<p>', '<p class="first">', 1)))
    # A last scrap of column on the far right, above 'पीर पराई'.
    b.append(col(cm(12.95), cm(low), cm(5.2), cm(15.95 - low), paras(WEATHER[::-1])))

    # The stamp, printed over everything.
    b.append(stamp_svg(W, L, 711, 1129, -4.2))
    return page(W, L, '\n'.join(b), px=4096)


# ---------------------------------------------------------------- flap


def flap():
    """The flap seen from above: fold at the top, free edge at the bottom."""
    h = (dims.F + dims.FOLD_ARC) * U
    base = h - 0.36 * U  # baseline of the running header
    body = (
        f'<rect width="{W:.0f}" height="{h:.0f}" fill="{PAPER}"/>'
        f'<text x="40" y="{base:.1f}" font-family="{HEAD}" font-weight="800" font-size="34" fill="{INK}">{HEADER[0]}</text>'
        f'<rect x="92" y="{base - 30:.1f}" width="2" height="36" fill="{INK}"/>'
        f'<text x="112" y="{base:.1f}" font-family="{HEAD}" font-weight="700" font-size="30" fill="{INK}">{HEADER[1]}</text>'
        f'<text x="{W - 40:.0f}" y="{base:.1f}" text-anchor="end" font-family="{HEAD}" font-weight="500" font-size="27" fill="{INK}">{HEADER[2]}</text>'
        f'<rect x="-10" y="{base + 12:.1f}" width="{W + 20:.0f}" height="4" fill="{INK}"/>'
        f'<rect x="-10" y="{base + 20:.1f}" width="{W + 20:.0f}" height="1.4" fill="{INK}"/>'
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {h:.0f}" data-width="4096">{body}</svg>'


# ---------------------------------------------------------------- back


def halftone(x0, y0, w, h, pitch=9.0, seed=3):
    """A small newspaper photo as a halftone screen: evening sky, the domes and
    minarets of the old city in silhouette, a busy street below."""
    rnd = random.Random(seed)
    blobs = [(rnd.uniform(0, w), rnd.uniform(h * 0.72, h), rnd.uniform(18, 60), rnd.uniform(0.1, 0.35)) for _ in range(90)]

    def tone(x, y):  # 0 = white, 1 = black; x, y from the photo's top-left
        u, v = x / w, y / h
        t = 0.12 + 0.2 * v  # sky
        # Main dome on its drum, two smaller domes, two minarets.
        def dome(cx, base, r, hgt):
            dy = (base - y) / hgt
            return abs(x - cx) < r * math.sqrt(max(0.0, 1 - dy * dy)) * (1 + 0.25 * dy) and base - hgt < y <= base
        sil = (
            dome(w * 0.5, h * 0.44, w * 0.13, h * 0.2) or dome(w * 0.3, h * 0.5, w * 0.075, h * 0.12)
            or dome(w * 0.7, h * 0.5, w * 0.075, h * 0.12)
            or (abs(x - w * 0.5) < w * 0.012 and h * 0.2 < y < h * 0.25)
            or (y > h * 0.44 and abs(x - w * 0.5) < w * 0.24)
            or (y > h * 0.5 and abs(x - w * 0.5) < w * 0.36)
            or (abs(x - w * 0.1) < w * 0.022 and y > h * 0.14) or (abs(x - w * 0.9) < w * 0.022 and y > h * 0.14)
            or (abs(x - w * 0.1) < w * 0.032 and h * 0.3 < y < h * 0.33) or (abs(x - w * 0.9) < w * 0.032 and h * 0.3 < y < h * 0.33)
        )
        if sil:
            t = 0.72
            # Arched gateway, lit from inside.
            if abs(x - w * 0.5) < w * 0.06 and y > h * 0.52 and ((y - h * 0.52) > -(abs(x - w * 0.5) / (w * 0.06)) ** 2 * h * 0.03):
                t = 0.42
        if y > h * 0.66:  # the street: people, stalls
            t = 0.52 + 0.1 * math.sin(x * 0.05) * math.sin(y * 0.09)
            for bx, by, br, bt in blobs:
                if (x - bx) ** 2 + (y - by) ** 2 < br * br:
                    t += bt
        return max(0.0, min(0.95, t + 0.04 * math.sin(u * 40 + v * 23)))

    dots = []
    c, s = math.cos(math.radians(45)), math.sin(math.radians(45))
    span = int((w + h) / pitch) + 2
    for i in range(-span, span):
        for j in range(-span, span):
            gx, gy = i * pitch, j * pitch
            x, y = gx * c - gy * s + w / 2, gx * s + gy * c + h / 2
            if not (0 <= x <= w and 0 <= y <= h):
                continue
            r = pitch * 0.56 * math.sqrt(tone(x, y))
            if r > 0.4:
                dots.append(f'<circle cx="{x0 + x:.1f}" cy="{y0 + y:.1f}" r="{r:.2f}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{L:.0f}" viewBox="0 0 {W:.0f} {L:.0f}">'
        f'<clipPath id="ph"><rect x="{x0}" y="{y0}" width="{w}" height="{h}"/></clipPath>'
        f'<g clip-path="url(#ph)" fill="{INK}">{"".join(dots)}</g>'
        f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="{INK}" stroke-width="2"/></svg>'
    )


def back():
    """The back panel as seen from behind, upright (top = the fold)."""
    cm = lambda v: v * U  # noqa: E731
    b = [grain(W, L, 9)]
    b.append(hl(FOOD_HEAD, W / 2, cm(0.75), 60, 800, w=1500))
    b.append(hr(cm(0.7), cm(12.8), cm(1.75), 1.6))
    b.append(halftone(cm(0.7), cm(2.05), cm(7.0), cm(5.2)))
    b.append(col(cm(0.7), cm(7.38), cm(7.0), cm(0.6), CAPTION, style='font-size:30px;line-height:44px;text-align:left'))
    b.append(vr(cm(7.95), cm(2.05), cm(13.3)))
    b.append(hl(METRO[0], cm(10.5), cm(2.1), 40, 800, w=600))
    b.append(col(cm(8.2), cm(2.85), cm(4.6), cm(10.45), paras(METRO[1]).replace('<p>', '<p class="first">', 1)))
    b.append(col(cm(0.7), cm(8.2), cm(7.0), cm(5.1), paras(FOOD).replace('<p>', '<p class="first">', 1), cls='col multi'))
    b.append(hr(-10, W + 10, cm(13.55), 2.4))
    b.append(hl('वर्गीकृत', W / 2, cm(13.8), 40, 800, w=600))
    for k, (head, text) in enumerate(ADS):
        x = cm(0.7 + k * 4.1)
        b.append(f'<div class="ad" style="left:{x:.0f}px;top:{cm(14.55):.0f}px;width:{cm(3.9):.0f}px;height:{cm(3.9):.0f}px">'
                 f'<b>{head}</b>{text}</div>')
    return page(W, L, '\n'.join(b), px=4096)


open(os.path.join(ART, 'front.html'), 'w').write(front())
open(os.path.join(ART, 'flap.svg'), 'w').write(flap())
open(os.path.join(ART, 'back.html'), 'w').write(back())
print('art written')
