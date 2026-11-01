$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class LookupperProbeInput {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int command);
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr value);
    [DllImport("user32.dll")] public static extern void keybd_event(byte key, byte scan, uint flags, UIntPtr extra);
}
'@
[void][LookupperProbeInput]::SetThreadDpiAwarenessContext([IntPtr]::new(-4))

function Condition($property, $value) {
    [System.Windows.Automation.PropertyCondition]::new($property, $value)
}
function Find-Name($parent, $name) {
    $parent.FindFirst([System.Windows.Automation.TreeScope]::Descendants,
        (Condition ([System.Windows.Automation.AutomationElement]::NameProperty) $name))
}
function Pump($milliseconds) {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    while ($clock.ElapsedMilliseconds -lt $milliseconds) {
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 30
    }
}
function Hotkey {
    [LookupperProbeInput]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)
    [LookupperProbeInput]::keybd_event(0x51, 0, 0, [UIntPtr]::Zero)
    [LookupperProbeInput]::keybd_event(0x51, 0, 2, [UIntPtr]::Zero)
    [LookupperProbeInput]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
}
function Snapshot {
    $windows = [System.Windows.Automation.AutomationElement]::RootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Children, $processCondition)
    $result = @()
    foreach ($window in $windows) {
        $nodes = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition)
        $rows = @()
        for ($index = 0; $index -lt [Math]::Min(400, $nodes.Count); $index++) {
            $node = $nodes.Item($index)
            $current = $node.Current
            # Retain synthetic text and structural controls, never existing library entries.
            $name = $current.Name
            if ($name -match 'children|bright|river|watched|дет[ьи]|реб[её]н|ярк|рек[аиу]|The children' -or
                ($window.Current.Name -eq 'Lookupper Overlay' -and $name -match 'ошиб|загруз|не найден|распозн|сеть|доступ' -and $name -notmatch '@|https?://|Bearer') -or
                ($current.ControlType.ProgrammaticName -in @('ControlType.Button','ControlType.TabItem') -and
                $name -match '^(Закрыть|Сохранить|Перевод|Словар|Настройки|Looktionary|Контекст|Всплывающий)')) {
                $rows += [pscustomobject]@{ type=$current.ControlType.ProgrammaticName; name=$name; id=$current.AutomationId }
            }
        }
        $result += [pscustomobject]@{ window=$window.Current.Name; descendants=$nodes.Count; examined=[Math]::Min(400,$nodes.Count); controls=$rows }
    }
    return $result
}

$target = Get-Process -Name Lookupper | Select-Object -First 1
if (-not $target) { throw 'Lookupper must already be running.' }
$processCondition = Condition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty) ([int]$target.Id)
$main = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
    [System.Windows.Automation.TreeScope]::Children, $processCondition)
(Find-Name $main 'Настройки').GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
Pump 300
$autoSaveCondition = [System.Windows.Automation.AndCondition]::new(
    (Condition ([System.Windows.Automation.AutomationElement]::NameProperty) 'Сохранять слова автоматически'),
    (Condition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty) ([System.Windows.Automation.ControlType]::Button)))
$autoSave = $main.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $autoSaveCondition)
$toggle = $autoSave.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
$originalState = $toggle.Current.ToggleState
if ($originalState -eq [System.Windows.Automation.ToggleState]::Indeterminate) { throw 'Unknown autosave state.' }
$language = $main.FindFirst([System.Windows.Automation.TreeScope]::Descendants,
    (Condition ([System.Windows.Automation.AutomationElement]::AutomationIdProperty) 'LanguagesComboBox'))
