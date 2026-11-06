# Publishing updates to GitHub

The repo already exists at github.com/Justins10000x/AI-cap-cyc-fragility. To publish v3:

1. Unzip the v3 package. Copy **everything inside it** over your local clone of the repo
   (replace files when asked). If you have no local clone:
   `git clone https://github.com/Justins10000x/AI-cap-cyc-fragility.git`
2. In a terminal, from inside the repo folder:

```bash
git add -A
git commit -m "v3: robust null, family-wise dating, fundamentals mode; withdraw v2 results" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

Before pushing, open `LICENSE` and replace `<YOUR NAME>` with your name (it is still a placeholder).

GitHub asks for a personal access token rather than your password on push. Create one under
Settings → Developer settings → Personal access tokens, or run `gh auth login` once. Never
paste a token into a chat.

`data/` is git-ignored, so the market-data CSVs stay local; `results/*.csv` are committed on purpose.
