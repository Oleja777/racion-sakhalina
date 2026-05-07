"""One-shot script to inject kcal/protein/fat/carbsNum/fiber/sugar/sodium fields
into each product entry in index.html.

Values per 100 g (or per unit if gramsPerUnit is set), sourced from USDA FoodData
Central / Skurikhin tables for common foods, with rough estimates for endemics
(klopovka, dudnik, sea grape, etc.). Estimates flagged in comments where uncertain.

Run: python _inject_macros.py
"""
import re, sys, os

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, 'index.html')

# (kcal, protein, fat, carbsNum, fiber, sugar, sodium) per 100 g
NUTRIENTS = {
    # ── greens ──
    'nettle':    (42,  2.7, 0.5,  7.5,  6.9, 0.3,   4),
    'cheremsha': (35,  2.5, 0.5,  6.5,  1.0, 1.0,   5),
    'fern':      (34,  4.6, 0.4,  5.5,  2.0, 0.5,   2),
    'burdock':   (72,  1.5, 0.2, 17.3,  3.3, 2.9,   5),
    'dand':      (45,  2.7, 0.7,  9.2,  3.5, 0.7,  76),
    'limonnik':  (45,  0.5, 0.4, 11.0,  1.6, 6.0,   5),
    # ── berries ──
    'klopovka':  (36,  0.6, 0.4,  7.5,  4.1, 4.0,   1),  # estimate (Sakhalin endemic)
    'rose':      (162, 1.6, 0.7, 22.4, 24.0, 2.0,   5),  # dried
    'seabuck':   (82,  1.2, 5.4,  5.7,  4.7, 5.0,   4),
    'brusnika':  (46,  0.7, 0.5,  8.2,  2.5, 5.7,   7),
    'morozka':   (51,  0.8, 0.9,  7.4,  6.3, 6.0,   1),
    # ── vegs ──
    'cucumber':  (14,  0.8, 0.1,  2.5,  1.0, 1.5,   8),
    'tomato':    (20,  1.1, 0.2,  3.7,  1.4, 2.6,   5),
    'pumpkinveg':(22,  1.0, 0.1,  4.4,  2.0, 2.8,   4),
    'horseradish':(56, 4.5, 0.4, 10.5,  7.3, 3.0,  14),
    # ── sea ──
    'kelp':      (235,12.0, 1.5, 47.0, 35.0, 1.0, 800),  # dried (per 100 g dry)
    'grape':     (4,   1.2, 0.5,  1.4,  1.2, 0.5, 700),  # umibudo, very low cal
    'trepang':   (68, 16.4, 0.4,  0.4,  0.0, 0.0, 380),
    'urchin':    (175,16.0, 4.5,  1.5,  0.0, 1.0, 200),
    'shrimp':    (99, 24.0, 0.3,  0.0,  0.0, 0.0, 111),
    'crab':      (85, 18.0, 1.0,  0.5,  0.0, 0.0, 320),
    'squid':     (92, 18.0, 1.4,  3.1,  0.0, 0.0,  44),
    'octopus':   (82, 14.9, 1.0,  2.2,  0.0, 0.0, 230),
    'scallop':   (88, 16.8, 0.8,  2.4,  0.0, 0.0, 161),
    'oyster':    (81,  9.5, 2.3,  4.9,  0.0, 0.5, 106),
    'whelk':     (137,23.8, 0.4,  7.8,  0.0, 0.0, 206),
    'redcaviar': (252,30.0,14.0,  1.5,  0.0, 1.0,1500),
    'pollcockcaviar':(130,28.0,2.0,1.0, 0.0, 0.0,1500),
    # ── meat ──
    'pollock':   (72, 16.0, 0.9,  0.0,  0.0, 0.0, 100),
    'salmon':    (208,20.0,13.0,  0.0,  0.0, 0.0,  60),
    'beef':      (250,26.0,17.0,  0.0,  0.0, 0.0,  60),
    'chicken':   (165,31.0, 3.6,  0.0,  0.0, 0.0,  74),
    'egg':       (155,13.0,11.0,  1.1,  0.0, 1.1, 124),
    # ── grain / seeds ──
    'buckwheat': (343,13.0, 3.4, 71.0, 10.0, 0.0,   1),
    'millet':    (378,11.0, 4.2, 73.0,  8.5, 0.0,   5),
    'rice':      (365, 7.1, 0.7, 80.0,  1.3, 0.0,   5),
    'lentil':    (353,25.0, 1.1, 60.0, 11.0, 2.0,   6),
    'hemp':      (553,31.6,49.0,  8.7,  4.0, 1.5,   5),
    'pumpkin':   (559,30.0,49.0, 11.0,  6.0, 1.4,   7),
    'sesame':    (573,17.7,49.7, 23.0, 11.8, 0.3,  11),
    # ── fungi ──
    'boletus':   (34,  3.7, 1.7,  1.1,  2.3, 0.4,   5),
    'chanterelle':(38, 1.5, 0.5,  6.8,  3.8, 1.2,   9),
    'redcap':    (22,  3.3, 0.5,  1.2,  2.0, 1.0,   4),
    'birchbolt': (20,  2.3, 0.9,  1.2,  5.1, 1.0,   4),
    'butter':    (19,  2.4, 0.7,  0.5,  1.2, 1.0,   5),
    'russula':   (19,  1.7, 0.7,  1.5,  5.5, 1.0,   3),
    'ryzhik':    (22,  1.9, 0.8,  0.5,  2.2, 1.0,   5),
    'gruzd':     (16,  1.8, 0.8,  0.5,  1.8, 1.0,   5),
    'openyok':   (22,  2.2, 1.2,  0.5,  5.1, 1.0,   5),
    'champignon':(27,  4.3, 1.0,  0.1,  2.6, 1.7,   6),
    'volnushka': (22,  2.5, 0.7,  1.7,  2.0, 1.0,   5),
    'oyster_f':  (33,  3.3, 0.4,  6.1,  2.3, 1.1,  18),
    # ── suppl: oils (high-cal) ──
    'fishoil':   (902, 0.0,100.0, 0.0,  0.0, 0.0,   0),
    'sealoil':   (902, 0.0,100.0, 0.0,  0.0, 0.0,   0),
    'blackcumin':(898, 0.5,99.5,  0.0,  0.0, 0.0,   0),
    'hempoil':   (884, 0.0,100.0, 0.0,  0.0, 0.0,   0),
    'pumpkinoil':(884, 0.0,100.0, 0.0,  0.0, 0.0,   0),
    'sesameoil': (884, 0.0,100.0, 0.0,  0.0, 0.0,   0),
}

