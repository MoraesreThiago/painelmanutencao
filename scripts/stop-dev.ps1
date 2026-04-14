$ports = 8000, 3000, 3001

foreach ($port in $ports) {
    $line = netstat -ano | Select-String ":$port" | Select-Object -First 1
    if (-not $line) {
        Write-Output "Nenhum processo encontrado na porta $port."
        continue
    }

    $fields = ($line -split "\s+") | Where-Object { $_ }
    $processId = [int]$fields[-1]

    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Output "Processo $processId encerrado na porta $port."
    }
    catch {
        Write-Output "Nao foi possivel encerrar o processo $processId na porta ${port}: $($_.Exception.Message)"
    }
}
