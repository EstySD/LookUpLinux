Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type 'using System; using System.Runtime.InteropServices; public static class FixtureDpi { [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr value); }'
[void][FixtureDpi]::SetThreadDpiAwarenessContext([IntPtr]::new(-4))
$form = [System.Windows.Forms.Form]::new()
$form.Text = 'LookUpLinux controlled OCR probe'
$form.WindowState = 'Maximized'
$form.BackColor = [Drawing.Color]::White
$form.TopMost = $true
$label = [System.Windows.Forms.Label]::new()
$label.Text = 'The children watched the bright river.'
$label.Font = [Drawing.Font]::new('Arial', 26)
$label.ForeColor = [Drawing.Color]::Black
$label.Location = [Drawing.Point]::new(100, 180)
$label.AutoSize = $true
$form.Controls.Add($label)
$form.Show()
[System.Windows.Forms.Application]::DoEvents()
$origin = $label.PointToScreen([Drawing.Point]::new(0,0))
$points = @{}
$flags = [Windows.Forms.TextFormatFlags]::NoPadding -bor [Windows.Forms.TextFormatFlags]::SingleLine
foreach ($word in @('children','bright')) {
    $index = $label.Text.IndexOf($word,[StringComparison]::Ordinal)
    $before = [Windows.Forms.TextRenderer]::MeasureText($label.Text.Substring(0,$index),$label.Font,[Drawing.Size]::new(10000,10000),$flags)
    $size = [Windows.Forms.TextRenderer]::MeasureText($word,$label.Font,[Drawing.Size]::new(10000,10000),$flags)
    $points[$word] = @{ x=($origin.X+$before.Width+[int]($size.Width/2)); y=($origin.Y+[int]($label.Height/2)) }
}
$record = @{ process_id=$PID; handle=$form.Handle.ToInt64(); x=$origin.X; y=$origin.Y; points=$points; coordinate_space='physical pixels; per-monitor-aware thread' }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'fixture-layout.json'), ($record | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
[System.Windows.Forms.Application]::Run($form)
$form.Dispose()
