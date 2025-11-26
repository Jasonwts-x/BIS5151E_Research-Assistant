# Contributing to ResearchAssistantGPT

This is a **short, practical guide** for teammates working on the shared branches:

- `feature/deepl-integration`
- `feature/evaluation-integration`
- `feature/n8n-governance`
- `feature/weaviate-integration`

Please **read this before you start coding**.

---

## 1. Branches – how to use them

### 1.1. Clone the repo (first time only)

```bash
git clone https://github.com/Jasonwts-x/BIS5151E_Research-Assistant.git
cd BIS5151E_Research-Assistant
```

### 1.2. Switch to your assigned feature branch

Do **NOT** work directly on `main`.

Example:

```bash
git fetch --all
git checkout feature/weaviate-integration
git branch
```

> Always do your work in your **feature/** branch, never in `main`.

---

## 2. Development environment (DevContainer)

We all develop inside the **VS Code DevContainer**, so the environment is identical.

Open VS Code → **Reopen in Container**  
Then wait until dependencies install.

If the terminal looks like:

```
vscode ➜ /workspaces/BIS5151E_Research-Assistant (feature/branch) $
```

…you are inside the container.

---

## 3. Coding standards

Run before every commit:

```bash
ruff check <folder> --fix || true
black <folder> || true
```

Rules:

- Use type hints
- Use logging, not print
- No large commented blocks
- No secrets in code

---

## 4. Working on your feature

### Pull latest changes:

```bash
git checkout feature/<your-branch>
git pull origin main
```

### Work normally inside the branch.

---

## 5. Committing and pushing

### Check changes

```bash
git status
```

### Run formatters

```bash
ruff check <folder> --fix || true
black <folder> || true
```

### Stage files

```bash
git add -A
```

### Commit

```bash
git commit -m "feature: describe you made changes"

e.g.: git commit -m "weaviate: added weaviate api connection"
```

### Push

```bash
git push origin feature/<your-branch>
```

If error: run:

```bash
git pull --rebase origin feature/<your-branch>
git push
```

---

## 6. Pull Request (PR)

1. Open GitHub → New Pull Request  
2. Base: `main`  
3. Compare: `feature/<your-branch>`
4. Write summary
5. Request review

---

## 7. Do / Don’t

### DO
- Work only in feature branches  
- Use DevContainer  
- Run ruff + black  
- Add/update tests  
- Write clear commits  
- Pull before pushing  

### DON'T
- Don’t push to main  
- Don’t commit secrets or `.env`  
- Don’t commit caches  
- Don’t ignore linting  
- Don’t force push without discussing  

---

If unsure → ask in chat or open a GitHub Issue.
