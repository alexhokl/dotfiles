# AGENTS.md

Personal dotfiles (bash, macOS primary, some Linux/i3 leftovers). Installed by symlinking, not copying.

## Install / wiring

- `make` (= `bin usr dotfiles etc`) uses `sudo`; `etc`/`usr` targets are
  Linux-oriented (dmidecode, X11). On macOS prefer `make dotfiles`.
- `make dotfiles` symlinks every root `.*` file into `$HOME`, and each root
  `functions_<name>` to `~/.functions_<name>` (note the added leading dot).
- A new `functions_<name>` file is NOT loaded automatically: add `source
  ${HOME}/.functions_<name>` to the list near the end of `.functions`.
- Load order: `.bash_profile` -> `.bashrc` ->
  `~/.{bash_prompt,aliases,functions,path,dockerfunc,extra,exports}`. `.extra`
  is private/untracked.
- Anything under `config/` must be linked explicitly in the `dotfiles` target of
  `Makefile` (e.g. `config/opencode/opencode.json` ->
  `~/.config/opencode/opencode.json`, `config/claude/settings.json` ->
  `~/.claude/settings.json`).
- Agent skills live in `config/opencode/skills/<name>/SKILL.md`; each dir is
  symlinked individually into both `~/.agents/skills/` and `~/.claude/skills/`.
  Re-run `make dotfiles` after adding a skill.
- Bash completions go in `config/bash_completion.d/`.
- `gitignore` (no dot) is hard-linked to `~/.gitignore` as the global gitignore;
  `.gitignore` is this repo's own.

## Checks

- `make test` runs shellcheck over every shell-type file via Docker
  (`jess/shellcheck`). Requires Docker running.
- Quick local alternative: `shellcheck <file>`.
- Follow existing style: tabs for indentation, `# shellcheck source=/dev/null`
  before dynamic `source`, header comment with Usage/Dependencies on functions
  (see `functions_jira`).

## Commits

- Short imperative-past messages, e.g. `Added agent skill sql-export`, `Updated
  .gitignore`.

