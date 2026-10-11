"""Bulk annotator: MeCab (fugashi+unidic-lite) tokens, JmdictFurigana furigana, jamdict glosses.

Usage: python3 annotate.py FILE.md... [--out-dir DIR] [--trans-dir DIR] [--furigana-file PATH]
"""
import argparse
import html
import os
import re
import sys
from urllib.parse import quote

DEFAULT_FURIGANA = os.environ.get(
    'JMDICT_FURIGANA', os.path.expanduser('~/.local/share/nvim/JmdictFurigana.txt'))

TYPES = {
    'n': ('noun', 'Noun'),
    'v': ('verb', 'Verb'),
    'ai': ('adjective', 'い-adjective'),
    'an': ('adjective', 'な-adjective'),
    'pn': ('adnominal', 'Adnominal'),
    'av': ('adverb', 'Adverb'),
    'p': ('particle', 'Particle'),
    'x': ('auxiliary', 'Auxiliary'),
    'pr': ('pronoun', 'Pronoun'),
    'c': ('conjunction', 'Conjunction'),
    'ct': ('counter', 'Counter / Number'),
    'i': ('interjection', 'Interjection'),
    'af': ('affix', 'Affix'),
}
POSKEY = {
    'n': ['noun'], 'v': ['verb'], 'ai': ['adjective (keiyoushi)'], 'an': ['adjectival nouns', 'noun'],
    'pn': ['pre-noun'], 'av': ['adverb'], 'c': ['conjunction'], 'i': ['interjection'],
    'pr': ['pronoun'], 'af': ['suffix', 'prefix', 'counter'],
}

KANJI = r'\u4e00-\u9fff々〆ヶ'

ABS_AUX = {'ます', 'た', 'ない', 'ぬ', 'れる', 'られる', 'せる', 'させる', 'たい', 'う', 'よう'}
AUXLABEL = {
    'ます': 'polite', 'た': 'past', 'ない': 'negative', 'ぬ': 'negative',
    'れる': 'passive/potential', 'られる': 'passive/potential', 'せる': 'causative',
    'させる': 'causative', 'たい': 'want to', 'う': 'volitional', 'よう': 'volitional',
}
FORMLABEL = {'連用形': 'continuative', '未然形': 'irrealis', '命令形': 'imperative', '仮定形': 'conditional'}
DEMO = {'この', 'あの', 'その', 'どの', 'ここ'}

PGLOSS = {
    'は': 'topic marker', 'が': 'subject marker', 'を': 'object marker',
    'に': 'direction / time / target marker', 'で': 'location / means marker',
    'と': 'and / with / quotative', 'の': 'possessive / attributive marker', 'も': 'also',
    'か': 'question / or', 'や': 'and (non-exhaustive)', 'から': 'from / because',
    'まで': 'until / up to', 'へ': 'direction marker', 'より': 'than / from', 'など': 'such as',
    'だけ': 'only', 'ば': 'conditional', 'て': 'te-form connective', 'し': 'and (listing reasons)',
    'ね': 'sentence-final (agreement)', 'よ': 'sentence-final (emphasis)', 'ので': 'because',
    'のに': 'even though', 'けど': 'but', 'けれど': 'but', 'ながら': 'while',
    'たり': 'doing things like', 'ばかり': 'only / just', 'さえ': 'even', 'ほど': 'extent',
    'くらい': 'about / approximately', 'ぐらい': 'about / approximately', 'こそ': 'emphasis',
    'でも': 'even / or something', 'ても': 'even if', 'って': 'quotative (casual)',
    'とか': 'things like', 'なり': 'or', 'ほか': 'other', 'のみ': 'only', 'ずつ': 'each / at a time',
    'しか': 'only (with negative)', 'なら': 'if / as for',
}
# Connective で (te-form after voiced verbs) is a 接続助詞, unlike the case particle で.
PGLOSS_CONJ = {'で': 'te-form connective'}
PPOS = {
    '格助詞': 'case particle', '係助詞': 'binding particle', '接続助詞': 'conjunctive particle',
    '終助詞': 'sentence-final particle', '副助詞': 'adverbial particle',
    '準体助詞': 'nominalising particle', '助詞': 'particle',
}
XGLOSS = {
    'です': 'is (polite copula)', 'だ': 'is (copula)', 'ます': 'polite verb ending', 'た': 'past tense',
    'ない': 'negative', 'ぬ': 'negative (classical)', 'れる': 'passive / potential',
    'られる': 'passive / potential', 'せる': 'causative', 'させる': 'causative', 'たい': 'want to',
    'う': 'volitional', 'よう': 'seems / like', 'そうだ': 'seems / hearsay', 'らしい': 'seems / typical of',
    'ようだ': 'seems / like', 'まい': 'will not', 'べし': 'should', 'ず': 'negative (continuative)',
    'ごとし': 'like', 'みたい': 'like / seems',
}
PARTICLE_ROMA = {'は': 'は (wa)', 'を': 'を (o)', 'へ': 'へ (e)'}

