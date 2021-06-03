$crawler_program = Get-Process -Name "main" -ErrorAction SilentlyContinue
$browsers = Get-Process -Name "Chrome" -ErrorAction SilentlyContinue

if (-Not $crawler_program) {
    if ($browsers) {
        $browsers.CloseMainWindow()
        Start-Sleep 5
        if (-Not $browsers) {
            $browsers | Stop-Process -Force
        }
    }
    Set-Location -Path "C:\Users\admin\Desktop"
    Start-Process -FilePath "main.exe" -WorkingDirectory "C:\Users\admin\Desktop"
}