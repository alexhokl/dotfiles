#!/bin/bash
# Shell prompt based on the Solarized Dark theme.
# Screenshot: http://i.imgur.com/EkEtphC.png
# Heavily inspired by @necolas’s prompt: https://github.com/necolas/dotfiles
# iTerm → Profiles → Text → use 13pt Monaco with 1.1 vertical spacing.
# vim: set filetype=sh :

__git_ps1_custom() {
	local s='';
	local ahead=0;
	local behind=0;
	local branchName='';
	local remote_commit='';

	# Check if the current directory is in a Git repository.
	if [ "$(git rev-parse --is-inside-work-tree &>/dev/null; echo "${?}")" == '0' ]; then

		# check if the current directory is in .git before running git checks
		if [ "$(git rev-parse --is-inside-git-dir 2> /dev/null)" == 'false' ]; then

			if [[ -O "$(git rev-parse --show-toplevel)/.git/index" ]]; then
				git update-index --really-refresh -q &> /dev/null;
			fi;

			# Check for uncommitted changes in the index.
			if ! git diff --quiet --ignore-submodules --cached; then
				s+='+';
			fi;

			# Check for unstaged changes.
			if ! git diff-files --quiet --ignore-submodules --; then
				s+='!';
			fi;

			# Check for untracked files.
			if [ -n "$(git ls-files --others --exclude-standard)" ]; then
				s+='?';
			fi;

			# Check for stashed files.
			if git rev-parse --verify refs/stash &>/dev/null; then
				s+='$';
			fi;

		fi;

		# Get the short symbolic ref.
		# If HEAD isn’t a symbolic ref, get the short SHA for the latest commit
		# Otherwise, just give up.
		branchName="$(git symbolic-ref --quiet --short HEAD 2> /dev/null || \
			git rev-parse --short HEAD 2> /dev/null || \
			echo '(unknown)')";

		# check if the current directory is in .git before running git checks
		if [ "$(git rev-parse --is-inside-git-dir 2> /dev/null)" == 'false' ]; then

			remote_commit=$(git ls-remote --exit-code . origin/${branchName} 2>/dev/null)
			if [ -n "${remote_commit}" ]; then

				# Check if it is ahead of or behind origin
				ahead=$(git rev-list --count origin/${branchName}.. 2>/dev/null);
				behind=$(git rev-list --count ..origin/${branchName} 2>/dev/null);

				if [ $ahead -ne 0 ] && [ $behind -ne 0 ]; then
					branchName+=" diverged ${behind}< ${ahead}>";
				elif [ $behind -ne 0 ]; then
					branchName+=" ${behind}<origin";
				elif [ $ahead -ne 0 ]; then
					branchName+=" ${ahead}>origin";
				fi;
			else
				branchName+=" (local-only)"
			fi;

		fi;

		[ -n "${s}" ] && s=" [${s}]";

		echo -e "${1}${branchName}${blue}${s}";
	else
		return;
	fi;
}
