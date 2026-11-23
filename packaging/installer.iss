; Inno Setup script for PC Toolkit
; Build the exe first (see build.ps1), then compile this file with ISCC.exe.

#define AppName "PC Toolkit"
#define AppVersion "0.1.0"
#define AppPublisher "blazerbob"
#define AppURL "https://github.com/blazerbob/pc-toolkit"

[Setup]
AppId={{8F3A2B14-7C6D-4E29-9A51-0B7C1D2E3F40}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={code:GetDefaultDir}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=PC-Toolkit-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "РЎРѕР·РґР°С‚СЊ СЏСЂР»С‹Рє РЅР° СЂР°Р±РѕС‡РµРј СЃС‚РѕР»Рµ"; GroupDescription: "Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ:"

[Files]
Source: "..\dist\PC Toolkit.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\PC Toolkit.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\PC Toolkit.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PC Toolkit.exe"; Description: "Р—Р°РїСѓСЃС‚РёС‚СЊ {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
// РџРѕ СѓРјРѕР»С‡Р°РЅРёСЋ СЃС‚Р°РІРёРј РЅР° РґРёСЃРє D (РµСЃР»Рё РѕРЅ РµСЃС‚СЊ), РёРЅР°С‡Рµ РІ Program Files.
function GetDefaultDir(Param: String): String;
begin
  if DirExists('D:\') then
    Result := 'D:\{#AppName}'
  else
    Result := ExpandConstant('{autopf}\{#AppName}');
end;
