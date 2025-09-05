; This script is parameterized. The AppVersion and SafeVersion are passed in
; from the GitHub Actions workflow using the /D flag.

#define MyAppName "TASA"
#define MyAppPublisher "RIA"
#define MyAppURL "https://www.ria.ee/"
#define MyOutputName "tasa-installer"

[Setup]
; App details defined from command line or above
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}

; Installation directory
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
OutputBaseFilename={#MyOutputName}-{#SafeVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Source: "path\in\runner" DestDir: "path\in\installation"
; The main executable built by Nuitka.
Source: "..\build\windows\tasa-{#SafeVersion}.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu and Desktop shortcuts
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\tasa-{#SafeVersion}.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\tasa-{#SafeVersion}.exe"; Tasks: desktopicon

[Run]
; Option to run the application after installation finishes
Filename: "{app}\tasa-{#SafeVersion}.exe"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";
