; Define base app details
#define MyAppName "TASA"
#define MyAppPublisher "RIA"
#define MyAppURL "https://www.ria.ee/"

; Logic to conditionally create a final version string with the postfix
; CORRECTED: Removed {#...} from inside the define expression
#ifdef Postfix
  #define MyFinalVersion SafeVersion + Postfix
#else
  #define MyFinalVersion SafeVersion
#endif

; Use the final version string to define all filenames
#define MyAppExeName "tasa-" + MyFinalVersion + ".exe"
#define MyOutputBaseFilename "tasa-installer-" + MyFinalVersion

[Setup]
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
WizardStyle=modern
Compression=lzma
SolidCompression=yes
OutputDir=Output
OutputBaseFilename={#MyOutputBaseFilename}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\build\windows\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";
