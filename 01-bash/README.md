# 01 - Bash scripting exercise

Exercise: https://courses.dallard.tech/linux/bash_exo/ (slide 18)

## Part 1 - The shell

```bash
echo $0        # the shell running right now
echo $SHELL    # my default (login) shell
```

On Windows I work in **Git Bash**, so both commands show `bash` (`/usr/bin/bash`).
Oh My Zsh only works with zsh (the default shell on Mac). With bash, the same idea is done in the
`~/.bashrc` file, which bash reads every time it starts:

```bash
# in ~/.bashrc
alias gst='git status'
alias gp='git push'
alias gl='git pull'
alias glog='git log --oneline --graph'
```

```bash
source ~/.bashrc
```

**Why `source`?** Running a script normally (`./file`) starts a *new* shell: the aliases and
variables it creates disappear when it ends. `source` executes the file *in the current shell*,
so its aliases and variables stay available. It is how you reload a config file without opening a
new terminal.

## Part 2 - Python

```bash
python --version     # on Windows the command is "python" (or "py"), on Mac/Linux "python3"
```

## Part 3 - The installation script

[`env_install.sh`](env_install.sh) prepares a Python + Jupyter environment.

```bash
chmod +x env_install.sh
./env_install.sh --help
./env_install.sh --dry-run     # shows the commands without installing anything
./env_install.sh
```

| Required feature | How it is done |
|---|---|
| 1. `pretty_print` function | `printf` with a blank line before and after, and a colored level (`[INFO]`, `[ OK ]`, `[WARN]`, `[FAIL]`) |
| 2. Detect the OS | `case "$OSTYPE"`: `darwin*` = macOS, `linux*` = Linux, `msys*`/`cygwin*` = Windows (Git Bash) |
| 3. Check / install Python | tries `python3`, `python` then `py` and keeps the first one that really answers "Python 3"; if none, installs it with `brew`, `apt-get` or `winget` |
| 4. Check pip | `python -m pip --version`, installs it with `ensurepip` (or `apt-get`) if missing |
| 5. Install Jupyter Notebook | `python -m pip install --user notebook` |
| 6. `brew doctor` on macOS | only runs when the OS is macOS, and a warning does not stop the script |

### Bonus features

- **Strict mode** `set -euo pipefail`: the script stops at the first error instead of continuing
  in a broken state (`-e`), refuses unset variables (`-u`) and detects errors inside pipes (`pipefail`).
- **Log file**: every step and command is written with a timestamp in `env_install.log` (ignored by Git).
- **`--dry-run`**: every command goes through a `run` function that only prints it in dry-run mode.
- **`--no-color`** and **`--help`** options.
- **Windows support**: `python3` can be a fake Microsoft Store shortcut on Windows, so the script
  runs each candidate and checks its answer instead of only checking that the command exists.
- **PEP 668**: recent Homebrew and Ubuntu Pythons refuse `pip install` outside a virtual
  environment. If pip refuses, the script installs Jupyter with the system package manager instead.
