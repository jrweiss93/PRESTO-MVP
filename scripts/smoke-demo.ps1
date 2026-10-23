# Smoke test de la demo desplegada.
#
#   .\scripts\smoke-demo.ps1 -ApiUrl https://api.mi-dominio.com -FrontUrl https://mi-front.vercel.app
#
# Verifica salud, modo demo, CORS con credenciales, login, cookie de refresh,
# Presti y que el front (incluidas las rutas profundas) responda.

param(
    [Parameter(Mandatory = $true)][string]$ApiUrl,
    [Parameter(Mandatory = $true)][string]$FrontUrl,
    [string]$Email = 'ana@presto.demo',
    [string]$Password = 'Presto123!'
)

$ErrorActionPreference = 'Stop'
$ApiUrl = $ApiUrl.TrimEnd('/')
$FrontUrl = $FrontUrl.TrimEnd('/')
$script:failures = 0

function Pass($name, $detail = '') {
    Write-Host "OK   $name $detail" -ForegroundColor Green
}

function Fail($name, $detail = '') {
    $script:failures++
    Write-Host "FAIL $name $detail" -ForegroundColor Red
}

function Get-StatusAndBody($uri, $method = 'GET', $headers = @{}, $body = $null, $session = $null) {
    $params = @{
        Uri             = $uri
        Method          = $method
        Headers         = $headers
        UseBasicParsing = $true
        TimeoutSec      = 90
    }
    if ($body) { $params['Body'] = $body; $params['ContentType'] = 'application/json' }
    if ($session) { $params['WebSession'] = $session }
    try {
        $response = Invoke-WebRequest @params
        return @{ Status = [int]$response.StatusCode; Body = $response.Content; Headers = $response.Headers; Cookies = $response.Headers['Set-Cookie'] }
    }
    catch {
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
            return @{ Status = $status; Body = ''; Headers = @{}; Cookies = $null }
        }
        return @{ Status = 0; Body = ''; Headers = @{}; Cookies = $null }
    }
}

Write-Host "API:   $ApiUrl" -ForegroundColor Cyan
Write-Host "Front: $FrontUrl" -ForegroundColor Cyan
Write-Host ''

# El plan free de Render duerme por inactividad: la primera peticion puede
# tardar un minuto. Se despierta antes de medir para no reportar un falso fallo.
for ($i = 1; $i -le 3; $i++) {
    $warm = Get-StatusAndBody "$ApiUrl/health/"
    if ($warm.Status -eq 200) { break }
    Write-Host "Despertando la API... (intento $i)" -ForegroundColor DarkYellow
}

# 1. Salud
$health = Get-StatusAndBody "$ApiUrl/health/"
if ($health.Status -eq 200) { Pass 'health' } else { Fail 'health' "(status $($health.Status))" }

# 2. Modo demo
$meta = Get-StatusAndBody "$ApiUrl/api/v1/meta/"
if ($meta.Status -eq 200) {
    $data = $meta.Body | ConvertFrom-Json
    if ($data.mode -eq 'demo' -and $data.simulated_money -eq $true) {
        Pass 'modo demo' '(dinero simulado)'
    }
    else {
        Fail 'modo demo' "(mode=$($data.mode), simulated_money=$($data.simulated_money))"
    }
}
else { Fail 'meta' "(status $($meta.Status))" }

# 3. CORS con credenciales para el origen del front
$cors = Get-StatusAndBody "$ApiUrl/api/v1/ledger/accounts/" -method 'OPTIONS' -headers @{
    Origin                        = $FrontUrl
    'Access-Control-Request-Method'  = 'POST'
    'Access-Control-Request-Headers' = 'authorization,content-type,idempotency-key'
}
if ($cors.Status -eq 200) {
    $allowOrigin = $cors.Headers['Access-Control-Allow-Origin']
    $allowCred = $cors.Headers['Access-Control-Allow-Credentials']
    $allowHeaders = [string]$cors.Headers['Access-Control-Allow-Headers']
    if ($allowOrigin -eq $FrontUrl -and $allowCred -eq 'true' -and $allowHeaders -match 'idempotency-key') {
        Pass 'CORS' '(origen, credenciales e Idempotency-Key)'
    }
    else {
        Fail 'CORS' "(origin=$allowOrigin, credentials=$allowCred, headers=$allowHeaders)"
    }
}
else { Fail 'CORS' "(status $($cors.Status))" }

# 4. Login de un usuario de demo (guarda la cookie de refresh)
$loginBody = @{ email = $Email; password = $Password } | ConvertTo-Json -Compress
$access = $null
$authSession = $null
$loginCookie = ''
try {
    $login = Invoke-WebRequest -Uri "$ApiUrl/api/v1/auth/login/" -Method 'POST' `
        -ContentType 'application/json' -Body $loginBody -SessionVariable authSession `
        -UseBasicParsing -TimeoutSec 30
    if ($login.StatusCode -eq 200) {
        $access = ($login.Content | ConvertFrom-Json).access
        $loginCookie = [string]$login.Headers['Set-Cookie']
        Pass 'login demo' $Email
    }
    else { Fail 'login demo' "(status $($login.StatusCode))" }
}
catch { Fail 'login demo' $_.Exception.Message }

# 5. Cookie httpOnly de refresh + renovación (con la misma sesión)
if ($loginCookie -match 'presto_refresh') {
    if ($loginCookie -match 'HttpOnly') { Pass 'cookie httpOnly' }
    else { Fail 'cookie httpOnly' '(la cookie no vino con HttpOnly)' }

    try {
        $refresh = Invoke-WebRequest -Uri "$ApiUrl/api/v1/auth/token/refresh/" -Method 'POST' `
            -ContentType 'application/json' -Body '{}' -WebSession $authSession `
            -UseBasicParsing -TimeoutSec 30
        if ($refresh.StatusCode -eq 200) { Pass 'refresh con cookie httpOnly' }
        else { Fail 'refresh con cookie httpOnly' "(status $($refresh.StatusCode))" }
    }
    catch { Fail 'refresh con cookie httpOnly' $_.Exception.Message }
}
else { Fail 'cookie httpOnly' '(el login no devolvió presto_refresh)' }

# 6. Presti con la API real
if ($access) {
    $market = Get-StatusAndBody "$ApiUrl/api/v1/assistant/market/" -headers @{ Authorization = "Bearer $access" }
    if ($market.Status -eq 200) { Pass 'Presti mercado' } else { Fail 'Presti mercado' "(status $($market.Status))" }

    $chatBody = @{ message = 'cual es mi saldo' } | ConvertTo-Json -Compress
    $chat = Get-StatusAndBody "$ApiUrl/api/v1/assistant/chat/" -method 'POST' -headers @{ Authorization = "Bearer $access" } -body $chatBody
    if ($chat.Status -eq 200) { Pass 'Presti chat' } else { Fail 'Presti chat' "(status $($chat.Status))" }
}

# 7. Front: home y ruta profunda (rewrite de SPA)
foreach ($path in @('/', '/legal', '/asistente')) {
    $front = Get-StatusAndBody "$FrontUrl$path"
    if ($front.Status -eq 200) { Pass "front $path" } else { Fail "front $path" "(status $($front.Status))" }
}

Write-Host ''
if ($script:failures -eq 0) {
    Write-Host 'Smoke test OK: la demo está lista para mostrar.' -ForegroundColor Green
    exit 0
}
Write-Host "$($script:failures) chequeo(s) fallaron." -ForegroundColor Red
exit 1
