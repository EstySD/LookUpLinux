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
$lookupVm='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
$lookupVBox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
$lookupInfo=& $lookupVBox showvminfo $lookupVm --machinereadable
if ($LASTEXITCODE -ne 0 -or $lookupInfo -notcontains 'name="lookup-gsd-07"') { throw 'Owned clone identity mismatch' }
if ($lookupInfo -notcontains 'macaddress1="080027A05376"' -or
    $lookupInfo -notcontains 'Forwarding(0)="lookup-gsd-07-ssh,tcp,127.0.0.1,2227,,22"') { throw 'Owned clone network identity mismatch' }
$lookupOriginal=& $lookupVBox showvminfo abc73254-ddf7-4f1f-9c66-7c2fcc5254d7 --machinereadable
if ($LASTEXITCODE -ne 0 -or $lookupOriginal -notcontains 'VMState="poweroff"') { throw 'Original VM must remain powered off' }
if ($Action -eq 'Check') { $lookupInfo | Select-String '^(name|UUID|VMState|macaddress1|Forwarding)' | ForEach-Object { $_.Line }; exit 0 }
if ($lookupInfo -notcontains 'VMState="running"') { throw 'Owned clone is not running' }
if ($Action -eq 'Native') {
    $lookupEncoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Command))
    ssh -o BatchMode=yes -o HostKeyAlias=lookup-gsd-07 -o UserKnownHostsFile=D:/vm/machines/lookup-gsd-07/ssh_known_hosts -p 2227 archvm "sudo -n -H -u lookup07 python /home/lookup07/check_settings_app.py --command $lookupEncoded"
    exit $LASTEXITCODE
}
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
