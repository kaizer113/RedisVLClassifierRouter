# GitHub Publishing Checklist

Use this checklist before publishing the project to GitHub.

## Pre-Publication Checklist

### 🔒 Security Review

- [ ] **Remove all API keys from code**
  ```bash
  # Search for potential API keys
  grep -r "sk-" *.py
  grep -r "OPENAI_API_KEY.*=" *.py | grep -v "config.example.py"
  ```

- [ ] **Verify config.py is in .gitignore**
  ```bash
  git check-ignore config.py
  # Should output: config.py
  ```

- [ ] **Check for other secrets**
  ```bash
  # Look for common secret patterns
  grep -r "password\|secret\|token\|key" *.py | grep -v "example"
  ```

- [ ] **Review .gitignore completeness**
  ```bash
  cat .gitignore
  # Verify it includes: config.py, .env, .venv/, __pycache__/
  ```

### 📝 Documentation Review

- [ ] **README.md is complete**
  - [ ] Project description
  - [ ] Installation instructions
  - [ ] Usage examples
  - [ ] Configuration options
  - [ ] Performance comparison

- [ ] **All documentation files exist**
  - [ ] README.md
  - [ ] README_OPTIMIZER.md
  - [ ] SETUP.md
  - [ ] CONTRIBUTING.md
  - [ ] LICENSE
  - [ ] PROJECT_STRUCTURE.md

- [ ] **Update repository URLs in documentation**
  - [ ] README.md (replace `yourusername` with actual username)
  - [ ] CONTRIBUTING.md
  - [ ] SETUP.md
  - [ ] pyproject.toml

### 🧪 Code Quality

- [ ] **All scripts run without errors**
  ```bash
  python -m py_compile 1_baseline_with_openai.py
  python -m py_compile 2_RedisVLRouter.py
  python -m py_compile 3_RedisVLRouterwithChatGPT.py
  python -m py_compile 4_RedisVLRouterWithOptimizer.py
  ```

- [ ] **No syntax errors**
  ```bash
  uv run ruff check .
  ```

- [ ] **Code is formatted**
  ```bash
  uv run ruff format .
  ```

- [ ] **Dependencies are up to date**
  ```bash
  uv sync
  ```

### 📦 Project Files

- [ ] **pyproject.toml is complete**
  - [ ] Correct project name
  - [ ] Version number
  - [ ] Description
  - [ ] Dependencies list
  - [ ] Author information
  - [ ] License

- [ ] **uv.lock is committed**
  ```bash
  git add uv.lock
  ```

- [ ] **config.example.py exists**
  ```bash
  ls config.example.py
  ```

- [ ] **LICENSE file exists**
  ```bash
  ls LICENSE
  ```

### 🎯 Dataset Files

- [ ] **CSV files are present**
  - [ ] BBC News Train2.csv
  - [ ] BBC News Train.csv
  - [ ] BBC News Test.csv

- [ ] **CSV files are not too large for GitHub**
  ```bash
  ls -lh *.csv
  # Each should be < 100 MB (GitHub limit)
  ```

### 🔧 GitHub Configuration

- [ ] **Create .github/workflows/ci.yml**
  ```bash
  ls .github/workflows/ci.yml
  ```

- [ ] **CI configuration is valid**
  - [ ] Correct Python version
  - [ ] Redis service configured
  - [ ] All jobs defined

### 🚀 Final Checks

- [ ] **Test quickstart script**
  ```bash
  ./quickstart.sh
  ```

- [ ] **Verify git status**
  ```bash
  git status
  # Should NOT show config.py or .venv/
  ```

- [ ] **Check for large files**
  ```bash
  find . -type f -size +50M
  # Should not show any files > 100MB
  ```

## Publication Steps

### 1. Initialize Git Repository (if not already done)

```bash
git init
git add .
git commit -m "Initial commit: RedisVL Classifier Router"
```

### 2. Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `RedisVLClassifierRouter`
3. Description: "Text classification using RedisVL SemanticRouter with automatic threshold optimization"
4. Choose: Public or Private
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

### 3. Connect Local Repository to GitHub

```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/RedisVLClassifierRouter.git
git branch -M main
git push -u origin main
```

### 4. Configure Repository Settings