tagger = None
jam = None
JF = {}
_gloss_cache = {}


def init(furigana_file):
    global tagger, jam
    import fugashi
    import unidic_lite
    from jamdict import Jamdict

    # A stub `unidic` package can shadow unidic-lite; point MeCab at unidic-lite explicitly.
    tagger = fugashi.GenericTagger('-r /dev/null -d ' + unidic_lite.DICDIR)
    jam = Jamdict()
    if os.path.exists(furigana_file):
        with open(furigana_file, encoding='utf-8-sig') as f:
            for ln in f:
                p = ln.rstrip('\n').split('|')
                if len(p) == 3:
                    JF[(p[0], p[1])] = p[2]
    else:
        print('warning: %s not found; using regex furigana alignment only' % furigana_file, file=sys.stderr)


def hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ン' else c for c in s)


def has_kanji(s):
    return re.search('[%s]' % KANJI, s) is not None


def esc(s):
    return html.escape(s, quote=True)


def furi(s, r):
    """Return a list of (text, reading or None) segments."""
    if not has_kanji(s) or not r or r == '*':
        return [(s, None)]
    r = hira(r)
    spec = JF.get((s, r))
    if spec:
        segs = {}
        for part in spec.split(';'):
            a, rd = part.split(':', 1)
            if '-' in a:
                x, y = map(int, a.split('-'))
            else:
                x = y = int(a)
            segs[x] = (y, rd)
        out = []
        i = 0
        while i < len(s):
            if i in segs:
                y, rd = segs[i]
                out.append((s[i:y + 1], rd))
                i = y + 1
            else:
                out.append((s[i], None))
                i += 1
        return out
    parts = re.findall('[%s]+|[^%s]+' % (KANJI, KANJI), s)
    pat = ''.join('(.+?)' if has_kanji(p) else re.escape(hira(p)) for p in parts)
    m = re.fullmatch(pat, r)
    if m:
        gs = list(m.groups())
        return [(p, gs.pop(0)) if has_kanji(p) else (p, None) for p in parts]
    return [(s, r)]


def ruby(segs):
    return ''.join(
        '<ruby>%s<rt>%s</rt></ruby>' % (esc(t), esc(rd)) if rd else esc(t) for t, rd in segs)


class Morph:
    def __init__(self, w):
        f = w.feature
        self.surf = w.surface
        self.pos1, self.pos2 = f[0], f[1]
        self.ctype, self.cform = f[4], f[5]
        lem = f[7] if len(f) > 7 else '*'
        if lem == '*' or not lem:
            lem = w.surface
        m = re.fullmatch(r'(.+?)-[A-Za-z].*', lem)
        self.lemma = m.group(1) if m else lem
        self.kana = f[17] if len(f) > 17 and f[17] != '*' else ''


def morphs(text):
    out = []
    for chunk in re.split(r'(\s+)', text):
        if not chunk:
            continue
        if chunk.isspace():
            out.append(('P', chunk))
            continue
        for w in tagger(chunk):
            m = Morph(w)
            if m.pos1 in ('補助記号', '記号', '空白'):
                out.append(('P', w.surface))
            else:
                out.append(('M', m))
    return out


def gloss(lemma, typ):
    key = (lemma, typ)
    if key in _gloss_cache:
        return _gloss_cache[key]
    res = ''
    try:
        ents = list(jam.lookup(lemma, lookup_chars=False).entries)

        def exact(e):
            return any(k.text == lemma for k in e.kanji_forms) or any(k.text == lemma for k in e.kana_forms)

        ents = [e for e in ents if exact(e)] or ents
        keys = POSKEY.get(typ, [])
        pick = None
        for e in ents:
            for s in e.senses:
                if any(any(k in p for k in keys) for p in s.pos):
                    pick = s
                    break
            if pick:
                break
        if not pick and ents and ents[0].senses:
            pick = ents[0].senses[0]
        if pick:
            res = '; '.join(str(g) for g in pick.gloss[:3])
    except Exception:
        res = ''
    _gloss_cache[key] = res
    return res


