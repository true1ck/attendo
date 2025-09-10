# 🚀 ATTENDO - GitHub Setup Guide

This guide helps you push your ATTENDO project to GitHub quickly and easily.

## 🎯 Quick Steps

### Option 1: Automated Script (Recommended)
```powershell
# Run the automated setup script
python scripts/git_setup_and_push.py
```
The script will guide you through:
- ✅ Git initialization and configuration
- ✅ File staging and committing
- ✅ GitHub remote setup
- ✅ Pushing to GitHub

### Option 2: Manual Setup

#### Step 1: Create GitHub Repository
1. Go to [GitHub](https://github.com/new)
2. Repository name: `vendor-timesheet-tool`
3. Description: `ATTENDO - Workforce Management Platform`
4. Set visibility (Public/Private)
5. **Don't** initialize with README
6. Click "Create repository"

#### Step 2: Initialize Local Git Repository
```powershell
# Initialize git (if not already done)
git init

# Configure Git user (if not already done)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add files to staging
git add .

# Create initial commit
git commit -m "Initial commit: ATTENDO Workforce Management Platform"

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/vendor-timesheet-tool.git

# Set main branch and push
git branch -M main
git push -u origin main
```

## 📝 Before Pushing

Make sure you have:
- ✅ Completed the project setup
- ✅ Generated sample data (optional but recommended)
- ✅ Tested the application locally
- ✅ Updated any placeholder URLs in README

## 🔐 Authentication

### GitHub Personal Access Token
1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (for private repos) or `public_repo` (for public repos)
4. Use this token as your password when pushing

### Alternative: GitHub CLI
```powershell
# Install GitHub CLI and authenticate
gh auth login
# Then use git commands normally
```

## 🎉 After Successful Push

Your repository will be available at:
`https://github.com/YOUR_USERNAME/vendor-timesheet-tool`

### Update README
1. Edit `README.md`
2. Replace `YOUR_USERNAME` with your actual GitHub username
3. Commit and push the changes:
   ```powershell
   git add README.md
   git commit -m "Update README with correct GitHub URLs"
   git push
   ```

### Set Up Repository
1. **Add topics/tags:** In GitHub, go to Settings > General > Topics
   - Add: `flask`, `python`, `attendance`, `workforce-management`, `sqlite`
2. **Enable Issues:** Settings > General > Features > Issues
3. **Enable Discussions:** Settings > General > Features > Discussions (optional)
4. **Branch Protection:** Settings > Branches (for production)

## 🎯 Repository Structure

After pushing, your repository will contain:
```
vendor-timesheet-tool/
├── 📄 README.md              # Main project documentation
├── 📄 SETUP.md               # Detailed setup guide
├── 📄 GITHUB_SETUP.md        # This file
├── 📄 requirements.txt       # Python dependencies
├── 🐍 app.py                 # Main application
├── 🐍 models.py              # Database models
├── 📁 scripts/               # Setup and utility scripts
├── 📁 templates/             # HTML templates
├── 📁 static/                # CSS, JS, images
├── 📁 docs/                  # Documentation files
└── 📁 Test_DATA/             # Sample CSV data
```

## ✅ Verification Checklist

After pushing to GitHub:
- [ ] Repository is accessible at your GitHub URL
- [ ] All files are present (check file count)
- [ ] README displays correctly
- [ ] No sensitive files were pushed (.env, *.db files)
- [ ] Repository description is set
- [ ] License is specified (if applicable)

## 🚨 Troubleshooting

### Push Rejected
```
! [rejected] main -> main (fetch first)
```
**Solution:** Someone else made changes, or you need to pull first:
```powershell
git pull origin main --allow-unrelated-histories
git push origin main
```

### Authentication Failed
**Solution:** Use Personal Access Token instead of password

### Large File Error
**Solution:** Check what large files are being committed:
```powershell
git ls-files | xargs ls -lh | sort -k5 -hr | head -20
```

### Already Exists Error
**Solution:** Repository with same name exists. Either:
1. Use a different repository name
2. Delete the existing repository on GitHub
3. Push to existing repository (if it's yours)

## 📞 Need Help?

- 📖 **Full Setup Guide:** See [SETUP.md](SETUP.md)
- 🐛 **Issues:** Create an issue in your GitHub repository
- 💬 **GitHub Docs:** [GitHub Documentation](https://docs.github.com)
- 🔍 **Git Help:** `git help <command>`

---

**🎉 Once pushed successfully, share your repository URL with others to showcase ATTENDO!**
