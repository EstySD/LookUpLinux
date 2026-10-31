param([ValidateSet('Keys','Pointer','Relative')][string]$Action,[string]$Codes,[int]$X=0,[int]$Y=0,[int]$Buttons=0)
$ErrorActionPreference='Stop'
$gameVm='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
$gameVBox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
$gameInfo=& $gameVBox showvminfo $gameVm --machinereadable
if ($LASTEXITCODE -ne 0 -or $gameInfo -notcontains 'UUID="cf207909-94b5-4b49-8bd8-ccff973c1dc8"' -or
    $gameInfo -notcontains 'name="lookup-gsd-07"' -or $gameInfo -notcontains 'VMState="running"' -or
    $gameInfo -notcontains '"SATA-ImageUUID-0-0"="2712d710-daaa-449c-843d-d570091127bc"' -or
    $gameInfo -notcontains 'macaddress1="080027A05376"' -or
    $gameInfo -notcontains 'Forwarding(0)="lookup-gsd-07-ssh,tcp,127.0.0.1,2227,,22"') {throw 'Owned game clone mismatch'}
# The user assigns the original VM lifecycle to an external agent; never control it.
if ($Action -eq 'Keys') {
    if ($Codes -notmatch '^(?:[0-9a-fA-F]{2}\s*)+$') {throw 'Invalid scancodes'}
    & $gameVBox controlvm $gameVm keyboardputscancode @($Codes.Trim() -split '\s+')
    exit $LASTEXITCODE
}
$gameManager=New-Object -ComObject VirtualBox.VirtualBox
$gameSession=New-Object -ComObject VirtualBox.Session
try {
    $gameManager.FindMachine($gameVm).LockMachine($gameSession,1)
    if ($Action -eq 'Pointer') {
        $gameSession.Console.Mouse.PutMouseEventAbsolute($X+2,$Y+1,0,0,$Buttons)
        $gameSession.Console.Mouse.PutMouseEventAbsolute($X+1,$Y+1,0,0,$Buttons)
    } else {$gameSession.Console.Mouse.PutMouseEvent($X,$Y,0,0,$Buttons)}
} finally {if ($gameSession.State -eq 1) {$gameSession.UnlockMachine()}}
