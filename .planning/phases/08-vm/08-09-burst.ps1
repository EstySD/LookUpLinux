param([ValidateSet('Burst')][string]$Action='Burst')
$ErrorActionPreference='Stop'
$ownedVm='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
$ownedVBox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
$ownedInfo=& $ownedVBox showvminfo $ownedVm --machinereadable
if ($LASTEXITCODE -ne 0 -or $ownedInfo -notcontains 'UUID="cf207909-94b5-4b49-8bd8-ccff973c1dc8"' -or
    $ownedInfo -notcontains 'name="lookup-gsd-07"' -or $ownedInfo -notcontains 'VMState="running"' -or
    $ownedInfo -notcontains '"SATA-ImageUUID-0-0"="2712d710-daaa-449c-843d-d570091127bc"' -or
    $ownedInfo -notcontains 'macaddress1="080027A05376"' -or
    $ownedInfo -notcontains 'Forwarding(0)="lookup-gsd-07-ssh,tcp,127.0.0.1,2227,,22"') {throw 'Owned clone mismatch'}
$ownedManager=New-Object -ComObject VirtualBox.VirtualBox
$ownedSession=New-Object -ComObject VirtualBox.Session
try {
    $ownedManager.FindMachine($ownedVm).LockMachine($ownedSession,1)
    $ownedKeyboard=$ownedSession.Console.Keyboard
    $ownedWatch=[Diagnostics.Stopwatch]::StartNew()
    for ($ownedIndex=0; $ownedIndex -lt 10; $ownedIndex++) {
        while ($ownedWatch.Elapsed.TotalMilliseconds -lt $ownedIndex*50) {Start-Sleep -Milliseconds 1}
        $ownedSent=$ownedKeyboard.PutScancodes([int[]](224,91,42,18,146,170,224,219))
        if ($ownedSent -ne 8) {throw 'Physical burst injection incomplete'}
    }
} finally {if ($ownedSession.State -eq 1) {$ownedSession.UnlockMachine()}}
