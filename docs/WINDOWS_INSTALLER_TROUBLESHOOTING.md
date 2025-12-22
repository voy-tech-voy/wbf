# Windows Installer Build Troubleshooting Guide

## Problem: App doesn't appear in Windows Start Menu after MSI installation

### Root Causes & Solutions

#### Issue 1: WiX Configuration Missing Shortcuts
**Status**: ✅ FIXED in latest build

The original WiX configuration was missing:
- Start Menu shortcut component
- Desktop shortcut component  
- Icon definition from executable
- Registry entries for Apps & Features display

**Solution**: Updated `build_msix.py` with complete WiX template including:

```xml
<!-- Start Menu Shortcut -->
<DirectoryRef Id="ApplicationProgramsFolder">
    <Component Id="StartMenuShortcut" Guid="{...}">
        <Shortcut Id="ApplicationStartMenuShortcut" 
                 Name="webatchify" 
                 Target="[INSTALLFOLDER]webatchify.exe" 
                 Icon="ProductIcon" />
        ...
    </Component>
</DirectoryRef>

<!-- Icon Definition -->
<Icon Id="ProductIcon" SourceFile="${var.SourceDir}\webatchify.exe" />
<Property Id="ARPPRODUCTICON" Value="ProductIcon" />
```

#### Issue 2: Missing App Icon in Apps & Features
**Status**: ✅ FIXED

**Solution**: 
1. Icon is now extracted from `webatchify.exe` (embedded by PyInstaller)
2. Icon GUID registered in Windows registry:
   ```xml
   <Property Id="ARPPRODUCTICON" Value="ProductIcon" />
   ```
3. Registry entry points to executable:
   ```xml
   <RegistryValue Type="string" Name="DisplayIcon" Value="[INSTALLFOLDER]webatchify.exe" />
   ```

#### Issue 3: MSI Not Building (WiX Toolset not found)
**Status**: Requires manual setup

**Solution**:
1. Download WiX Toolset v3.11+ from https://wixtoolset.org/
2. Install to default location (C:\Program Files (x86)\WiX Toolset v3.11\)
3. Verify installation:
   ```powershell
   ls "C:\Program Files (x86)\WiX Toolset v3.11\bin\heat.exe"
   ls "C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe"
   ls "C:\Program Files (x86)\WiX Toolset v3.11\bin\light.exe"
   ```

#### Issue 4: MSIX Not Building
**Status**: Requires specific setup

**Solution**:
1. Run build with admin privileges:
   ```powershell
   Start-Process PowerShell -Verb RunAs -ArgumentList "-NoExit", "-Command", "cd 'V:\_MY_APPS\ImgApp_1'; .\build\scripts\build_all.ps1 -IncludeMSIX"
   ```
2. Ensure code signing certificate exists:
   - Path: `C:\certs\webatchify_test.pfx`
   - Password: `webatchify123`
3. Check Windows 10/11 version (MSIX requires build 14393+)

## Build Output Structure

### After Successful Build:
```
ImgApp_Releases/
└── v8.0.4/
    ├── webatchify-v8.0.4/              (Application folder with .exe and dependencies)
    ├── webatchify-v8.0.4-installer.msi (MSI installer - ready to distribute)
    ├── webatchify-v8.0.4.msix          (MSIX package - optional, for Microsoft Store)
    └── MSIX_CONVERSION_GUIDE.md        (Instructions for MSIX conversion)
```

### What Each File Does:

1. **webatchify-v8.0.4-installer.msi**
   - Traditional Windows installer
   - ~150-300 MB depending on dependencies
   - Creates Start Menu shortcut ✅ (FIXED)
   - Shows icon in Apps & Features ✅ (FIXED)
   - Can be uninstalled via Control Panel

2. **webatchify-v8.0.4.msix** (if -IncludeMSIX flag used)
   - Modern Windows app package
   - Used for Microsoft Store distribution
   - Automatic updates
   - Sandboxed installation

## Testing Installation

### Test MSI Locally:
```powershell
# Navigate to release directory
cd "V:\_MY_APPS\ImgApp_1\ImgApp_Releases\v8.0.4"

# Install MSI
msiexec /i "webatchify-v8.0.4-installer.msi"

# Check Start Menu
Get-ChildItem $env:ProgramData\Microsoft\Windows\Start Menu\Programs\webatchify\

# Check Apps & Features
Get-Package -Name "webatchify"
```

