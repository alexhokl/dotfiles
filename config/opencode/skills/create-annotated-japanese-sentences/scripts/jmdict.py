"""Offline JMdict lookup (port of the nvim-jmdict plugin) and JmdictFurigana splits.

Usage: python3 jmdict.py [--dict-file PATH] [--limit N] WORD...
       python3 jmdict.py --furigana WORD READING [WORD READING ...]

Stdlib only. Reads a JMdict JSON file produced by `jmdict-to-json convert`
and caches a compact index, rebuilt when the dictionary is newer.
"""
import argparse
import json
import os
import re
import sys

DEFAULT_DICT = os.environ.get(
    'JMDICT_JSON', os.path.expanduser('~/.local/share/nvim/jmdict.json'))
DEFAULT_FURIGANA = os.environ.get(
    'JMDICT_FURIGANA', os.path.expanduser('~/.local/share/nvim/JmdictFurigana.txt'))
DEFAULT_CACHE = os.path.join(
    os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')),
    'create-annotated-japanese-sentences', 'jmdict-index.json')

KANJI = r'一-鿿々〆ヶ'

# Deinflection rule table (from nvim-jmdict).
# Each entry: (suffix, replacement, min_stem_codepoints)
# suffix      : kana suffix to strip
# replacement : kana to append after stripping (may be '')
# min_stem_cp : minimum codepoints required in the remaining stem
#
# Every matching rule produces a candidate.
DEINFLECT_RULES = [
    # -------------------------------------------------------------------------
    # Irregular: する and compound verbs ending in する (〜する)
    # -------------------------------------------------------------------------
    # These are matched as whole-word replacements handled separately below.

    # -------------------------------------------------------------------------
    # Long suffixes first (most specific)
    # -------------------------------------------------------------------------

    # Causative-passive: 〜させられ(る) ← す-verb causative passive
    ('させられる', 'す', 1),
    ('させられた', 'す', 1),
    ('させられて', 'す', 1),
    ('させられない', 'す', 1),
    # Causative: 〜させ(る)
    ('させる', 'す', 1),
    ('させた', 'す', 1),
    ('させて', 'す', 1),
    ('させない', 'す', 1),

    # Ichidan causative-passive: 〜させられ ← 〜る (stem + させられ)
    ('させられる', 'る', 1),
    ('させられた', 'る', 1),
    ('させられて', 'る', 1),
    ('させられない', 'る', 1),
    # Ichidan causative: 〜させる
    ('させる', 'る', 1),
    ('させた', 'る', 1),
    ('させて', 'る', 1),

    # Passive / potential Ichidan: stem + られ
    ('られる', 'る', 1),
    ('られた', 'る', 1),
    ('られて', 'る', 1),
    ('られない', 'る', 1),
    ('られれば', 'る', 1),

    # Polite negative past: 〜ませんでした
    ('ませんでした', 'る', 1),  # Ichidan
    # Polite negative: 〜ません
    ('ません', 'る', 1),        # Ichidan
    # Polite past: 〜ました
    ('ました', 'る', 1),        # Ichidan
    # Polite: 〜ます (Ichidan: strip nothing from stem, add る)
    # The masu-stem of Ichidan is the bare stem, so 食べます → 食べ + ます → 食べる
    ('ます', 'る', 1),

    # te-iru / te-iru contracted forms (progressive)
    ('ている', 'る', 1),
    ('ていた', 'る', 1),
    ('ていて', 'る', 1),
    ('ていない', 'る', 1),
    # contracted: 〜てる / 〜てた
    ('てる', 'る', 1),
    ('てた', 'る', 1),

    # Negative past: 〜なかった (Ichidan)
    ('なかった', 'る', 1),
    # Negative: 〜ない (Ichidan)
    ('ない', 'る', 1),
    # Negative adverbial: 〜なく (Ichidan)
    ('なく', 'る', 1),

    # Conditional: 〜れば (Ichidan)
    ('れば', 'る', 1),
    # Potential Ichidan: 〜られる (already above)

    # Past / ta-form Ichidan: 〜た
    ('た', 'る', 1),
    # Te-form Ichidan: 〜て
    ('て', 'る', 1),
    # Volitional Ichidan: 〜よう
    ('よう', 'る', 1),
    # Imperative Ichidan: 〜ろ / 〜よ
    ('ろ', 'る', 1),
    ('よ', 'る', 1),

    # -------------------------------------------------------------------------
    # Godan (う-verb) conjugation reversal
    # Each godan column ends in a different vowel row:
    #   dict  | a-row | i-row | te/ta | e-row
    #   く    | か    | き    | いて  | け
    #   ぐ    | が    | ぎ    | いで  | げ
    #   す    | さ    | し    | して  | せ
    #   つ    | た    | ち    | って  | て
    #   ぬ    | な    | に    | んで  | ね
    #   ぶ    | ば    | び    | んで  | べ
    #   む    | ま    | み    | んで  | め
    #   る    | ら    | り    | って  | れ
    #   う    | わ    | い    | って  | え
    # -------------------------------------------------------------------------

    # Godan polite negative past
    ('きませんでした', 'く', 1),
    ('ぎませんでした', 'ぐ', 1),
    ('しませんでした', 'す', 1),
    ('ちませんでした', 'つ', 1),
    ('にませんでした', 'ぬ', 1),
    ('びませんでした', 'ぶ', 1),
    ('みませんでした', 'む', 1),
    ('りませんでした', 'る', 1),
    ('いませんでした', 'う', 1),

    # Godan polite negative: 〜ません
    ('きません', 'く', 1),
    ('ぎません', 'ぐ', 1),
    ('しません', 'す', 1),
    ('ちません', 'つ', 1),
    ('にません', 'ぬ', 1),
    ('びません', 'ぶ', 1),
    ('みません', 'む', 1),
    ('りません', 'る', 1),
    ('いません', 'う', 1),

    # Godan polite past: 〜ました
    ('きました', 'く', 1),
    ('ぎました', 'ぐ', 1),
    ('しました', 'す', 1),
    ('ちました', 'つ', 1),
    ('にました', 'ぬ', 1),
    ('びました', 'ぶ', 1),
    ('みました', 'む', 1),
    ('りました', 'る', 1),
    ('いました', 'う', 1),

    # Godan polite: 〜ます
    ('きます', 'く', 1),
    ('ぎます', 'ぐ', 1),
    ('します', 'す', 1),
    ('ちます', 'つ', 1),
    ('にます', 'ぬ', 1),
    ('びます', 'ぶ', 1),
    ('みます', 'む', 1),
    ('ります', 'る', 1),
    ('います', 'う', 1),

    # Godan negative past: 〜なかった
    ('かなかった', 'く', 1),
    ('がなかった', 'ぐ', 1),
    ('さなかった', 'す', 1),
    ('たなかった', 'つ', 1),
    ('ななかった', 'ぬ', 1),
    ('ばなかった', 'ぶ', 1),
    ('まなかった', 'む', 1),
    ('らなかった', 'る', 1),
    ('わなかった', 'う', 1),

    # Godan negative: 〜ない
    ('かない', 'く', 1),
    ('がない', 'ぐ', 1),
    ('さない', 'す', 1),
    ('たない', 'つ', 1),
    ('なない', 'ぬ', 1),
    ('ばない', 'ぶ', 1),
    ('まない', 'む', 1),
    ('らない', 'る', 1),
    ('わない', 'う', 1),

    # Godan te-iru (progressive): 〜いている
    ('いている', 'く', 1),
    ('いでいる', 'ぐ', 1),
    ('している', 'す', 1),
    ('していた', 'す', 1),
    ('していない', 'す', 1),
    ('っている', 'つ', 1),
    ('んでいる', 'ぬ', 1),
    ('んでいる', 'ぶ', 1),
    ('んでいる', 'む', 1),
    ('っている', 'る', 1),
    ('っている', 'う', 1),

    # Godan te-form + た/て (past/te)
    # く → いた / いて
    ('いた', 'く', 1),
    ('いて', 'く', 1),
    # ぐ → いだ / いで
    ('いだ', 'ぐ', 1),
    ('いで', 'ぐ', 1),
    # す → した / して
    ('した', 'す', 1),
    ('して', 'す', 1),
    # つ → った / って
    ('った', 'つ', 1),
    ('って', 'つ', 1),
    # ぬ → んだ / んで
    ('んだ', 'ぬ', 1),
    ('んで', 'ぬ', 1),
    # ぶ → んだ / んで
    ('んだ', 'ぶ', 1),
    ('んで', 'ぶ', 1),
    # む → んだ / んで
    ('んだ', 'む', 1),
    ('んで', 'む', 1),
    # る → った / って  (Godan る)
    ('った', 'る', 1),
    ('って', 'る', 1),
    # う → った / って
    ('った', 'う', 1),
    ('って', 'う', 1),

    # Godan conditional: 〜eba row (e-row + ば)
    ('けば', 'く', 1),
    ('げば', 'ぐ', 1),
    ('せば', 'す', 1),
    ('てば', 'つ', 1),
    ('ねば', 'ぬ', 1),
    ('べば', 'ぶ', 1),
    ('めば', 'む', 1),
    ('れば', 'る', 1),
    ('えば', 'う', 1),

    # Godan potential: e-row + る
    ('ける', 'く', 1),
    ('げる', 'ぐ', 1),
    ('せる', 'す', 1),
    ('てる', 'つ', 1),
    ('ねる', 'ぬ', 1),
    ('べる', 'ぶ', 1),
    ('める', 'む', 1),
    ('れる', 'る', 1),
    ('える', 'う', 1),

    # Godan passive: a-row + れる
    ('かれる', 'く', 1),
    ('がれる', 'ぐ', 1),
    ('される', 'す', 1),
    ('たれる', 'つ', 1),
    ('なれる', 'ぬ', 1),
    ('ばれる', 'ぶ', 1),
    ('まれる', 'む', 1),
    ('られる', 'る', 1),
    ('われる', 'う', 1),

    # Godan causative: a-row + せる/させる
    ('かせる', 'く', 1),
    ('がせる', 'ぐ', 1),
    ('させる', 'す', 1),
    ('たせる', 'つ', 1),
    ('なせる', 'ぬ', 1),
    ('ばせる', 'ぶ', 1),
    ('ませる', 'む', 1),
    ('らせる', 'る', 1),
    ('わせる', 'う', 1),

    # Godan causative-passive: a-row + せられる
    ('かせられる', 'く', 1),
    ('がせられる', 'ぐ', 1),
    ('させられる', 'す', 1),
    ('たせられる', 'つ', 1),
    ('なせられる', 'ぬ', 1),
    ('ばせられる', 'ぶ', 1),
    ('ませられる', 'む', 1),
    ('らせられる', 'る', 1),
    ('わせられる', 'う', 1),

    # Godan causative-passive, short: a-row + される (not used by す-verbs)
    ('かされる', 'く', 1),
    ('がされる', 'ぐ', 1),
    ('たされる', 'つ', 1),
    ('なされる', 'ぬ', 1),
    ('ばされる', 'ぶ', 1),
    ('まされる', 'む', 1),
    ('らされる', 'る', 1),
    ('わされる', 'う', 1),

    # Godan causative-passive, colloquial: a-row + せれる
    ('かせれる', 'く', 1),
    ('がせれる', 'ぐ', 1),
    ('させれる', 'す', 1),
    ('たせれる', 'つ', 1),
    ('なせれる', 'ぬ', 1),
    ('ばせれる', 'ぶ', 1),
    ('ませれる', 'む', 1),
    ('らせれる', 'る', 1),
    ('わせれる', 'う', 1),
    # Ichidan causative-passive, colloquial: 〜させれる
    ('させれる', 'る', 1),

    # Godan volitional: o-row + う
    ('こう', 'く', 1),
    ('ごう', 'ぐ', 1),
    ('そう', 'す', 1),
    ('とう', 'つ', 1),
    ('のう', 'ぬ', 1),
    ('ぼう', 'ぶ', 1),
    ('もう', 'む', 1),
    ('ろう', 'る', 1),
    ('おう', 'う', 1),

    # Godan imperative: e-row bare
    ('け', 'く', 1),
    ('げ', 'ぐ', 1),
    ('せ', 'す', 1),
    ('て', 'つ', 1),
    ('ね', 'ぬ', 1),
    ('べ', 'ぶ', 1),
    ('め', 'む', 1),
    ('れ', 'る', 1),
    ('え', 'う', 1),

    # Godan masu-stem (i-row): used in compounds but also standalone misses
    ('き', 'く', 1),
    ('ぎ', 'ぐ', 1),
    ('し', 'す', 1),
    ('ち', 'つ', 1),
    ('に', 'ぬ', 1),
    ('び', 'ぶ', 1),
    ('み', 'む', 1),
    ('り', 'る', 1),
    ('い', 'う', 1),

    # い-adjectives (not in nvim-jmdict)
    ('くなかった', 'い', 1),
    ('くありません', 'い', 1),
    ('くない', 'い', 1),
    ('かった', 'い', 1),
    ('ければ', 'い', 1),
    ('くて', 'い', 1),
    ('さそう', 'い', 1),
    ('く', 'い', 1),
]

