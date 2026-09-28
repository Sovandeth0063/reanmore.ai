# PowerShell script to stop microservices listening on 9000-9003 and frontend on 5173
$ports = @(9000, 9001, 9002, 9003, 5173)

foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            $pidToKill = $c.OwningProcess
            if ($pidToKill -gt 0) {
                Write-Host "Stopping process PID $pidToKill listening on port $port..." -ForegroundColor Yellow
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        Write-Host "Port $port is already clear." -ForegroundColor Gray
    }
}
Write-Host "All services stopped." -ForegroundColor Green