#### Topics (for discoverability)
Add these topics to your repository:
- `redis`
- `vector-search`
- `classification`
- `nlp`
- `semantic-router`
- `redisvl`
- `machine-learning`
- `python`
- `openai`

#### About Section
- Description: "Text classification using RedisVL SemanticRouter with automatic threshold optimization"
- Website: (optional)
- Topics: (add the topics above)

#### Features
Enable:
- [x] Issues
- [x] Discussions (optional)
- [x] Projects (optional)

### 5. Create Initial Release (Optional)

1. Go to "Releases" → "Create a new release"
2. Tag: `v0.1.0`
3. Title: "Initial Release"
4. Description:
   ```markdown
   ## Features
   - Pure GPT-4 baseline classification
   - RedisVL SemanticRouter implementation
   - Hybrid approach with ChatGPT fallback
   - Automatic threshold optimization
   - BBC News dataset with 5 categories
   - Performance metrics and cost analysis
   
   ## Requirements
   - Python 3.11+
   - Redis Stack
   - OpenAI API key
   ```

### 6. Update README with Correct URLs

After creating the repository, update these files with your actual GitHub username:

```bash
# Replace in README.md
sed -i '' 's/yourusername/YOUR_ACTUAL_USERNAME/g' README.md

# Replace in CONTRIBUTING.md
sed -i '' 's/yourusername/YOUR_ACTUAL_USERNAME/g' CONTRIBUTING.md

# Replace in SETUP.md
sed -i '' 's/yourusername/YOUR_ACTUAL_USERNAME/g' SETUP.md

# Replace in pyproject.toml
sed -i '' 's/yourusername/YOUR_ACTUAL_USERNAME/g' pyproject.toml

# Commit the changes
git add .
git commit -m "Update repository URLs with actual username"
git push
```

### 7. Verify GitHub Actions

1. Go to "Actions" tab
2. Check if CI workflow runs successfully
3. Fix any issues if the workflow fails

## Post-Publication

### Share Your Project

- [ ] **Tweet about it** (if applicable)
- [ ] **Post on Reddit** (r/Python, r/MachineLearning, r/redis)
- [ ] **Share on LinkedIn**
- [ ] **Add to awesome lists** (awesome-redis, awesome-nlp)

### Monitor

- [ ] **Watch for issues**
- [ ] **Respond to questions**
- [ ] **Review pull requests**
- [ ] **Update documentation** as needed

### Maintenance

- [ ] **Set up branch protection** (optional)
  - Require PR reviews
  - Require status checks to pass
  - Require branches to be up to date

- [ ] **Add collaborators** (if team project)

- [ ] **Create project board** (optional)
  - For tracking issues and features

## Common Issues

### Issue: config.py was committed

**Solution:**
```bash
# Remove from git but keep locally
git rm --cached config.py
git commit -m "Remove config.py from git"
git push

# Make sure it's in .gitignore
echo "config.py" >> .gitignore
git add .gitignore
git commit -m "Add config.py to .gitignore"
git push
```

### Issue: Large files rejected

**Solution:**
```bash
# If CSV files are too large, use Git LFS
git lfs install
git lfs track "*.csv"
git add .gitattributes
git commit -m "Track CSV files with Git LFS"
git push
```

### Issue: CI failing

**Solution:**
1. Check the Actions tab for error details
2. Fix the issue locally
3. Test with `./quickstart.sh`
4. Commit and push the fix

## Final Verification

After publishing, verify:

- [ ] **Repository is accessible**
  - Visit: `https://github.com/YOUR_USERNAME/RedisVLClassifierRouter`

- [ ] **README renders correctly**
  - Check formatting, links, code blocks

- [ ] **CI badge is green** (if added)
  - Add badge to README: `![CI](https://github.com/YOUR_USERNAME/RedisVLClassifierRouter/workflows/CI/badge.svg)`

- [ ] **Clone and test from scratch**
  ```bash
  cd /tmp
  git clone https://github.com/YOUR_USERNAME/RedisVLClassifierRouter.git
  cd RedisVLClassifierRouter
  ./quickstart.sh
  ```

## Success! 🎉

Your project is now published on GitHub!

Next steps:
1. Star your own repository (for visibility)
2. Share with the community
3. Keep improving and updating
4. Respond to issues and PRs

---

**Remember:** Never commit API keys or secrets to Git!