# Irregular くる/する forms: (conjugated kana tail, dictionary kana tail).
IRREGULAR_RULES = [
    # くる (来る) forms
    ('きた', 'くる'),
    ('きて', 'くる'),
    ('きない', 'くる'),
    ('きません', 'くる'),
    ('きます', 'くる'),
    ('こない', 'くる'),
    ('こよう', 'くる'),
    ('こられる', 'くる'),
    ('こい', 'くる'),
    ('くれば', 'くる'),
    # する forms
    ('した', 'する'),
    ('して', 'する'),
    ('しない', 'する'),
    ('しません', 'する'),
    ('しました', 'する'),
    ('します', 'する'),
    ('しよう', 'する'),
    ('される', 'する'),
    ('させる', 'する'),
    ('すれば', 'する'),
    ('しろ', 'する'),
    ('せよ', 'する'),
    ('できる', 'する'),  # potential of する (informal)
]

# Derived stems (potential, passive, causative, causative-passive) conjugate
# like Ichidan verbs, so rules are re-applied to each candidate up to this
# depth, e.g. 書けました → 書ける → 書く.
MAX_DEINFLECT_DEPTH = 3
# Safety cap on the total number of candidates generated.
MAX_DEINFLECT_CANDIDATES = 200

JF = {}


def hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ン' else c for c in s)