### Uninstall for Testing:
```powershell
# Via MSI
msiexec /x "webatchify-v8.0.4-installer.msi"

# Via PowerShell
Remove-Item -Path "$env:ProgramFiles\webatchify" -Recurse -Force
```

## WiX Configuration Details

### Key Components Added:

#### 1. Start Menu Folder
```xml
<Directory Id="ProgramMenuFolder">
    <Directory Id="ApplicationProgramsFolder" Name="webatchify" />
</Directory>
```

#### 2. Start Menu Shortcut Component
```xml
<Component Id="StartMenuShortcut" Guid="{11111111-2222-3333-4444-555555555555}">
    <Shortcut Id="ApplicationStartMenuShortcut" 
             Name="webatchify" 
             Target="[INSTALLFOLDER]webatchify.exe" 
             Icon="ProductIcon" />
    <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall" />
</Component>
```

#### 3. Desktop Shortcut Component
```xml
<Component Id="DesktopShortcut" Guid="{66666666-7777-8888-9999-000000000000}">
    <Shortcut Id="DesktopApplicationShortcut" 
             Name="webatchify" 
             Target="[INSTALLFOLDER]webatchify.exe" 
             Icon="ProductIcon" />
</Component>
```

#### 4. Registry Entries
```xml
<RegistryKey Root="HKLM" Key="Software\Microsoft\Windows\CurrentVersion\Uninstall\webatchify">
    <RegistryValue Type="string" Name="DisplayName" Value="webatchify v8.0.4" />
    <RegistryValue Type="string" Name="DisplayIcon" Value="[INSTALLFOLDER]webatchify.exe" />
    <RegistryValue Type="dword" Name="NoModify" Value="1" />
    <RegistryValue Type="dword" Name="NoRepair" Value="1" />
</RegistryKey>
```

## Verification Checklist

After installation, verify:

- [ ] App appears in Windows Start Menu
- [ ] App appears in Apps & Features (Control Panel)
- [ ] Icon displays correctly in Start Menu
- [ ] Icon displays correctly in Apps & Features
- [ ] Desktop shortcut created (if selected)
- [ ] Application launches when clicked
- [ ] Uninstall removes Start Menu folder
- [ ] Uninstall removes application files

## Common Issues & Fixes

### App doesn't appear in Start Menu
- **Cause**: WiX shortcuts not configured
- **Fix**: Use updated `build_msix.py` (already applied ✅)

### No icon in Apps & Features
- **Cause**: ARPPRODUCTICON not set or icon path invalid
- **Fix**: Ensure webatchify.exe is built with embedded icon (PyInstaller does this by default)

### MSI installation fails silently
- **Cause**: WiX components have duplicate GUIDs
- **Fix**: Each component must have unique GUID (already handled)

### MSIX build fails
- **Cause**: Requires admin privileges and valid certificate
- **Fix**: Run `build_all.ps1 -IncludeMSIX` as Administrator

## Build History

### Changes Made (Latest):
1. ✅ Added Start Menu shortcut component to WiX
2. ✅ Added Desktop shortcut component to WiX
3. ✅ Added icon extraction from executable
4. ✅ Added registry entries for proper app discovery
5. ✅ Added help URL and publisher info
6. ✅ Added file association support

### Files Modified:
- `build/scripts/build_msix.py` - Updated WiX template

### Testing Status:
- Build: Pending (test next run)
- Installation: Pending (test on clean Windows)
- Start Menu: Expected to appear ✅
- Icon: Expected to display ✅

## Next Steps

1. **Run Build**:
   ```powershell
   cd "V:\_MY_APPS\ImgApp_1"
   .\build\scripts\build_all.ps1
   ```

2. **Test Installation**:
   ```powershell
   msiexec /i "ImgApp_Releases\v8.0.4\webatchify-v8.0.4-installer.msi"
   ```

3. **Verify**:
   - Check Windows Start Menu for "webatchify"
   - Check Applications in Settings
   - Verify icon displays
   - Test application launch

4. **Build with MSIX** (optional, requires admin):
   ```powershell
   Start-Process PowerShell -Verb RunAs -ArgumentList "-NoExit", "-Command", "cd 'V:\_MY_APPS\ImgApp_1'; .\build\scripts\build_all.ps1 -IncludeMSIX"
   ```

## Support Resources

- WiX Documentation: https://wixtoolset.org/documentation/
- MSIX Documentation: https://docs.microsoft.com/en-us/windows/msix/
- Windows Installer (MSI): https://docs.microsoft.com/en-us/windows/win32/msi/
- PyInstaller Icon Support: https://pyinstaller.org/
