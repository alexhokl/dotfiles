#!/bin/bash

# .bashrc returns early for non-interactive shells, so load the environment
# here for login shells that are not interactive (e.g. `ssh host cmd`).
if [[ $- != *i* ]]; then
	for file in ~/.{path,exports}; do
		# shellcheck source=/dev/null
		[[ -r "$file" ]] && source "$file"
	done
	unset file
fi

# Load .bashrc, which loads: ~/.{bash_prompt,aliases,functions,path,dockerfunc,extra,exports}
if [[ -r "${HOME}/.bashrc" ]]; then
	# shellcheck source=/dev/null
	source "${HOME}/.bashrc"
fi

