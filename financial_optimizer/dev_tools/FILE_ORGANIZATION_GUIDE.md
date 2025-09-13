# File Organization Quick Reference
**Financial Optimizer Project Structure Guide**

## 🔧 Tools to Prevent File Mess

### 1. **File Creation Script** 
```bash
# Run this instead of creating files manually
/workspaces/financial_optimizer/dev_tools/create_file.sh
```

### 2. **VS Code Snippets**
- Type `business-spec` in a .md file → Creates Business Mode specification template
- Type `personal-spec` in a .md file → Creates Personal Mode specification template  
- Type `fin-module` in a .py file → Creates proper Python module template

### 3. **Command Palette Tasks** (Ctrl+Shift+P)
- "Tasks: Run Task" → "Create New Business Mode Specification"
- "Tasks: Run Task" → "Create New Python Module"
- "Tasks: Run Task" → "Create New Prototype"

## 📁 **Correct File Locations**

### **Documentation & Specifications**
```
/specifications/
├── modules/           # Feature specifications (Business/Personal Mode)
├── architecture/      # System architecture docs
├── implementation/    # Implementation plans and updates
└── meta/             # Documentation about documentation
```

### **Code & Development**
```
/core/                 # Core calculation engines and base functionality
/modules/              # Feature modules (organized by use case)
/services/             # Services (data, notifications, etc.)
/shared/               # Shared utilities and components
/dev_tools/            # Development tools and prototypes
├── prototypes/        # Working prototypes and examples
└── tests/             # Development tests
```

## 🚫 **What NOT to Put in Root Directory**
- ❌ Specification files (`*_SPECIFICATION*.md`)
- ❌ Workflow files (`*workflow*.py`)
- ❌ Form files (`*forms*.py`) 
- ❌ Configuration files (`*config*.py`)
- ❌ Test files (`*_test*.py`)

## ✅ **What BELONGS in Root Directory**
- ✅ `README.md` - Project overview
- ✅ `requirements.txt` - Python dependencies
- ✅ `simple_app.py` - Main application file
- ✅ `mypy.ini` - Type checking configuration

## 🛡️ **Protection Features Enabled**

### **VS Code Settings**
- ✅ File creation confirmations
- ✅ File nesting organization
- ✅ Auto-save protection
- ✅ Project structure awareness

### **Git Protection**  
- ✅ `.gitignore` rules prevent misplaced files from being committed
- ✅ Patterns catch common mistakes

### **Editor Configuration**
- ✅ `.editorconfig` enforces consistent formatting
- ✅ Specification files get proper formatting

## 🚨 **If Files Get Misplaced Again**

### **Quick Cleanup Commands**
```bash
# Remove empty files in root (be careful!)
find /workspaces/financial_optimizer -maxdepth 1 -name "*.md" -size 0 -delete
find /workspaces/financial_optimizer -maxdepth 1 -name "*.py" -size 0 -delete

# Check for misplaced files
ls -la /workspaces/financial_optimizer/*.md
ls -la /workspaces/financial_optimizer/*.py
```

### **Prevention Checklist**
1. Always use absolute paths when creating files
2. Use the file creation script for new files
3. Check VS Code's current folder before creating files  
4. Use snippets instead of typing file templates manually
5. Review git status before committing to catch misplaced files

---

**Last Updated**: July 21, 2025  
**Location**: `/workspaces/financial_optimizer/dev_tools/FILE_ORGANIZATION_GUIDE.md`