$languageNames = @($language.GetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern).Current.GetSelection() | ForEach-Object { $_.Current.Name })
$record = [ordered]@{ timestamp_utc=[DateTime]::UtcNow.ToString('o'); authority='shell-windows-uia'; target_version='2.0.6.0'; synthetic_text='The children watched the bright river.'; original_autosave=$originalState.ToString(); recognition_language=$languageNames; coordinate_space='physical pixels; per-monitor-aware thread'; probes=@(); status='started'; limitations=@('Filtered UI Automation names, not a native call trace.', 'Screenshots clipped to the controlled fixture; no user library values retained.', 'Existing hotkey Alt+Q required; observed in settings before the run.', 'observation_after_ms is a fixed observation delay, not time to first result.') }
$fixture = $null
try {
    if ($originalState -eq [System.Windows.Automation.ToggleState]::On) { $toggle.Toggle(); Pump 300 }
    if ($toggle.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::Off) { throw 'Could not disable autosave.' }
    # The source window has its own process; app focus/freeze must not pause the observer.
    $fixture = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList @('-NoProfile','-STA','-File',('"' + (Join-Path $PSScriptRoot 'fixture-scene.ps1') + '"')) -WindowStyle Hidden -PassThru
    $layout = $null
    $launchClock = [Diagnostics.Stopwatch]::StartNew()
    while ($launchClock.ElapsedMilliseconds -lt 5000) {
        $layoutFile = Join-Path $PSScriptRoot 'fixture-layout.json'
        if (Test-Path -LiteralPath $layoutFile) {
            $candidate = Get-Content -LiteralPath $layoutFile -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($candidate.process_id -eq $fixture.Id) { $layout = $candidate; break }
        }
        Pump 100
    }
    if (-not $layout) { throw 'Fixture did not publish its own window layout.' }
    $fixtureHandle = [IntPtr]::new([long]$layout.handle)
    foreach ($point in @(@{word='children'}, @{word='bright'})) {
        [void][LookupperProbeInput]::ShowWindow($fixtureHandle,3)
        [void][LookupperProbeInput]::SetForegroundWindow($fixtureHandle)
        Pump 300
        if ([LookupperProbeInput]::GetForegroundWindow() -ne $fixtureHandle) {
            [System.Windows.Automation.AutomationElement]::FromHandle($fixtureHandle).SetFocus()
            Pump 200
        }
        if ([LookupperProbeInput]::GetForegroundWindow() -ne $fixtureHandle) { throw 'Fixture did not receive foreground; hotkey not sent.' }
        $wordPoint = $layout.points.PSObject.Properties[$point.word].Value
        [System.Windows.Forms.Cursor]::Position = [System.Drawing.Point]::new($wordPoint.x,$wordPoint.y)
        $clock = [Diagnostics.Stopwatch]::StartNew()
        Hotkey
        Pump 7000
        $clip = [Drawing.Rectangle]::Intersect(
            [Drawing.Rectangle]::new(($layout.x - 20), ($layout.y - 40), 1050, 600),
            [System.Windows.Forms.Screen]::FromPoint([Drawing.Point]::new($layout.x,$layout.y)).Bounds)
        $bitmap = [Drawing.Bitmap]::new($clip.Width,$clip.Height)
        $graphics = [Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($clip.Location,[Drawing.Point]::Empty,$clip.Size)
            $bitmap.Save((Join-Path $PSScriptRoot ('runtime-' + $point.word + '.png')),[Drawing.Imaging.ImageFormat]::Png)
        } finally { $graphics.Dispose(); $bitmap.Dispose() }
        $record.probes += [pscustomobject]@{ intended_word=$point.word; cursor_screen_x=$wordPoint.x; cursor_screen_y=$wordPoint.y; observation_after_ms=$clock.ElapsedMilliseconds; screenshot=('runtime-' + $point.word + '.png'); windows=@(Snapshot) }
        [LookupperProbeInput]::keybd_event(0x1b,0,0,[UIntPtr]::Zero)
        [LookupperProbeInput]::keybd_event(0x1b,0,2,[UIntPtr]::Zero)
        Pump 400
    }
    $record.status = 'observed'
} catch {
    $record.status = 'failed'
    $record.error = $_.Exception.Message
} finally {
    [LookupperProbeInput]::keybd_event(0x51,0,2,[UIntPtr]::Zero)
    [LookupperProbeInput]::keybd_event(0x12,0,2,[UIntPtr]::Zero)
    [LookupperProbeInput]::keybd_event(0x1b,0,0,[UIntPtr]::Zero)
    [LookupperProbeInput]::keybd_event(0x1b,0,2,[UIntPtr]::Zero)
    if ($fixture) {
        [void]$fixture.CloseMainWindow()
        if (-not $fixture.WaitForExit(2000)) { $fixture.Kill(); $fixture.WaitForExit() }
    }
    [void][LookupperProbeInput]::SetForegroundWindow($target.MainWindowHandle)
    (Find-Name $main 'Настройки').GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
    Pump 300
    $autoSave = $main.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $autoSaveCondition)
    $restore = $autoSave.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
    if ($restore.Current.ToggleState -ne $originalState) { $restore.Toggle(); Pump 300 }
    $record.autosave_restored = ($restore.Current.ToggleState -eq $originalState)
    $json = $record | ConvertTo-Json -Depth 9
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'runtime-workflow.json'), $json, [Text.UTF8Encoding]::new($false))
}
if (-not $record.autosave_restored) { throw 'Autosave setting was not restored.' }
$record | ConvertTo-Json -Depth 9 -Compress