def classify(m):
    p1, p2 = m.pos1, m.pos2
    if p1 == '名詞':
        if p2 in ('数詞', '助数詞'):
            return 'ct'
        if p2 == '代名詞':
            return 'pr'
        return 'n'
    if p1 == '連体詞':
        return 'pr' if m.surf in DEMO else 'pn'
    if p1 in ('接頭辞', '接尾辞'):
        return 'ct' if p2 == '助数詞' else 'af'
    return {
        '動詞': 'v', '形容詞': 'ai', '形状詞': 'an', '副詞': 'av', '助詞': 'p', '助動詞': 'x',
        '接続詞': 'c', '感動詞': 'i', '代名詞': 'pr',
    }.get(p1, 'n')


def tokens(text):
    seq = morphs(text)
    toks = []
    i = 0

    def nxt():
        return seq[i][1] if i < len(seq) and seq[i][0] == 'M' else None

    while i < len(seq):
        kind, m = seq[i]
        if kind == 'P':
            toks.append({'punct': m})
            i += 1
            continue
        t = classify(m)
        group = [m]
        i += 1
        if m.pos1 in ('動詞', '形容詞'):
            while True:
                n = nxt()
                if n is None:
                    break
                is_aux = n.pos1 == '助動詞' and n.lemma in ABS_AUX
                is_te = n.pos1 == '助詞' and n.surf in ('て', 'で') and n.pos2 == '接続助詞'
                if not (is_aux or is_te):
                    break
                group.append(n)
                i += 1
        elif m.pos1 == '形状詞':
            n = nxt()
            if n is not None and n.pos1 == '助動詞' and n.lemma == 'だ' and n.surf in ('な', 'に'):
                group.append(n)
                i += 1
        elif t == 'ct':
            while True:
                n = nxt()
                if n is None or classify(n) != 'ct':
                    break
                group.append(n)
                i += 1
        toks.append({'ms': group, 'typ': t})
    return toks


def build_token(tk):
    ms = tk['ms']
    t = tk['typ']
    head = ms[0]
    surf = ''.join(m.surf for m in ms)
    segs = []
    for m in ms:
        segs += furi(m.surf, m.kana)
    reading = ''.join(rd if rd else tt for tt, rd in segs) if has_kanji(surf) else surf
    reading = hira(reading)
    lemma = surf if t == 'ct' else head.lemma

    if t == 'p':
        if head.pos2 == '接続助詞' and surf in PGLOSS_CONJ:
            g = PGLOSS_CONJ[surf]
        else:
            g = PGLOSS.get(surf) or PPOS.get(head.pos2, 'particle')
    elif t == 'x':
        g = XGLOSS.get(lemma) or XGLOSS.get(surf) or 'auxiliary'
        if lemma == 'だ' and surf in ('だ', 'で', 'な', 'に', 'だっ', 'じゃ'):
            g = 'copula (is / be)'
    elif t == 'ct':
        g = 'number / counter'
    elif re.fullmatch(r'[A-Za-z0-9 ./&-]+', surf):
        g = 'Latin-script term'
    else:
        g = gloss(lemma, t)
        if not g and surf != lemma:
            g = gloss(surf, t)
        if t in ('v', 'ai', 'an') and g:
            labels = []
            for m in ms[1:]:
                lb = 'te-form' if m.pos1 == '助詞' else AUXLABEL.get(m.lemma)
                if lb and lb not in labels:
                    labels.append(lb)
            if not labels and head.cform in FORMLABEL:
                labels = [FORMLABEL[head.cform]]
            if labels:
                g += ' (' + ', '.join(labels) + ')'
    if t == 'p':
        reading = PARTICLE_ROMA.get(reading, reading)
    return {'surf': surf, 'segs': segs, 'reading': reading, 'lemma': lemma, 'typ': t, 'gloss': g}


def split_sentences(para):
    sents = []
    cur = ''
    depth = 0
    i = 0
    while i < len(para):
        c = para[i]
        cur += c
        if c in '「『（(':
            depth += 1
        elif c in '」』）)':
            depth = max(0, depth - 1)
        if c in '。！？!?' and depth == 0:
            while i + 1 < len(para) and para[i + 1] in '」』）)':
                i += 1
                cur += para[i]
            sents.append(cur.strip())
            cur = ''
        i += 1
    if cur.strip():
        sents.append(cur.strip())
    return [s for s in sents if s]


