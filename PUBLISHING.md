# Publishing this to GitHub

This repo is ready to push. I can't push it for you (that needs your GitHub login,
which I don't handle), but here's the whole process — about four commands.

## 1. Before you publish (30 seconds)
- Open `LICENSE` and replace `<YOUR NAME>` with your name. (Or swap MIT for another
  license if you prefer.)
- Optional: skim `README.md` and adjust the project name / wording to taste.

## 2. Create an empty repo on GitHub
Go to github.com → **New repository** → name it (e.g. `ai-capital-cycle-fragility`)
→ **do not** add a README, .gitignore, or license (this repo already has them) → Create.
Copy the repo URL it shows you.

## 3. Initialize and push (run inside the unzipped folder)
```bash
cd ai-capital-cycle-fragility

git init
git add .
git commit -m "Initial commit: GSADF bubble detector + research roadmap"

git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO>.git
git push -u origin main
```
Replace `<YOUR-USERNAME>/<YOUR-REPO>` with the URL from step 2.

That's it — committing under your own git identity from the first commit, so the
authorship is clean for a portfolio.

## Notes
- If git asks who you are first, set it once:
  `git config --global user.name "Your Name"` and
  `git config --global user.email "you@example.com"`.
- GitHub now uses tokens, not passwords, for HTTPS pushes. If prompted for a password,
  paste a **personal access token** (GitHub → Settings → Developer settings → Tokens),
  or use the GitHub CLI (`gh auth login`) / an SSH remote instead. Generate and handle
  that token yourself — never paste it into a chat.
- `.gitignore` already excludes `*.csv` and a `data/` folder, so any real price data
  you pull stays out of the public repo by default.
