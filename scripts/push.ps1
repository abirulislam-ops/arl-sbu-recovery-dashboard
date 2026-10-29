# Push to origin using the Windows-stored git credential. No secret is written to disk.
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$src = @"
using System;
using System.Runtime.InteropServices;
public class CredAuto {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct CREDENTIAL {
    public int Flags; public int Type; public string TargetName; public string Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public int CredentialBlobSize; public IntPtr CredentialBlob;
    public int Persist; public int AttributeCount; public IntPtr Attributes;
    public string TargetAlias; public string UserName;
  }
  [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool CredRead(string target, int type, int flags, out IntPtr cred);
  [DllImport("advapi32.dll")] public static extern void CredFree(IntPtr cred);
}
"@
if (-not ("CredAuto" -as [type])) { Add-Type -TypeDefinition $src }
$ptr = [IntPtr]::Zero
if (-not [CredAuto]::CredRead("git:https://sabbiriron@github.com", 1, 0, [ref]$ptr)) {
  Write-Output "no stored credential - skip push"; exit 0
}
$c = [Runtime.InteropServices.Marshal]::PtrToStructure($ptr, [type][CredAuto+CREDENTIAL])
$blob = [Runtime.InteropServices.Marshal]::PtrToStringUni($c.CredentialBlob, $c.CredentialBlobSize/2)
[CredAuto]::CredFree($ptr)
$env:GH_USER = $c.UserName
$env:GH_PAT = $blob
$ap = Join-Path $env:TEMP "gitaskpass_auto.cmd"
@"
@echo off
echo %1 | findstr /I "username" >nul
if %errorlevel%==0 (echo %GH_USER%) else (echo %GH_PAT%)
"@ | Set-Content $ap -Encoding ASCII
$env:GIT_TERMINAL_PROMPT = "0"
Push-Location $repo
$out = git -c core.askPass="$ap" push origin main 2>&1
Pop-Location
Remove-Item $ap -Force -ErrorAction SilentlyContinue
($out | Out-String) -replace "https://[^ ]*", "https://<redacted>"
$env:GH_PAT = $null; $env:GH_USER = $null