def load_sentences(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    paras = []
    for blk in re.split(r'\n\s*\n', text):
        lines = [ln for ln in blk.split('\n') if ln.strip() and not ln.startswith('#')]
        if lines:
            paras.append(split_sentences(''.join(lines)))
    return paras


def load_translations(path):
    trans = {}
    if not os.path.exists(path):
        return trans
    with open(path, encoding='utf-8') as f:
        for lineno, ln in enumerate(f, 1):
            if '\t' not in ln:
                continue
            a, b = ln.rstrip('\n').split('\t', 1)
            try:
                trans[int(a.strip())] = b
            except ValueError:
                print('warning: %s:%d: bad sentence number %r, skipped' % (path, lineno, a), file=sys.stderr)
    return trans


def render_sentence(n, s, translation):
    full = []
    rows = []
    for tk in tokens(s):
        if 'punct' in tk:
            full.append(esc(tk['punct']))
            continue
        b = build_token(tk)
        cls, name = TYPES[b['typ']]
        rb = ruby(b['segs'])
        if b['typ'] in ('p', 'ct') or re.fullmatch(r'[A-Za-z0-9 ./&-]+', b['surf']):
            full.append('<span class="%s">%s</span>' % (cls, rb))
        else:
            full.append('<span class="%s"><a href="https://jisho.org/word/%s" target="_blank" rel="noopener">%s</a></span>'
                        % (cls, quote(b['lemma']), rb))
        unc = ' class="uncertain"' if not b['gloss'] and b['typ'] in ('n', 'v', 'ai', 'an', 'av') else ''
        rows.append(
            '<tr><td class="word %s">%s</td><td>%s</td><td>%s</td><td%s><span class="badge %s">%s</span></td><td>%s</td></tr>'
            % (cls, rb, esc(b['reading']), esc(b['lemma']), unc, cls, name, esc(b['gloss'] or '—')))
    return (
        '<section class="sentence">\n<h2>Sentence %d</h2>\n<div class="full">%s</div>\n<table>\n'
        '<thead><tr><th>Word</th><th>Reading</th><th>Dictionary form</th><th>Type</th><th>English</th></tr></thead>\n'
        '<tbody>\n%s\n</tbody>\n</table>\n<p class="translation">%s</p>\n</section>'
        % (n, ''.join(full), '\n'.join(rows), esc(translation)))


def main():
    ap = argparse.ArgumentParser(description='Bulk-annotate Japanese text files into HTML.')
    ap.add_argument('files', nargs='+')
    ap.add_argument('--out-dir', help='output directory (default: next to each input file)')
    ap.add_argument('--trans-dir', default='.annotate',
                    help='working dir: writes sent/<name>.txt, reads trans/<name>.txt '
                         '(lines "N<TAB>English") (default: .annotate)')
    ap.add_argument('--furigana-file', default=DEFAULT_FURIGANA,
                    help='JmdictFurigana.txt path (default: $JMDICT_FURIGANA or %(default)s)')
    args = ap.parse_args()

    init(args.furigana_file)
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'template.html')
    with open(tpl_path, encoding='utf-8') as f:
        tpl = f.read()
    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(os.path.join(args.trans_dir, 'sent'), exist_ok=True)

    for path in args.files:
        base = os.path.splitext(os.path.basename(path))[0]
        trans = load_translations(os.path.join(args.trans_dir, 'trans', base + '.txt'))
        out = []
        sent_lines = []
        n = 0
        for pi, para in enumerate(load_sentences(path), 1):
            out.append('<h2 class="section">Paragraph %d</h2>' % pi)
            for s in para:
                n += 1
                sent_lines.append('%d\t%s\n' % (n, s))
                out.append(render_sentence(n, s, trans.get(n, '(translation pending)')))
        with open(os.path.join(args.trans_dir, 'sent', base + '.txt'), 'w', encoding='utf-8') as f:
            f.writelines(sent_lines)
        out_path = os.path.join(args.out_dir or os.path.dirname(os.path.abspath(path)), base + '.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(tpl.replace('{{TITLE}}', esc(base)).replace('<!-- SENTENCES -->', '\n'.join(out)))
        print('%s: %d sentences, %d translations -> %s' % (base, n, len(trans), out_path))


if __name__ == '__main__':
    main()
