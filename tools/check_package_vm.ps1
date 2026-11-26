param(
    [ValidateSet('Keys','Pointer','Relative','Scroll','Screenshot','Check','Native')][string]$Action='Check',
    [string]$Codes,
    [int]$X=0,
    [int]$Y=0,
    [int]$Buttons=0,
    [string]$Output,
    [string]$Command
)
$ErrorActionPreference='Stop'
$lookupVm='abc73254-ddf7-4f1f-9c66-7c2fcc5254d7'
$lookupVBox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
$lookupInfo=& $lookupVBox showvminfo $lookupVm --machinereadable
if ($LASTEXITCODE -ne 0 -or $lookupInfo -notcontains 'name="arch-kde"') { throw 'Owned clone identity mismatch' }
if ($lookupInfo -notcontains 'Forwarding(0)="ssh,tcp,127.0.0.1,2223,,22"' -or
    $lookupInfo -notcontains '"SATA-ImageUUID-0-0"="798288be-61f7-4c1e-9867-ae8b7228068b"') { throw 'Shared Arch identity mismatch' }
if ($Action -eq 'Check') { $lookupInfo | Select-String '^(name|UUID|VMState|macaddress1|Forwarding)' | ForEach-Object { $_.Line }; exit 0 }
if ($lookupInfo -notcontains 'VMState="running"') { throw 'Owned clone is not running' }
if ($Action -eq 'Native') { throw 'Clone-specific Native helper retired. Migrate the test to shared Arch explicitly; see D:/vm/README.md.' }
if ($Action -eq 'Keys') {
    if ($Codes -notmatch '^(?:[0-9a-fA-F]{2}\s*)+$') { throw 'Invalid key scancodes' }
    & $lookupVBox controlvm $lookupVm keyboardputscancode @($Codes.Trim() -split '\s+')
    exit $LASTEXITCODE
}
if ($Action -eq 'Screenshot') {
    if (-not $Output) { throw 'Screenshot output required' }
    & $lookupVBox controlvm $lookupVm screenshotpng ([IO.Path]::GetFullPath($Output))
    exit $LASTEXITCODE
}
$lookupCom=New-Object -ComObject VirtualBox.VirtualBox
$lookupSession=New-Object -ComObject VirtualBox.Session
$lookupCom.FindMachine($lookupVm).LockMachine($lookupSession,1)
try {
    if ($Action -eq 'Pointer') {
        $lookupSession.Console.Mouse.PutMouseEventAbsolute($X+2,$Y+1,0,0,$Buttons)
        $lookupSession.Console.Mouse.PutMouseEventAbsolute($X+1,$Y+1,0,0,$Buttons)
    } elseif ($Action -eq 'Scroll') {
        $lookupSession.Console.Mouse.PutMouseEvent(0,0,$Y,0,0)
    } else {
        $lookupSession.Console.Mouse.PutMouseEvent($X,$Y,0,0,$Buttons)
    }
} finally { $lookupSession.UnlockMachine() }
