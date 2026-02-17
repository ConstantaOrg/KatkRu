# PowerShell скрипт нагрузочного тестирования для Nginx + API stack

param(
    [string]$TargetHost = "localhost",
    [int]$TargetPort = 80
)

$BaseUrl = "http://${TargetHost}:${TargetPort}"
$TestsPassed = 0
$TestsFailed = 0

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Нагрузочное тестирование Nginx Stack" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Target: $BaseUrl`n" -ForegroundColor Cyan

function Test-Request {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedCode,
        [hashtable]$Headers = @{}
    )
    
    Write-Host "Тест: $Name... " -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -Headers $Headers -UseBasicParsing -ErrorAction SilentlyContinue
        $code = $response.StatusCode
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
    }
    
    if ($code -eq $ExpectedCode) {
        Write-Host "✓ (HTTP $code)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ (Ожидали $ExpectedCode, получили $code)" -ForegroundColor Red
        return $false
    }
}

function Send-MassRequests {
    param(
        [string]$Url,
        [int]$Count,
        [hashtable]$Headers = @{}
    )
    
    $success = 0
    $rateLimited = 0
    $errors = 0
    
    for ($i = 1; $i -le $Count; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -Headers $Headers -UseBasicParsing -ErrorAction SilentlyContinue
            $code = $response.StatusCode
        } catch {
            $code = $_.Exception.Response.StatusCode.value__
        }
        
        switch ($code) {
            { $_ -in 200, 404 } { $success++ }
            429 { $rateLimited++ }
            default { $errors++ }
        }
    }
    
    return @{
        Success = $success
        RateLimited = $rateLimited
        Errors = $errors
    }
}

# === 1. Базовые проверки ===
Write-Host "`n=== 1. Базовые проверки доступности ===" -ForegroundColor Yellow
Write-Host ""

if (Test-Request "Nginx работает" "$BaseUrl/" 404) { $TestsPassed++ } else { $TestsFailed++ }

# === 2. PUBLIC API ===
Write-Host "`n=== 2. Тестирование PUBLIC API ===" -ForegroundColor Yellow
Write-Host ""

if (Test-Request "PUBLIC API доступен" "$BaseUrl/api/v1/public/test" 404) { $TestsPassed++ } else { $TestsFailed++ }

Write-Host "Тест: Rate limiting на PUBLIC API (30 запросов)... " -NoNewline
$result = Send-MassRequests "$BaseUrl/api/v1/public/test" 30
if ($result.RateLimited -gt 0) {
    Write-Host "✓ (Успешно: $($result.Success), Rate limited: $($result.RateLimited), Ошибки: $($result.Errors))" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "✗ (Rate limiting не сработал! Все $($result.Success) запросов прошли)" -ForegroundColor Red
    $TestsFailed++
}

# === 3. PRIVATE API ===
Write-Host "`n=== 3. Тестирование PRIVATE API ===" -ForegroundColor Yellow
Write-Host ""

if (Test-Request "PRIVATE API без cookies" "$BaseUrl/api/v1/private/test" 401) { $TestsPassed++ } else { $TestsFailed++ }

$headers = @{
    "Cookie" = "access_token=test123; refresh_token=test456"
}
if (Test-Request "PRIVATE API с cookies" "$BaseUrl/api/v1/private/test" 404 $headers) { $TestsPassed++ } else { $TestsFailed++ }

Write-Host "Тест: Rate limiting на PRIVATE API (30 запросов с cookies)... " -NoNewline
$result = Send-MassRequests "$BaseUrl/api/v1/private/test" 30 $headers
if ($result.RateLimited -gt 0) {
    Write-Host "✓ (Успешно: $($result.Success), Rate limited: $($result.RateLimited), Ошибки: $($result.Errors))" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "✗ (Rate limiting не сработал! Все $($result.Success) запросов прошли)" -ForegroundColor Red
    $TestsFailed++
}

# === 4. SERVER API ===
Write-Host "`n=== 4. Тестирование SERVER API ===" -ForegroundColor Yellow
Write-Host ""

if (Test-Request "SERVER API заблокирован снаружи" "$BaseUrl/api/v1/server/test" 401) { $TestsPassed++ } else { $TestsFailed++ }

