r"""Embed the weapon data and assets into docs/index.html.

    python scripts/build.py [path\to\mh4u-collection-tracker] [path\to\mhgu-weapon-trees]

Both default to sibling folders of this repo. Nothing is read from the game here: every weapon, stat,
recipe and upgrade link comes from the MH4U Collection Tracker's generated docs/data/ (which reads the
game -- see that repo's scripts/build_data.py), along with its rarity icons, note icons, monster icons,
textures and font. The MHGU Weapon Trees page supplies only the coating bottles: the tracker names
4U's coatings but has no icons for them yet (4U's item table is not decoded).

Only the block between the DATA:BEGIN / DATA:END markers in docs/index.html is rewritten, so the
app's code stays hand-edited in place.

MH4U has no weapon levels, so the trees are built from the tracker's parent/children links: every
weapon is a node, and a "line" is a run of upgrades -- the first upgrade the game lists for a weapon
carries its line on, any others start lines of their own that branch off it. Lines only decide how
the tree is laid out (one straight lane per line); nothing in the game depends on them.
"""
import base64, io, json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(HERE)
TRACKER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PARENT, 'mh4u-collection-tracker')
GU_TREES = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PARENT, 'mhgu-weapon-trees')
TDOCS = os.path.join(TRACKER, 'docs')
INDEX = os.path.join(HERE, 'docs', 'index.html')

BEGIN = '<!-- DATA:BEGIN (written by scripts/build.py; do not edit by hand) -->'
END = '<!-- DATA:END -->'

# Theme names -> the icon file each one shows (the tracker's THEMES table; same 31 hexes family-wide).
THEME_ICONS = {
    'Black Gravios': 'Black Gravios', 'Rathalos': 'Rathalos', 'Cephadrome': 'Cephadrome',
    'Daimyo Hermitaur': 'Daimyo Hermitaur', 'Desert Seltas': 'Desert Seltas', 'G. Rathian': 'Gold Rathian',
    'Seltas': 'Seltas', 'Genprey': 'Genprey', 'Seltas Queen': 'Seltas Queen', 'Rathian': 'Rathian',
    'Basarios': 'Basarios', 'Blue Yian Kut-Ku': 'Blue Yian Kut-Ku', 'A. Rathalos': 'Azure Rathalos',
    'Tidal Najarala': 'Tidal Najarala', 'Velocidrome': 'Velocidrome', 'Gypceros': 'Gypceros',
    'Black Diablos': 'Black Diablos', 'Ash Kecha Wacha': 'Ash Kecha Wacha', 'Purple Gypceros': 'Purple Gypceros',
    'Great Jaggi': 'Great Jaggi', 'Plum D. Hermitaur': 'Plum Daimyo Hermitaur',
    'S. Nerscylla': 'Shrouded Nerscylla', 'P. Rathian': 'Pink Rathian', 'Yian Kut-Ku': 'Yian Kut-Ku',
    'Ruby Basarios': 'Ruby Basarios', 'D. Seltas Queen': 'Desert Seltas Queen', 'Kecha Wacha': 'Kecha Wacha',
    'Gravios': 'Gravios', 'S. Rathalos': 'Silver Rathalos', 'White Monoblos': 'White Monoblos',
    'Forbidden': 'Question Mark',
}
# 4U's coatings (Menu 543+) -> the MHGU app's bottle of the same colour. Paint has no MHGU bottle, so
# it stays text.
COATING_ICON = {'Power': 'Red', 'C.Range': 'White', 'Poison': 'Purple', 'Paralysis': 'Yellow',
                'Sleep': 'Light_Blue', 'Exhaust': 'Blue', 'Blast': 'Light_Green'}
GUNNER = {'light_bowgun', 'heavy_bowgun', 'bow'}


def data_uri(path, mime):
    with open(path, 'rb') as fh:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(fh.read()).decode())


def png_uri(img):
    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def load_catalog():
    s = open(os.path.join(TDOCS, 'data', 'catalog.js'), encoding='utf-8').read()
    return json.loads(s[s.index('=') + 1:].strip().rstrip(';'))


def gu_coats():
    """The MHGU Weapon Trees page's embedded coating bottles: {colour name: {c, i}}."""
    line = next(l for l in open(os.path.join(GU_TREES, 'docs', 'index.html'), encoding='utf-8')
                if l.startswith('<script>window.THEME_ASSETS='))
    for part in line.strip().split('</script><script>'):
        part = part.replace('<script>', '').replace('</script>', '')
        name, body = part.split('=', 1)
        if name == 'window.COATS':
            return json.loads(body.rstrip(';'))['col']
    raise SystemExit('no window.COATS in the MHGU Weapon Trees page')


