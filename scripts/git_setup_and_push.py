#!/usr/bin/env python
"""
Git Setup and Push Script for ATTENDO Project
This script helps you set up Git repository and push to GitHub.

Usage:
  python scripts/git_setup_and_push.py
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description="", check=True):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}")
    print(f"   Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and check:
            print(f"❌ Error: {result.stderr}")
            return False
        else:
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            print(f"✅ {description} completed")
            return True
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def check_git_installed():
    """Check if Git is installed"""
    try:
        result = subprocess.run("git --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Git is not installed")
            return False
    except Exception:
        print("❌ Git is not installed or not in PATH")
        return False

def get_user_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def main():
    print("🚀 ATTENDO - Git Setup and Push Script")
    print("=" * 50)
    
    # Check if we're in the project directory
    if not os.path.exists("app.py"):
        print("❌ Please run this script from the project root directory (vendor-timesheet-tool)")
        sys.exit(1)
    
    # Check if Git is installed
    if not check_git_installed():
        print("\n📥 Please install Git first:")
        print("   Windows: https://git-scm.com/download/windows")
        print("   macOS: brew install git")
        print("   Linux: sudo apt install git")
        sys.exit(1)
    
    # Check if already a git repository
    if os.path.exists(".git"):
        print("✅ Already a Git repository")
        existing_repo = True
    else:
        existing_repo = False
    
    print("\n📋 We'll help you:")
    print("   1. Initialize Git repository (if needed)")
    print("   2. Configure Git user settings")
    print("   3. Add all files to staging")
    print("   4. Create initial commit")
    print("   5. Add GitHub remote")
    print("   6. Push to GitHub")
    
    proceed = get_user_input("\n❓ Do you want to proceed? (y/n)", "y")
    if proceed.lower() != 'y':
        print("❌ Aborted by user")
        sys.exit(0)
    
    # Step 1: Initialize Git repository
    if not existing_repo:
        if not run_command("git init", "Initializing Git repository"):
            sys.exit(1)
    
    # Step 2: Configure Git user (if not already configured)
    result = subprocess.run("git config user.name", shell=True, capture_output=True)
    if result.returncode != 0:
        print("\n⚙️ Git user not configured. Let's set it up:")
        git_name = get_user_input("Enter your Git username (for commits)")
        git_email = get_user_input("Enter your Git email")
        
        if not run_command(f'git config user.name "{git_name}"', "Setting Git username"):
            sys.exit(1)
        if not run_command(f'git config user.email "{git_email}"', "Setting Git email"):
            sys.exit(1)
    else:
        print("✅ Git user already configured")
    
    # Step 3: Add files to staging
    print("\n📁 Adding files to Git staging area...")
    
    # Create .gitignore if it doesn't exist
    gitignore_content = """# Database
*.db
vendor_timesheet.db

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.pytest_cache/
*.egg-info/

# Virtual Environment
venv/
env/
.venv/

# Environment Variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
.tmp/

# Logs
*.log
logs/

# Uploads
uploads/
temp/

# Node modules (if any)
node_modules/
"""
    
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore file")
    
    if not run_command("git add .", "Adding all files to staging"):
        sys.exit(1)
    
    # Step 4: Create commit
    commit_message = get_user_input("Enter commit message", "Initial commit: ATTENDO Workforce Management Platform")
    if not run_command(f'git commit -m "{commit_message}"', "Creating commit"):
        # If commit fails, might be because nothing to commit
        print("ℹ️ Nothing to commit or commit failed. This might be normal.")
    
    # Step 5: Add GitHub remote
    print("\n🔗 Setting up GitHub remote...")
    print("   First, create a repository on GitHub:")
    print("   1. Go to https://github.com/new")
    print("   2. Repository name: vendor-timesheet-tool")
    print("   3. Description: ATTENDO - Workforce Management Platform")
    print("   4. Set to Public or Private as needed")
    print("   5. DO NOT initialize with README (we already have files)")
    
    github_username = get_user_input("\nEnter your GitHub username")
    repo_name = get_user_input("Enter repository name", "vendor-timesheet-tool")
    
    github_url = f"https://github.com/{github_username}/{repo_name}.git"
    
    # Check if remote already exists
    result = subprocess.run("git remote get-url origin", shell=True, capture_output=True)
    if result.returncode == 0:
        print(f"ℹ️ Remote 'origin' already exists: {result.stdout.strip()}")
        update_remote = get_user_input("Update remote URL? (y/n)", "n")
        if update_remote.lower() == 'y':
            if not run_command(f"git remote set-url origin {github_url}", "Updating remote URL"):
                sys.exit(1)
    else:
        if not run_command(f"git remote add origin {github_url}", "Adding GitHub remote"):
            sys.exit(1)
    
    # Step 6: Push to GitHub
    print(f"\n🚀 Pushing to GitHub: {github_url}")
    print("   If this is your first push, you might be asked to authenticate.")
    print("   Use your GitHub username and Personal Access Token (not password).")
    
    # Try to push
    branch_name = get_user_input("Enter branch name to push to", "main")
    
    # First, let's set the upstream branch
    if not run_command(f"git branch -M {branch_name}", f"Setting main branch to {branch_name}"):
        print("ℹ️ Branch rename might have failed, continuing...")
    
    push_success = run_command(f"git push -u origin {branch_name}", f"Pushing to GitHub ({branch_name} branch)", check=False)
    
    if push_success:
        print("\n🎉 SUCCESS! Your code has been pushed to GitHub!")
        print(f"   Repository URL: https://github.com/{github_username}/{repo_name}")
        print(f"   Clone URL: {github_url}")
        
        print("\n📝 Next steps:")
        print("   1. Visit your GitHub repository to verify files are there")
        print("   2. Update README.md with your actual GitHub username")
        print("   3. Set up GitHub Pages (optional) for documentation")
        print("   4. Configure branch protection rules (optional)")
        print("   5. Invite collaborators (optional)")
        
        print(f"\n🔗 Quick links:")
        print(f"   📊 Repository: https://github.com/{github_username}/{repo_name}")
        print(f"   ⚙️ Settings: https://github.com/{github_username}/{repo_name}/settings")
        print(f"   🔧 Issues: https://github.com/{github_username}/{repo_name}/issues")
    else:
        print("\n❌ Push failed. Common solutions:")
        print("   1. Check if repository exists on GitHub")
        print("   2. Verify GitHub username and repository name")
        print("   3. Ensure you have push permissions")
        print("   4. Try authenticating with GitHub CLI: gh auth login")
        print("   5. Use Personal Access Token instead of password")

if __name__ == "__main__":
    main()