# === 5. Ban system ===
Write-Host "`n=== 5. Тестирование системы банов ===" -ForegroundColor Yellow
Write-Host ""

$banMonitor = docker ps --filter "name=katk_ban_monitor" --format "{{.Names}}"
if ($banMonitor) {
    Write-Host "✓ Ban monitor контейнер запущен" -ForegroundColor Green
    $TestsPassed++
    
    $iptablesCheck = docker exec katk_ban_monitor iptables -L KATK_BANLIST -n 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ iptables цепочка KATK_BANLIST существует" -ForegroundColor Green
        $TestsPassed++
    } else {
        Write-Host "✗ iptables цепочка KATK_BANLIST не найдена" -ForegroundColor Red
        $TestsFailed++
    }
    
    Write-Host "`nТекущие баны:" -ForegroundColor Cyan
    docker exec katk_ban_monitor /app/scripts/manage_bans.sh list 2>$null
} else {
    Write-Host "✗ Ban monitor контейнер не запущен" -ForegroundColor Red
    $TestsFailed++
}

# === 6. Стресс-тест ===
Write-Host "`n=== 6. Стресс-тест (100 запросов) ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Отправка 100 запросов... " -NoNewline
$startTime = Get-Date
$result = Send-MassRequests "$BaseUrl/api/v1/public/test" 100
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host "Завершено" -ForegroundColor Green
Write-Host "  Время выполнения: $([math]::Round($duration, 2))s"
Write-Host "  Успешных запросов: $($result.Success)"
Write-Host "  Rate limited (429): $($result.RateLimited)"
Write-Host "  Ошибок: $($result.Errors)"
Write-Host "  RPS: $([math]::Round(100 / $duration, 2))"

if ($result.RateLimited -gt 50) {
    Write-Host "✓ Rate limiting работает эффективно" -ForegroundColor Green
    $TestsPassed++
} else {
    Write-Host "⚠ Rate limiting пропустил слишком много запросов" -ForegroundColor Yellow
}

# === 7. Логи ===
Write-Host "`n=== 7. Проверка логов nginx ===" -ForegroundColor Yellow
Write-Host ""

if (Test-Path "logs/access.log") {
    Write-Host "✓ Access log существует" -ForegroundColor Green
    Write-Host "  Последние 5 записей:"
    Get-Content "logs/access.log" -Tail 5 | ForEach-Object { Write-Host "    $_" }
    $TestsPassed++
} else {
    Write-Host "✗ Access log не найден" -ForegroundColor Red
    $TestsFailed++
}

# === 8. Производительность ===
Write-Host "`n=== 8. Анализ производительности ===" -ForegroundColor Yellow
Write-Host ""

Write-Host "Измерение средней задержки (10 запросов)... " -NoNewline
$totalTime = 0
for ($i = 1; $i -le 10; $i++) {
    $start = Get-Date
    try {
        Invoke-WebRequest -Uri "$BaseUrl/api/v1/public/test" -Method Get -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
    } catch {}
    $end = Get-Date
    $totalTime += ($end - $start).TotalSeconds
}
$avgTime = $totalTime / 10

Write-Host "$([math]::Round($avgTime, 3))s" -ForegroundColor Green

if ($avgTime -lt 0.1) {
    Write-Host "✓ Отличная производительность (< 100ms)" -ForegroundColor Green
    $TestsPassed++
} elseif ($avgTime -lt 0.5) {
    Write-Host "⚠ Приемлемая производительность (< 500ms)" -ForegroundColor Yellow
    $TestsPassed++
} else {
    Write-Host "✗ Медленная производительность (> 500ms)" -ForegroundColor Red
    $TestsFailed++
}

# === Результаты ===
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "Результаты тестирования" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Пройдено: " -NoNewline
Write-Host $TestsPassed -ForegroundColor Green
Write-Host "Провалено: " -NoNewline
Write-Host $TestsFailed -ForegroundColor Red
Write-Host "Всего: $($TestsPassed + $TestsFailed)"

if ($TestsFailed -eq 0) {
    Write-Host "`n✓ Все тесты пройдены успешно!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Некоторые тесты провалились" -ForegroundColor Red
    exit 1
}