class Strings:
    """Per-class string table, so repeated labels are stored once (the MHGU app's `str`)."""
    def __init__(self):
        self.list, self.ix = [], {}

    def __call__(self, s):
        if s not in self.ix:
            self.ix[s] = len(self.list)
            self.list.append(s)
        return self.ix[s]


AMMO_LV = re.compile(r'^(.*?)\s+Lv(\d+)$')


def extra(cls, st, S):
    """Class-specific payload (L[7]); the page's unpack() reads it back."""
    if cls in ('switch_axe', 'charge_blade'):
        return [S(re.sub(r'\s*Phial$', '', st['phial']))]
    if cls == 'insect_glaive':
        return [S(st['kinsect'])]
    if cls == 'hunting_horn':
        # notes [label, icon, colour]; songs [[note indexes into those three], effect].
        return [[S(n[0]) for n in st['notes']], [[seq, S(effect)] for seq, effect in st.get('songs', [])]]
    if cls == 'gunlance':
        return [S(st['shell'])]
    if cls == 'bow':
        # charges [name, loadUp]; coatings are the game's labels (no icon in the tracker's data).
        return [S(st['arc']) if st.get('arc') else -1,
                [[S(re.sub(r' L(\d)$', r' Lv\1', name)), load_up] for name, load_up in st['charges']],
                [S(c) for c in st['coatings']]]
    if cls in ('light_bowgun', 'heavy_bowgun'):
        groups, order = {}, []
        for name, cap in st['ammo']:          # in the game's item order: Normal S Lv1, Lv2, ...
            m = AMMO_LV.match(name)
            base, lv = (m.group(1), int(m.group(2))) if m else (name, 1)
            if base not in groups:
                groups[base] = {}
                order.append(base)
            groups[base][lv] = cap
        ammo = [[S(b), [groups[b].get(lv, 0) for lv in range(1, max(groups[b]) + 1)]] for b in order]
        # Rapid Fire (LBG): [ammo, shots, wait, damage per shot]; Crouching Fire (HBG): ammo names.
        rapid = [[S(a), shots, S(wait), dmg] for a, shots, wait, dmg in st.get('rapid', [])]
        crouch = [S(a) for a in st.get('crouch', [])]
        return [S(st['reload']), S(st['recoil']), S(st['deviation']), ammo, rapid, crouch]
    return []