def has_kanji(s):
    return re.search('[%s]' % KANJI, s) is not None


class DictionaryMissing(Exception):
    pass


def compact_entry(entry):
    """Kanji forms, kana readings and English senses; senses without a part
    of speech inherit the previous sense's, as in JMdict."""
    senses = []
    pos = []
    for sense in entry.get('sense') or []:
        pos = sense.get('partOfSpeech') or pos
        gl = [g['text'] for g in sense.get('gloss') or []
              if g.get('lang', 'eng') == 'eng' and g.get('text')]
        if gl:
            senses.append({'pos': pos, 'gloss': gl})
    return {
        'kanji': [k['text'] for k in entry.get('kanji') or [] if k.get('text')],
        'kana': [k['text'] for k in entry.get('kana') or [] if k.get('text')],
        'senses': senses,
    }


def build_index(dict_path):
    with open(dict_path, encoding='utf-8') as f:
        data = json.load(f)
    entries = []
    keys = {}
    for entry in data:
        c = compact_entry(entry)
        if not c['senses']:
            continue
        entries.append(c)
        idx = len(entries) - 1
        for text in c['kanji'] + c['kana']:
            lst = keys.setdefault(text, [])
            if not lst or lst[-1] != idx:
                lst.append(idx)
    return {'entries': entries, 'keys': keys}


