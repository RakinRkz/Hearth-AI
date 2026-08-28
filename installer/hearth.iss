; Inno Setup script for Hearth AI
;
; Per-user install: no UAC prompt, no admin rights, which matters because the
; people this is for often cannot elevate on a work machine. This is the same
; model Chrome and VS Code use for their user installers.
;
; Build with:
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\hearth.iss
; Expects dist\HearthAI\ to already exist (build.spec via build.bat).

#define AppName "Hearth AI"
#define AppExeName "HearthAI.exe"
#define AppPublisher "Rakin"
#define AppURL "https://github.com/RakinRkz/Hearth-AI"

; Version is overridable from CI: ISCC /DAppVersion=1.2.3
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{8F3B1C4E-2A7D-4E19-9C5A-6D1E0B7F2A34}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
VersionInfoVersion={#AppVersion}

; Per-user install - no elevation requested at any point
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={localappdata}\Programs\HearthAI
DisableProgramGroupPage=yes
DefaultGroupName={#AppName}

OutputDir=..\dist\installer
OutputBaseFilename=HearthAI-Setup-{#AppVersion}
SetupIconFile=..\assets\hearth.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

; The payload is a ~254MB tree of mostly-compressible Python and native libs
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; The whole PyInstaller onedir output, including _internal
Source: "..\dist\HearthAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Start {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop a running instance before removing its files, otherwise the uninstall
; leaves the exe and _internal behind and the tray icon lingers.
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "StopHearth"

[Code]
// Downloaded models and chat history live outside {app}, so uninstalling does
// not touch them by default - a 2.4GB re-download is not something to trigger
// silently. Offer it explicitly instead.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\HearthAI');
    if DirExists(DataDir) then
    begin
      // SuppressibleMsgBox, not MsgBox: under /SUPPRESSMSGBOXES a plain MsgBox
      // auto-answers Yes regardless of MB_DEFBUTTON2, so a silent uninstall
      // would delete models and chat history without anyone being asked. The
      // explicit IDNO is the answer used when the box cannot be shown.
      if SuppressibleMsgBox('Also delete your Hearth AI data?' + #13#10#13#10 +
                'This removes downloaded models, chat history and uploaded documents from:' + #13#10 +
                DataDir + #13#10#13#10 +
                'Choose No to keep them for a future reinstall.',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2, IDNO) = IDYES then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;
