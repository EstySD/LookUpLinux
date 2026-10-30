param(
    [ValidateSet('Check','Keys','Pointer','Relative','Screenshot','Burst')][string]$Action='Check',
    [string]$Codes,[int]$X=0,[int]$Y=0,[int]$Buttons=0,[string]$Output
)
$ErrorActionPreference='Stop'
$hardeningVm='cf207909-94b5-4b49-8bd8-ccff973c1dc8'
$hardeningVBox='C:/Program Files/Oracle/VirtualBox/VBoxManage.exe'
$hardeningInfo=& $hardeningVBox showvminfo $hardeningVm --machinereadable
if ($LASTEXITCODE -ne 0 -or $hardeningInfo -notcontains 'name="lookup-gsd-07"' -or
    $hardeningInfo -notcontains '"SATA-ImageUUID-0-0"="2712d710-daaa-449c-843d-d570091127bc"' -or
    -not ($hardeningInfo | Select-String -SimpleMatch 'lookup-gsd-07\\lookup-gsd-07.vdi')) { throw 'Owned full clone attachment mismatch' }
# Reuse only UUID-guarded physical input/framebuffer controls, never old Native.
if ($Action -eq 'Burst') {
    & "$PSScriptRoot/check_package_vm.ps1" -Action Check
    if ($LASTEXITCODE -ne 0) { throw 'Owned clone guard failed' }
    $hardeningManager=New-Object -ComObject VirtualBox.VirtualBox
    $hardeningMachine=$hardeningManager.FindMachine($hardeningVm)
    $hardeningSession=New-Object -ComObject VirtualBox.Session
    try {
        $hardeningMachine.LockMachine($hardeningSession,1)
        $hardeningKeyboard=$hardeningSession.Console.Keyboard
        $hardeningWatch=[Diagnostics.Stopwatch]::StartNew()
        for ($hardeningIndex=0; $hardeningIndex -lt 10; $hardeningIndex++) {
            while ($hardeningWatch.Elapsed.TotalMilliseconds -lt $hardeningIndex*50) { Start-Sleep -Milliseconds 1 }
            $hardeningSent=$hardeningKeyboard.PutScancodes([int[]](224,91,42,18,146,170,224,219))
            if ($hardeningSent -ne 8) { throw 'Physical burst injection incomplete' }
        }
    } finally { if ($hardeningSession.State -eq 1) { $hardeningSession.UnlockMachine() } }
    exit 0
}
& "$PSScriptRoot/check_package_vm.ps1" -Action $Action -Codes $Codes -X $X -Y $Y -Buttons $Buttons -Output $Output
exit $LASTEXITCODE
