---
name: bb-cli
description: Use when the user asks to fetch, list, create, update, manage, or merge BitBucket pull requests, repositories, and projects directly from the terminal.
---

# bb-cli Skill

This skill provides `opencode` with the ability to interact with BitBucket via the local `bb` command-line application.

## Plan / Ask Mode (Read-Only)

Before executing any command, check whether a `<system-reminder>` block containing `Plan mode ACTIVE` is present in your current context. If it is, you are in **read-only mode** and MUST NOT execute any command that creates, updates, deletes, or merges data.

**Forbidden in read-only mode:**
- `bb pr` (create pull request)
- `bb update pr` / `bb approve` / `bb decline` / `bb merge`
- Any command with side effects on the remote repository

**Allowed in read-only mode:**
- `bb list pr` / `bb get pr` / `bb list repos` / `bb list workspaces`
- Any read-only fetch or inspection command

If the user requests a mutating operation while in read-only mode, respond:
> "I am currently in plan/read-only mode. I can describe what this operation would do, but I will not execute it until plan mode ends."

## Prerequisites
1. The `bb` binary must be compiled and available in the system's PATH. If not compiled, it can be built from source in the repository using `go install` or downloaded from its releases page.
2. A configuration file must exist at `~/.bb.yml` containing:
   ```yaml
   client_id: your-client-id
   client_secret: your-client-secret
   port: 8080 # or any available local port for the OAuth flow
   ```
3. The user must be logged in. The command `bb login` will open a browser to authenticate and store access tokens.
4. Many `bb` commands that operate on repositories (like creating/listing PRs) infer the repository context from the local git repository. Ensure the working directory is inside a cloned git repository linked to BitBucket when running those.

## How to use this skill
When the user asks to manage or fetch BitBucket pull requests, repositories, or other entities, follow these steps:
1. Verify `bb` is accessible by running `bb --help` in the bash tool.
2. Formulate the appropriate command based on the user's intent using the provided examples below.
3. Execute the command using the `bash` tool.

## Key Commands & Workflows

### 1. Pull Requests
To list pull requests for the current repository:
```bash
bb list pr [--source <branch>] [--destination <branch>] [--detail]
```

To create a new pull request:
```bash
bb pr -t "<title>" -m "<description>" [-s <source-branch>] [-d <destination-branch>]
```

To view details of a specific pull request:
```bash
bb describe -i <pr-id>
```

To approve, decline, or unapprove a pull request:
```bash
bb approve -i <pr-id>
bb decline -i <pr-id>
bb unapprove -i <pr-id>
```

To merge a pull request:
```bash
bb merge -i <pr-id> [--strategy <merge_commit|no_commit|squash>] [--close-source-branch=true|false]
```

To add a comment to a pull request:
```bash
bb comment -i <pr-id> -m "<comment body>"
```

To checkout the branch of a pull request locally:
```bash
bb checkout -i <pr-id>
```

### 2. Exploring Repositories & Projects
To list repositories in a workspace:
```bash
bb list repos -w <workspace-slug> [-p <project-key>]
```

To list projects in a workspace:
```bash
bb list projects -w <workspace-slug>
```

### 3. Users & Permissions
To show the currently authenticated user:
```bash
bb whoami
```

To list users in a workspace:
```bash
bb list users -w <workspace-slug>
```

To check repository permissions:
```bash
bb list repository-permissions -w <workspace-slug> -r <repo-slug>
```

### 4. Environments
The CLI also supports interacting with environments and variables.
- `bb list environment`
- `bb list environment-variable`
- `bb create environment`
- `bb create environment-variable`

*(Note: Discover more flags and nested subcommands using `bb <command> --help` if needed)*