def load_index(dict_path=DEFAULT_DICT, cache_path=DEFAULT_CACHE):
    """Load the cached index, rebuilding it when the dictionary is newer."""
    dict_path = os.path.expanduser(dict_path)
    if not os.path.exists(dict_path):
        raise DictionaryMissing(
            'JMdict JSON not found at %s; set --dict-file or $JMDICT_JSON, or create it with '
            '`jmdict-to-json download && jmdict-to-json convert -i jmdict.gz` (jmdict-to-json skill)'
            % dict_path)
    mtime = os.path.getmtime(dict_path)
    try:
        if os.path.getmtime(cache_path) >= mtime:
            with open(cache_path, encoding='utf-8') as f:
                idx = json.load(f)
            if idx.get('source') == os.path.abspath(dict_path):
                return idx
    except (OSError, ValueError):
        pass
    idx = build_index(dict_path)
    idx['source'] = os.path.abspath(dict_path)
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        tmp = cache_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(idx, f, ensure_ascii=False, separators=(',', ':'))
        os.replace(tmp, cache_path)
    except OSError as e:
        print('warning: cannot write index cache %s: %s' % (cache_path, e), file=sys.stderr)
    return idx


def deinflect_once(word, add):
    for conj, dict_tail in IRREGULAR_RULES:
        if word.endswith(conj):
            add(word[:-len(conj)] + dict_tail)
    for suffix, repl, min_cp in DEINFLECT_RULES:
        if len(word) > len(suffix) and word.endswith(suffix) and len(word) - len(suffix) >= min_cp:
            add(word[:-len(suffix)] + repl)


