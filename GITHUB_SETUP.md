# GitHub Repository Setup Guide

## Steps to Push to GitHub

### 1. Create a Personal Access Token (PAT)
Since GitHub no longer accepts passwords, you need to create a Personal Access Token:

1. Go to GitHub.com and sign in
2. Click your profile picture → **Settings**
3. Scroll down to **Developer settings** (bottom left)
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token (classic)**
6. Give it a name (e.g., "React E-Commerce App")
7. Select scopes: Check **repo** (full control of private repositories)
8. Click **Generate token**
9. **COPY THE TOKEN** (you won't see it again!)

### 2. Create a New Repository on GitHub

1. Go to GitHub.com
2. Click the **+** icon (top right) → **New repository**
3. Repository name: `react-ecommerce-app` (or any name you prefer)
4. Description: "React e-commerce application with login and cart functionality"
5. Set visibility: **Public**
6. **DO NOT** initialize with README, .gitignore, or license
7. Click **Create repository**

### 3. Push Your Code

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository (replace YOUR_USERNAME with sha2140 and REPO_NAME with your repo name)
git remote add origin https://github.com/sha2140/react-ecommerce-app.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub (you'll be prompted for username and password)
# Username: sha2140
# Password: <paste your Personal Access Token here>
git push -u origin main
```

## Quick Commands Summary

```bash
# Verify git config
git config user.name
git config user.email

# Check status
git status

# View commits
git log --oneline

# Push to GitHub
git push -u origin main
```

## Important Notes

- **Never share your Personal Access Token publicly**
- The token acts as your password for Git operations
- Store it securely (consider using a password manager)
- You can revoke tokens anytime in GitHub settings
