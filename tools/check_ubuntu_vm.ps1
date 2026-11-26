throw 'Ubuntu VM retired by Denis on 2026-11-13. Only Arch KDE is available; Ubuntu acceptance is BLOCKED. See D:/vm/README.md.'
param(
    [ValidateSet('Check','Keys','Pointer','Screenshot')][string]$Action='Check',
    [string]$Codes,[int]$X=0,[int]$Y=0,[int]$Buttons=0,[string]$Output
)
$ErrorActionPreference='Stop'
$ubuntuVm='e178b651-d035-4a30-b8b1-cea26bcf57d6'
$ubuntuVBox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
$ubuntuInfo=& $ubuntuVBox showvminfo $ubuntuVm --machinereadable
if ($LASTEXITCODE -ne 0 -or $ubuntuInfo -notcontains 'name="discourse-ubuntu-2404"' -or
    $ubuntuInfo -notcontains 'Forwarding(0)="ssh,tcp,127.0.0.1,2222,,22"') { throw 'Ubuntu VM identity mismatch' }
if ($Action -eq 'Check') {
    $ubuntuInfo | Select-String '^(name|UUID|VMState|Forwarding)' | ForEach-Object { $_.Line }
    exit 0
}
if ($ubuntuInfo -notcontains 'VMState="running"') { throw 'Ubuntu VM is not running' }
if ($Action -eq 'Keys') {
    if ($Codes -notmatch '^(?:[0-9a-fA-F]{2}\s*)+$') { throw 'Invalid key scancodes' }
    & $ubuntuVBox controlvm $ubuntuVm keyboardputscancode @($Codes.Trim() -split '\s+')
    exit $LASTEXITCODE
}
if ($Action -eq 'Screenshot') {
    if (-not $Output) { throw 'Screenshot output required' }
    & $ubuntuVBox controlvm $ubuntuVm screenshotpng ([IO.Path]::GetFullPath($Output))
    exit $LASTEXITCODE
}
$ubuntuCom=New-Object -ComObject VirtualBox.VirtualBox
$ubuntuSession=New-Object -ComObject VirtualBox.Session
$ubuntuCom.FindMachine($ubuntuVm).LockMachine($ubuntuSession,1)
try {
    $ubuntuSession.Console.Mouse.PutMouseEventAbsolute($X+2,$Y+1,0,0,$Buttons)
    $ubuntuSession.Console.Mouse.PutMouseEventAbsolute($X+1,$Y+1,0,0,$Buttons)
} finally { $ubuntuSession.UnlockMachine() }