def build_class(cls, cat):
    stats = json.load(open(os.path.join(TDOCS, 'data', 'stats', cls + '.json'), encoding='utf-8'))['byId']
    mats = json.load(open(os.path.join(TDOCS, 'data', 'materials', cls + '.json'), encoding='utf-8'))
    S = Strings()
    names = {e[0]: e[1] for e in cat['entries']}
    tree_order = {e[0]: e[4] for e in cat['entries']}
    # A weapon is laid out under the parent the tracker gives it. 4U has one weapon that two others
    # upgrade into (Dios Katana, from Wyvern Blade "Fall" and Tigrine Edge); the other link is kept
    # as `also` (L[13]) for the panels, and not drawn.
    kids = {i: [c for c in stats[str(i)]['children'] if c in names and stats[str(c)]['parent'] == i]
            for i in names}
    also = {}
    for i in names:
        for c in stats[str(i)]['children']:
            if c in names and stats[str(c)]['parent'] != i:
                also.setdefault(c, []).append(i)
    # The tracker gives what the game DISPLAYS and the true raw beside it: the record stores the true
    # value, and the status screen shows it times the class multiplier (u32[16] at 0xed24a0 / 100,
    # floored) -- element and status x10. The display inverts exactly: with a multiplier of at least 1
    # only one integer floors to a given display, the smallest one at or above display / multiplier.
    # That is checked here against the tracker's own true raw, and gives the true element.
    mult100 = round(cat['mult'] * 100)
    true_raw = lambda shown: -(-100 * shown // mult100)

    def level(i):
        st = stats[str(i)]
        rec = mats['create'].get(str(i), {})
        sharp = st.get('sh') if cls not in GUNNER else None
        raw = st.get('raw', true_raw(st['atk']))
        assert raw == true_raw(st['atk']), (cls, i, st['atk'], raw)
        ele = []
        for e in st.get('ele', []):
            t = e[3] if len(e) > 3 else e[1] // 10
            assert t * 10 == e[1], (cls, i, e)
            ele.append([e[0], e[1], e[2], t])
        return [i, names[i], st['atk'], st['aff'], st['def'], st['slots'], ele,
                extra(cls, st, S),
                rec['f'][2] if 'f' in rec else None,
                sharp, st['rar'],
                rec.get('d'),
                raw] + ([also[i]] if i in also else [])

    # Lines, depth first in the tracker's tree order so related lines sit together.
    trees = []

    def line_from(start, parent):
        t = {'i': len(trees) + 1, 'n': names[start], 'r': stats[str(start)]['rar'], 'p': parent or 0, 'L': []}
        trees.append(t)
        branches, i = [], start
        while True:
            t['L'].append(level(i))
            ks = kids[i]
            branches += [(i, k) for k in ks[1:]]
            if not ks:
                break
            i = ks[0]
        for at, k in branches:
            line_from(k, at)

    roots = sorted((i for i in names if stats[str(i)]['parent'] not in names), key=lambda i: tree_order[i])
    for r in roots:
        line_from(r, None)
    placed = sum(len(t['L']) for t in trees)
    assert placed == len(names), (cls, placed, len(names))
    return {'label': cat['label'], 'mats': mats['mats'], 'str': S.list, 'trees': trees}


def main():
    from PIL import Image
    cat = load_catalog()

    wdata = {cls: build_class(cls, c) for cls, c in cat['weapons'].items()}

    icons = {}
    for cls in cat['weapons']:
        icons[cls] = {}
        for r in range(1, 11):
            # The equipment box icons (24 px outlined game cells, doubled by the tracker), the style the
            # MH3U tree draws; doubled again so they hold their pixels at the size the map draws them
            # rather than being smoothed by the browser.
            img = Image.open(os.path.join(TDOCS, 'assets', 'icons', 'box_%s_r%d.png' % (cls, r))).convert('RGBA')
            icons[cls][r] = png_uri(img.resize((img.width * 2, img.height * 2), Image.NEAREST))

    monsters = {name: data_uri(os.path.join(TDOCS, 'assets', 'MonsterIcons',
                                            'MH4U-%s_Icon.png' % icon.replace(' ', '_')), 'image/png')
                for name, icon in THEME_ICONS.items()}

    theme = {
        'font': data_uri(os.path.join(TDOCS, 'fonts', 'mhfu_font.ttf'), 'font/ttf'),
        'rocky': data_uri(os.path.join(TDOCS, 'assets', 'rockyTextureDark2.png'), 'image/png'),
        'banner': data_uri(os.path.join(TDOCS, 'assets', 'banner-background.png'), 'image/png'),
        'title': data_uri(os.path.join(TDOCS, 'assets', 'titlebar-background.png'), 'image/png'),
    }

    gu = gu_coats()
    coats = {'map': COATING_ICON, 'col': {k: gu[k] for k in set(COATING_ICON.values())}}
    seen = {c for st in json.load(open(os.path.join(TDOCS, 'data', 'stats', 'bow.json'), encoding='utf-8'))['byId'].values()
            for c in st['coatings']}
    print('coatings without a bottle:', sorted(seen - set(COATING_ICON)))

    # Note label -> {i: the game's glyph, c: the HUD's colour for it} (the tracker reads both).
    notes = {}
    for st in json.load(open(os.path.join(TDOCS, 'data', 'stats', 'hunting_horn.json'), encoding='utf-8'))['byId'].values():
        for label, icon, col in st['notes']:
            notes[label] = {'c': col, 'i': data_uri(os.path.join(TDOCS, 'assets', 'notes', icon + '.png'), 'image/png')}

    blobs = [('THEME_ASSETS', theme), ('MONSTER_ICONS', monsters), ('ICONS', icons), ('COATS', coats),
             ('NOTE_ICONS', notes), ('RARITY', cat['rarityColors']),
             # The game's own colour per element / status where the tracker has one; the page keeps
             # its own palette for anything this leaves out (all of it, for 4U so far).
             ('ELE_COLOURS', cat['labels'].get('eleColours', {})), ('WDATA', wdata)]
    block = ''.join('<script>window.%s=%s;</script>' % (k, json.dumps(v, ensure_ascii=False, separators=(',', ':')))
                    for k, v in blobs)

    html = open(INDEX, encoding='utf-8').read()
    a, b = html.index(BEGIN) + len(BEGIN), html.index(END)
    html = html[:a] + '\n' + block + '\n' + html[b:]
    with open(INDEX, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(html)

    for cls, d in wdata.items():
        print('%-17s %4d weapons  %3d lines  %3d trees' % (
            cls, sum(len(t['L']) for t in d['trees']), len(d['trees']), sum(1 for t in d['trees'] if not t['p'])))
    print('index.html', os.path.getsize(INDEX), 'bytes')


if __name__ == '__main__':
    main()
