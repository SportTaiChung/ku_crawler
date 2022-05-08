Set-Location "~/Desktop"
$Now = Get-Date -UFormat %s
$LastStatusUpdateTimestamp = (Get-Item ku_crawler.status -ErrorAction Ignore).LastWriteTime | Get-Date -UFormat %s
# 大於五分鐘沒更新狀態，重啟程式
if (($Now - $LastStatusUpdateTimestamp) -gt 300) {
    taskkill.exe /IM leo_main.exe /F
    taskkill.exe /IM chrome.exe /F
    Start-Process leo_main.exe
}
# 自動啟動程式
elseif (-Not(Get-Process -Name leo_main -ErrorAction Ignore)) {
    taskkill.exe /IM chrome.exe /F
    Start-Process leo_main.exe
}
# 清除舊log
Get-ChildItem –Path "." -Name "*.log" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-3)} | Remove-Item
Get-ChildItem –Path "./mapping/" -Name "*.txt" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-3)} | Remove-Item