def deinflect_levels(word):
    """Candidates grouped by depth, breadth-first, so single-step candidates
    always precede chained ones."""
    if not word:
        return []
    seen = {word}
    levels = []
    level = [word]
    for _ in range(MAX_DEINFLECT_DEPTH):
        nxt = []

        def add(c):
            if c not in seen and len(seen) <= MAX_DEINFLECT_CANDIDATES:
                seen.add(c)
                nxt.append(c)
        for w in level:
            deinflect_once(w, add)
        if not nxt:
            break
        levels.append(nxt)
        level = nxt
    return levels


def find_entries(idx, word):
    """Entries matching `word` exactly (kanji form or kana reading), else the
    entries of the shallowest deinflection depth with any match.

    Returns (entries, [dictionary forms matched]); ([], []) when nothing matches.
    """
    keys, entries = idx['keys'], idx['entries']

    def hits(form):
        # JMdict lists する-verbs (勉強する) under the noun with a `vs` part of speech.
        if form in keys:
            return keys[form]
        if form.endswith('する') and len(form) > 2:
            return [i for i in keys.get(form[:-2], [])
                    if any(p.startswith('vs') for s in entries[i]['senses'] for p in s['pos'])]
        return []

    if hits(word):
        return [entries[i] for i in hits(word)], [word]
    for level in deinflect_levels(word):
        seen = set()
        out = []
        forms = []
        for form in level:
            for i in hits(form):
                if i not in seen:
                    seen.add(i)
                    out.append(entries[i])
                    if form not in forms:
                        forms.append(form)
        if out:
            return out, forms
    return [], []


def load_furigana(path=DEFAULT_FURIGANA):
    """Load JmdictFurigana.txt (lines `text|reading|spec`) into JF."""
    if not os.path.exists(path):
        return False
    with open(path, encoding='utf-8-sig') as f:
        for ln in f:
            p = ln.rstrip('\n').split('|')
            if len(p) == 3:
                JF[(p[0], p[1])] = p[2]
    return True


def furi(s, r):
    """Return a list of (text, reading or None) segments."""
    if not has_kanji(s) or not r or r == '*':
        return [(s, None)]
    r = hira(r)
    spec = JF.get((s, r))
    segs = {}
    if spec:
        try:
            for part in spec.split(';'):
                a, rd = part.split(':', 1)
                if '-' in a:
                    x, y = map(int, a.split('-'))
                else:
                    x = y = int(a)
                segs[x] = (y, rd)
        except ValueError:
            # malformed JmdictFurigana entry; fall back to regex alignment below
            segs = {}
    if segs:
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


def main():
    ap = argparse.ArgumentParser(description='Look up Japanese words in a local JMdict JSON file.')
    ap.add_argument('words', nargs='+', help='words (conjugated forms are deinflected)')
    ap.add_argument('--dict-file', default=DEFAULT_DICT,
                    help='JMdict JSON path (default: $JMDICT_JSON or %(default)s)')
    ap.add_argument('--cache-file', default=DEFAULT_CACHE, help='index cache (default: %(default)s)')
    ap.add_argument('--limit', type=int, default=5, help='max entries per word (default: %(default)s)')
    ap.add_argument('--furigana', action='store_true',
                    help='treat arguments as WORD READING pairs and print per-kanji furigana')
    ap.add_argument('--furigana-file', default=DEFAULT_FURIGANA,
                    help='JmdictFurigana.txt path (default: $JMDICT_FURIGANA or %(default)s)')
    args = ap.parse_args()

    if args.furigana:
        if len(args.words) % 2:
            ap.error('--furigana takes WORD READING pairs')
        if not load_furigana(args.furigana_file):
            print('warning: %s not found; using regex alignment only' % args.furigana_file, file=sys.stderr)
        for w, r in zip(args.words[::2], args.words[1::2]):
            print(json.dumps({'word': w, 'reading': r, 'segments': furi(w, r)}, ensure_ascii=False))
        return

    try:
        idx = load_index(args.dict_file, args.cache_file)
    except DictionaryMissing as e:
        print('error: %s' % e, file=sys.stderr)
        sys.exit(2)
    for w in args.words:
        entries, forms = find_entries(idx, w)
        print(json.dumps({'word': w, 'dictionary_form': forms, 'entries': entries[:args.limit],
                          'total': len(entries)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
