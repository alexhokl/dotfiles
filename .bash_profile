#!/bin/bash

# Load .bashrc, which loads: ~/.{bash_prompt,aliases,functions,functions_fzf,path,dockerfunc,extra,exports}
if [[ -r "${HOME}/.bashrc" ]]; then
	# shellcheck source=/dev/null
	source "${HOME}/.bashrc"
fi

