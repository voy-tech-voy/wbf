# ImgApp Version Management Strategy

## 📁 **Directory Structure**
```
V:\_MY_APPS\
├── ImgApp_1\                    # Main development directory (Git repo)
├── ImgApp_Releases\             # Release archives
│   ├── v1.0.0\
│   │   ├── ImgApp-v1.0.0.zip   # Source code archive
│   │   └── ImgApp.exe          # Compiled executable
│   └── v1.1.0\
└── ImgApp_Backups\             # Manual backups (optional)
    ├── 2025-11-18_stable\
    └── 2025-11-20_features\
```

## 🔄 **Git Workflow**

### **Branch Strategy:**
- **`master`** - Production-ready code
- **`develop`** - Integration branch for features
- **`feature/feature-name`** - Individual features
- **`hotfix/issue-name`** - Critical fixes

### **Version Numbering:**
- **Major.Minor.Patch** (Semantic Versioning)
- **1.0.0** - Initial release
- **1.1.0** - New features
- **1.0.1** - Bug fixes

### **Common Commands:**

#### **Daily Development:**
```bash
# Check status
git status

# Stage and commit changes
git add .
git commit -m "Add: New feature description"

# Create feature branch
git checkout -b feature/new-conversion-format
git checkout master  # Return to main
```

#### **Releases:**
```bash
# Tag a release
git tag v1.1.0 -m "Add video quality presets"

# Create release archive
git archive --format=zip --output=../ImgApp_Releases/v1.1.0/ImgApp-v1.1.0.zip HEAD

# View tags
git tag
git log --oneline
```

## 💾 **Backup Strategy**

### **Automated (Git):**
- Every commit is a backup point
- Tags mark stable versions
- Branch history preserves development

### **Manual Archives:**
```powershell
# Create release package
$version = "1.0.0"
$releaseDir = "V:\_MY_APPS\ImgApp_Releases\v$version"
New-Item -ItemType Directory -Path $releaseDir -Force
Copy-Item "dist\ImgApp.exe" "$releaseDir\ImgApp.exe"
```

### **External Backup (Recommended):**
1. **Cloud Storage**: Copy to OneDrive/Google Drive
2. **External Drive**: Weekly full backup
3. **Network Storage**: If available

## 🏷️ **Release Process**

### **1. Pre-Release:**
```bash
# Update version file
# Update CHANGELOG.md
# Test thoroughly
# Commit all changes
git add .
git commit -m "Prepare release v1.1.0"
```

### **2. Release:**
```bash
# Create tag
git tag v1.1.0 -m "Release v1.1.0: Add new features"

# Build executable
.\imgapp_venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name="ImgApp" --add-data="gui;gui" --add-data="core;core" main.py

# Archive source
git archive --format=zip --output=../ImgApp_Releases/v1.1.0/ImgApp-v1.1.0-source.zip v1.1.0
```

### **3. Post-Release:**
```bash
# Copy executable to release folder
# Update documentation
# Plan next version
```

## 🛠️ **Tools & Scripts**

### **Quick Scripts:**
- `git_status.bat` - Check project status
- `build_release.bat` - Automated build process
- `backup_project.bat` - Manual backup creation

### **File Organization:**
```
ImgApp_1\
├── .git\                # Git repository data
├── .gitignore          # Ignore file for Git
├── CHANGELOG.md        # Version history
├── version.py          # Version information
├── git_status.bat      # Status checking script
└── [source files...]
```

## 📋 **Best Practices**

1. **Commit Often**: Small, focused commits
2. **Descriptive Messages**: Clear commit descriptions
3. **Tag Releases**: Mark stable versions
4. **Update Changelog**: Document all changes
5. **Test Before Release**: Verify executables work
6. **Backup Releases**: Keep executable copies

## 🔍 **Monitoring**

### **Check Project Health:**
```bash
# View recent activity
git log --oneline -10

# Check repository size
git count-objects -vH

# Verify integrity
git fsck
```