# 02 - Git mini exercise

Exercise: https://gist.github.com/bdallard/8bdbdd70f234f94823c0c2cde9515388 (slide 26)

Environment: Windows, **Git Bash** (installed with Git for Windows). Git Bash gives a real bash
terminal on Windows, so all the Linux commands of the course (`ls`, `touch`, `chmod`...) work.

The script of part 7 is [`install.sh`](install.sh): it checks that `git` and `python` are installed
and creates a virtual environment.

## Part 1 - Setup and configuration

```bash
git --version
git config --global user.name "My Name"
git config --global user.email "my.email@example.com"
git config --list
```

The name and email are written in every commit. I used the email of my GitHub account so GitHub
links the commits to my profile. `--global` saves the setting for all the repositories of my computer.

## Part 2 - Create a repository

```bash
mkdir my-first-repo
cd my-first-repo
git init
touch readme.txt
```

`git init` creates a hidden `.git` folder: this folder is the repository (all the history lives inside).

## Part 3 - First commit

```bash
git status                        # readme.txt is "untracked"
git add readme.txt                # readme.txt goes to the staging area
git commit -m "Add readme file"
git log                           # one commit, with its hash, author and date
```

## Part 4 - Modify a file

```bash
echo "Second line" >> readme.txt
git status                        # readme.txt is now "modified" (not staged)
git add readme.txt
git commit -m "Add a second line to readme"
git log --oneline                 # two commits
```

Git compares the working directory with the last commit, so it detects the change by itself, but
nothing is saved until I `add` and `commit` it.

## Part 5 - Explore

| Command | What it shows |
|---|---|
| `git diff` | the lines changed but not staged yet |
| `git diff --staged` | the lines staged for the next commit |
| `git log --oneline` | one line per commit: short hash + message |
| `git show <hash>` | the content of one commit |

## Part 6 - Branches

```bash
git branch                        # list branches, the current one has a *
git branch feature-script         # create a branch (I stay on main)
git switch feature-script         # move to it (old syntax: git checkout feature-script)
git switch -c dev                 # create + move in one command (old syntax: git checkout -b dev)
git switch feature-script
git branch
```

A branch is only a pointer to a commit, which is why creating one is instant.

## Part 7 - A script on a branch

```bash
git switch feature-script
touch install.sh                  # content: see install.sh
chmod +x install.sh               # make it executable
git add install.sh
git commit -m "Add install script"
git log --oneline
```

## Part 8 - Merge

```bash
git switch main
ls                                # install.sh is not here: it only exists on feature-script
git merge feature-script
ls                                # install.sh is here now
git branch -d feature-script      # the branch is merged, it can be deleted
```

main had no new commit since the branch was created, so Git did a **fast-forward**: it simply moved
the `main` pointer forward, without creating a merge commit.

## Part 9 - Push to GitHub

On github.com: **New repository**, name `my-first-repo`, **without** README (a README created on
GitHub would be a commit that does not exist on my computer, and the push would be rejected).

```bash
git remote add origin https://github.com/<my-username>/my-first-repo.git
git branch -M main
git push -u origin main
```

On Windows the first push opens a browser window (Git Credential Manager) to log in to GitHub.
`-u` links my local `main` to `origin/main`, so next time `git push` is enough.

## Part 10 - Delete and clone

```bash
cd ..
rm -rf my-first-repo
git clone https://github.com/<my-username>/my-first-repo.git
cd my-first-repo
git log --oneline                 # all the files and the whole history are back
```

## Part 11 - Full workflow

```bash
mkdir bash-installer && cd bash-installer
git init
echo "# bash-installer" > README.md
git add README.md
git commit -m "Initial commit"
git switch -c feature-install
cp ../install.sh .
git add install.sh
git commit -m "Add install script"
git switch main
git merge feature-install
git branch -d feature-install
git remote add origin https://github.com/<my-username>/bash-installer.git
git push -u origin main
```

This whole course repository follows the same workflow: one branch per exercise, merged into `main`
when it is finished (`git log --graph --oneline` shows it).

## Reflection questions

**1. Why is version control important?**
Every version of the project is saved, so I can see what changed, when and why, and go back to a
version that worked. It also lets several people work on the same code without overwriting each other.

**2. What is the difference between staging and committing?**
`git add` prepares the next snapshot: I choose which changes go in it. `git commit` saves that
snapshot permanently in the history with a message. Staging lets me commit only part of my changes.

**3. When should you make a commit?**
After each small step that works and makes sense on its own (a function, a fix, an exercise).
Small commits are easier to understand and to undo than one big commit at the end.

**4. What is the difference between `git init` and `git clone`?**
`git init` starts a new, empty repository in the current folder. `git clone` downloads an existing
repository with its whole history and automatically sets the `origin` remote.

**5. Why are good commit messages important?**
The history is only useful if it can be read. A message like "Add input validation to transfer()"
explains the change months later; "update" or "fix" explains nothing.

**6. Why use branches?**
To work on a feature or try an idea in isolation. `main` stays stable, and the work is merged only
when it is ready (or deleted if the idea was bad).

**7. When should you create a branch instead of working on main?**
For every new feature, fix or experiment, and always when working in a team: `main` should always
contain code that works.
