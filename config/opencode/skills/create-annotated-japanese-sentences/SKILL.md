---
name: create-annotated-japanese-sentences
description: Use when the user asks to annotate, break down, analyse, or explain Japanese sentences as HTML. Reads Japanese sentences from the prompt or a file and produces a self-contained HTML page with colour-coded word types, furigana on all kanji, per-word English glosses, and a full-sentence translation. Also supports bulk/automated annotation of many files (e.g. dozens of Markdown newsletters) via a bundled script. Trigger keywords including 'annotate Japanese', 'Japanese sentence breakdown', 'furigana', 'word types', 'parts of speech Japanese'.
---

# create-annotated-japanese-sentences Skill

Produces a study-friendly HTML page for one or more Japanese sentences, built from the bundled `template.html` (in this skill's directory).

## Plan / Ask Mode (Read-Only)

Before doing anything, check whether a `<system-reminder>` block indicating Plan mode is present in your current context. If it is, you are in **read-only mode**:

- Do NOT write the HTML file.
- Instead, show the annotation in chat (full sentence with readings, a Markdown word table, and the translation for each sentence).
- Reading input files and querying jisho.org is allowed.

## 1. Input

- **From the prompt**: use the Japanese text supplied by the user.
- **From a file**:
  - `.txt` / `.md`: read directly.
  - PDF, DOCX, PPTX, XLSX, images: extract text with the `liteparse` skill first.
- Split text into sentences on `。`, `！`, `？` (and ASCII `!`, `?`) and line breaks. Keep the terminal punctuation with its sentence. Drop empty lines and Markdown syntax.

## 2. Output location

1. If the user gives an explicit output path, use it.
2. Else if input came from a file, write `<input-basename>.html` next to the input file.
3. Else write `annotated-sentences-<YYYYMMDD-HHMMSS>.html` in the current working directory.

Tell the user the final path when done.

## 3. Analysis rules

### Tokenisation
- Split each sentence into words. Keep a **conjugated verb or adjective as a single token** (e.g. `食べました`, `高くない`), not split into stem + auxiliaries.
- Standalone auxiliaries/copula (`です`, `だ`, `でした`) that follow a noun or な-adjective are separate `auxiliary` tokens.
- Particles (`は`, `が`, `を`, `に`, `で`, `から`, `ね`, `よ`, ...) are separate tokens.
- Punctuation (`。`, `、`, `！`, `？`, `「」`) is rendered in the full sentence without colour and omitted from the table.

### Word types → CSS class

| Type | CSS class | Colour |
|---|---|---|
| Noun (incl. proper noun, する-noun used as noun) | `noun` | blue |
| Verb (incl. する verbs, conjugated forms) | `verb` | red |
| い-adjective / な-adjective | `adjective` | green (Type column text: "い-adjective" or "な-adjective") |
| Adverb | `adverb` | cyan |
| Particle | `particle` | grey |
| Auxiliary verb / copula | `auxiliary` | orange |
| Pronoun | `pronoun` | purple |
| Conjunction | `conjunction` | brown |
| Counter / number | `counter` | teal |
| Interjection | `interjection` | pink |
| Prefix / suffix (お, ご, さん, 的, ...) | `affix` | dark yellow |
| Adnominal (ある, そんな, 大きな, ...) | `adnominal` | light green |

Demonstrative adnominals (この, その, あの, どの) are classed as `pronoun`.

### Verifying with jisho.org
When a word type or a kanji reading is in doubt (ambiguous POS such as words that are both noun and adverb, rare kanji, unusual readings), use `webfetch` on:

```
https://jisho.org/api/v1/search/words?keyword=<url-encoded word or dictionary form>
```

Use `data[0].japanese[].reading` for readings and `data[0].senses[].parts_of_speech` for word types; pick the sense matching the sentence context. Do NOT query every word — only uncertain ones. If jisho.org is unreachable or returns nothing, proceed with your best judgement and add the `uncertain` class to that word's Type cell (renders a red "?").

### Furigana
- Annotate **every kanji**, including common ones, with hiragana using `<ruby>`.
- Split per kanji when the mapping is clear: `<ruby>日<rt>に</rt>本<rt>ほん</rt></ruby>`.
- For okurigana, ruby only the kanji part: `<ruby>食<rt>た</rt></ruby>べました`.
- For jukujikun / ateji (今日, 大人, 明日, 一人), use one reading over the whole word: `<ruby>今日<rt>きょう</rt></ruby>`.

### Glosses
- English column: concise meaning in context. For conjugated words, give dictionary form + meaning + form, e.g. `to eat (polite past)`.
- Dictionary form column: the lemma (e.g. `食べる`); for uninflected words repeat the word.
- Full translation: natural English rendering of the whole sentence.

## 4. Building the HTML

1. Read `template.html` from this skill's directory.
2. Replace both `{{TITLE}}` occurrences with a title (input file name, or "Annotated Japanese Sentences").
3. Replace `<!-- SENTENCES -->` with one block per sentence, using this exact structure. In the full sentence, wrap each word (except particles, numbers/counters and Latin-script terms) in `<a href="https://jisho.org/word/<url-encoded dictionary form>" target="_blank" rel="noopener">`, using the same lemma as the Dictionary form column:

```html
<section class="sentence">
	<h2>Sentence 1</h2>
	<div class="full">
		<span class="pronoun"><a href="https://jisho.org/word/%E7%A7%81" target="_blank" rel="noopener"><ruby>私<rt>わたし</rt></ruby></a></span><span class="particle">は</span><span class="noun"><a href="https://jisho.org/word/%E6%AF%8E%E6%9C%9D" target="_blank" rel="noopener"><ruby>毎<rt>まい</rt>朝<rt>あさ</rt></ruby></a></span><span class="noun"><a href="https://jisho.org/word/%E3%82%B3%E3%83%BC%E3%83%92%E3%83%BC" target="_blank" rel="noopener">コーヒー</a></span><span class="particle">を</span><span class="verb"><a href="https://jisho.org/word/%E9%A3%B2%E3%82%80" target="_blank" rel="noopener"><ruby>飲<rt>の</rt></ruby>みます</a></span>。
	</div>
	<table>
		<thead>
			<tr><th>Word</th><th>Reading</th><th>Dictionary form</th><th>Type</th><th>English</th></tr>
		</thead>
		<tbody>
			<tr><td class="word pronoun"><ruby>私<rt>わたし</rt></ruby></td><td>わたし</td><td>私</td><td><span class="badge pronoun">Pronoun</span></td><td>I</td></tr>
			<tr><td class="word particle">は</td><td>は (wa)</td><td>は</td><td><span class="badge particle">Particle</span></td><td>topic marker</td></tr>
			<tr><td class="word noun"><ruby>毎<rt>まい</rt>朝<rt>あさ</rt></ruby></td><td>まいあさ</td><td>毎朝</td><td><span class="badge noun">Noun</span></td><td>every morning</td></tr>
			<tr><td class="word noun">コーヒー</td><td>コーヒー</td><td>コーヒー</td><td><span class="badge noun">Noun</span></td><td>coffee</td></tr>
			<tr><td class="word particle">を</td><td>を (o)</td><td>を</td><td><span class="badge particle">Particle</span></td><td>object marker</td></tr>
			<tr><td class="word verb"><ruby>飲<rt>の</rt></ruby>みます</td><td>のみます</td><td>飲む</td><td><span class="badge verb">Verb</span></td><td>to drink (polite non-past)</td></tr>
		</tbody>
	</table>
	<p class="translation">I drink coffee every morning.</p>
</section>
```

- For an uncertain type, use `<td class="uncertain"><span class="badge ...">...</span></td>`.
- Keep the spans in `.full` adjacent with no whitespace between them (Japanese has no spaces).
- Do not add JavaScript or external assets; the file must stay self-contained.

4. Write the result to the output path from section 2.

## 5. Bulk / automated mode

Use this when there are many sentences or files (for example dozens of `.md` newsletters) and hand annotation is impractical. For a handful of sentences, annotate by hand as in sections 3–4 (better quality).

### Setup

Homebrew/system Python on macOS blocks global `pip install` (PEP 668), so use a virtualenv:

```
python3 -m venv ~/.venvs/annotate-ja
~/.venvs/annotate-ja/bin/pip install fugashi unidic-lite jamdict jamdict-data
```

Then run the script with `~/.venvs/annotate-ja/bin/python`.

- `JmdictFurigana.txt` supplies per-kanji furigana. Path: `--furigana-file`, else `$JMDICT_FURIGANA`, else `~/.local/share/nvim/JmdictFurigana.txt` (used by the `nvim-kanji-to-hiragana` plugin). Download from https://github.com/Doublevil/JmdictFurigana/releases. Optional: if missing, the script warns and falls back to regex alignment.
- Gotcha: a stub `unidic` package can shadow `unidic-lite`, so the default `fugashi.Tagger()` fails with "no such file: mecabrc". The script avoids this with `fugashi.GenericTagger('-r /dev/null -d ' + unidic_lite.DICDIR)`.

### Running

```
~/.venvs/annotate-ja/bin/python <skill-dir>/scripts/annotate.py FILE.md [FILE2.md ...] [--out-dir DIR] [--trans-dir DIR] [--furigana-file PATH]
```

Writes `<name>.html` next to each input (or in `--out-dir`) using `template.html`, dumps `<trans-dir>/sent/<name>.txt` (lines `N<TAB>sentence`) for translators, and reads translations from `<trans-dir>/trans/<name>.txt`. Default `--trans-dir` is `.annotate`.

### What it does

- Splits sentences on `。！？` outside 「」/（）; skips `#` lines; adds "Paragraph N" headings per blank-line-separated paragraph.
- Tokenises with MeCab (UniDic). A verb or い-adjective absorbs following auxiliaries and the て form; a な-adjective absorbs な/に; numbers merge with counters. Compound nouns are not merged.
- Maps UniDic parts of speech to the CSS classes above. Uses the Adnominal type (ある, そんな) from section 3.
- Furigana: JmdictFurigana first, then regex alignment of kanji runs against the UniDic reading.
- Glosses: `jamdict` lookup of the dictionary form (exact match and part-of-speech match preferred, first sense). Particles/auxiliaries use a built-in gloss table. Verb/adjective glosses get a form suffix such as "(polite, past)". Content words with no gloss get the `uncertain` class.

### Translations (cannot be automated)

1. Run the script once; pages show "(translation pending)".
2. Delegate translation to parallel subagents (about 5 files each). Each reads `<trans-dir>/sent/<name>.txt` and writes `<trans-dir>/trans/<name>.txt` with one line `N<TAB>English` per sentence (same N, none missing). Lines with a non-numeric N are skipped with a warning.
3. Re-run the script; it merges the translations.

### Limits

Slang, contractions and rare words may be tokenised or glossed wrongly; glosses use the first dictionary sense and may not fit the context. Tell the user the output is machine-annotated.
