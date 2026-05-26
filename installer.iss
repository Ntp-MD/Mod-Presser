; ============================================================
;  EDIT THESE TO CUSTOMIZE YOUR INSTALLER
; ============================================================

#define AppName        "Auto Key Presser"    ; Name shown in installer + Start Menu
#define AppVersion     "1.0"                 ; Version number e.g. "1.0" or "2.5.1"
#define AppPublisher   "Personal"            ; Your name or company name
#define AppURL         "https://example.com" ; Your website (can leave as is)
#define AppExeName     "AutoKeyPresser.exe"  ; Must match PyInstaller --name + .exe
#define OutputFileName "AutoKeyPresser_Setup"; Output installer filename (no spaces)

; ============================================================

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=output
OutputBaseFilename={#OutputFileName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Main executable (built by PyInstaller)
Source: "output\AutoKeyPresser.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start menu shortcut
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional - user can choose during install)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Uncomment below to delete config on uninstall
; Type: files; Name: "{app}\config.json"