# Tinctures / pills — exclude from macro tracking entirely (kcal:null)
NULL_KCAL = {'eleu', 'dudnik', 'vitd3sup', 'magnesium', 'b12sup'}

# Conversion if portion unit isn't grams. For these, gramsPerUnit specifies
# how many grams equal one unit (1 шт, 1 ст.л., 1 ч.л., etc.).
GRAMS_PER_UNIT = {
    'egg': 50,        # 1 куриное яйцо ≈ 50 г
    'oyster': 17,     # 1 устрица ≈ 17 г съедобной массы
    'horseradish': 5, # 1 ч.л. тёртого хрена ≈ 5 г
    'hemp': 10,       # 1 ст.л. семян конопли ≈ 10 г
    'sesame': 10,     # 1 ст.л. кунжута ≈ 10 г
    'blackcumin': 5,  # 1 ч.л. масла ≈ 5 г
    'hempoil': 15,    # 1 ст.л. масла ≈ 15 г
    'pumpkinoil': 15,
    'sesameoil': 15,
}


def fmt_num(x):
    """Format float with minimal trailing zeros."""
    if x == int(x):
        return str(int(x))
    return f"{x:g}"


def fields_for(k):
    if k in NULL_KCAL:
        return "kcal:null,protein:null,fat:null,carbsNum:null,fiber:null,sugar:null,sodium:null,"
    n = NUTRIENTS[k]
    parts = [
        f"kcal:{fmt_num(n[0])}",
        f"protein:{fmt_num(n[1])}",
        f"fat:{fmt_num(n[2])}",
        f"carbsNum:{fmt_num(n[3])}",
        f"fiber:{fmt_num(n[4])}",
        f"sugar:{fmt_num(n[5])}",
        f"sodium:{fmt_num(n[6])}",
    ]
    if k in GRAMS_PER_UNIT:
        parts.append(f"gramsPerUnit:{GRAMS_PER_UNIT[k]}")
    return ",".join(parts) + ","


with open(HTML, 'r', encoding='utf-8') as f:
    content = f.read()

# Each product line looks like:
#   {k:'NAME',g:'GROUP',...,nuts:{...},desc:'...',...}
# Insert new fields between nuts:{...}, and desc:
known_keys = set(NUTRIENTS.keys()) | NULL_KCAL
seen = set()
missed = []

def replace_one(m):
    full_match = m.group(0)
    k = m.group(1)
    if k in seen:
        return full_match  # don't touch second occurrence
    seen.add(k)
    if k not in known_keys:
        missed.append(k)
        return full_match
    return f"{m.group('head')},{fields_for(k)}desc:"

pattern = re.compile(
    r"(?P<head>\{k:'(?P<key>[a-z0-9_]+)',[^\n]*?nuts:\{[^}]+\})"
    r",desc:",
    re.DOTALL,
)
# The named group "key" overlaps with "head" but Python re doesn't allow naming
# both. Simplify with two groups:
pattern = re.compile(
    r"(\{k:'([a-z0-9_]+)',[^\n]*?nuts:\{[^}]+\}),desc:"
)

def _sub(m):
    k = m.group(2)
    if k in seen:
        return m.group(0)
    seen.add(k)
    if k not in known_keys:
        missed.append(k)
        return m.group(0)
    return f"{m.group(1)},{fields_for(k)}desc:"

new_content, count = pattern.subn(_sub, content)

if missed:
    print(f"NOT IN TABLE (skipped): {missed}")
print(f"Injected fields into {count} products")

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(new_content)
