<#
.SYNOPSIS
    Connects the local Windows host machine as the 'pw-agent' inbound node in Jenkins (localhost:8088).
    Allows Jenkins jobs ('harvest-templates', 'run-e2e-tests', 'historical-dashboard', 'benchmark', 'smoke')
    to execute Pytest and Playwright directly inside the local Windows (.venv) environment and open
    a visible Chromium window on the desktop when HEADED=true.
#>
param(
    [string]$JenkinsUrl = "http://localhost:8088",
    [string]$AgentName  = "pw-agent",
    [string]$AdminUser  = "admin",
    [string]$AdminPass  = "admin123"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$PlaywrightDir = Join-Path $RepoRoot "automation-playwright"
$VenvScripts = Join-Path $PlaywrightDir ".venv\Scripts"
$AgentWorkDir = Join-Path $RepoRoot ".jenkins-agent"

New-Item -ItemType Directory -Force -Path $AgentWorkDir | Out-Null

# 1. Stop the Linux pw-agent container if it is running to prevent node connection collisions
$ErrorActionPreference = "Continue"
$runningContainer = docker ps --filter "name=automation-lab-pw-agent" --format "{{.Names}}" 2>$null
if ($runningContainer) {
    Write-Host "[Windows Agent] Stopping Linux container 'automation-lab-pw-agent' to release the node..." -ForegroundColor Yellow
    docker stop automation-lab-pw-agent | Out-Null
}

# 2. Locate Java 17 or 21 (required by modern Jenkins LTS remoting)
function Find-Java17Or21 {
    $candidates = @(
        "C:\Program Files\Microsoft\jdk-21*\bin\java.exe",
        "C:\Program Files\Microsoft\jdk-17*\bin\java.exe",
        "C:\Program Files\Eclipse Adoptium\jdk-21*\bin\java.exe",
        "C:\Program Files\Eclipse Adoptium\jdk-17*\bin\java.exe",
        "C:\Program Files\Eclipse Adoptium\jre-21*\bin\java.exe",
        "C:\Program Files\Eclipse Adoptium\jre-17*\bin\java.exe",
        "C:\Program Files\Java\jdk-21*\bin\java.exe",
        "C:\Program Files\Java\jdk-17*\bin\java.exe"
    )
    foreach ($pattern in $candidates) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
        if ($found) {
            return $found.FullName
        }
    }
    return "java"
}

$JavaExe = Find-Java17Or21
Write-Host "[Windows Agent] Using Java: $JavaExe" -ForegroundColor Cyan

# Verify major Java version (use cmd /c to avoid NativeCommandError on stderr in PowerShell 5.1)
$verOutput = cmd /c "`"$JavaExe`" -version 2>&1" | Out-String
if ($verOutput -match 'version "(1\.8|9|10|11)\.') {
    Write-Host "`n[ERROR] Detected Java 11 or lower ($($Matches[0])). Jenkins LTS agent requires Java 17 or Java 21." -ForegroundColor Red
    Write-Host "Install Java 21 in PowerShell by running:" -ForegroundColor Yellow
    Write-Host "    winget install Microsoft.OpenJDK.21" -ForegroundColor Green
    Write-Host "and re-run this script.`n"
    exit 1
}
$ErrorActionPreference = "Stop"

# 3. Activate Python .venv in the agent PATH (checks automation-playwright\.venv first, then root .venv)
if (-not (Test-Path $VenvScripts)) {
    $RootVenvScripts = Join-Path $RepoRoot ".venv\Scripts"
    if (Test-Path $RootVenvScripts) {
        $VenvScripts = $RootVenvScripts
    } else {
        Write-Host "[ERROR] Virtual environment not found at: $VenvScripts or $RootVenvScripts" -ForegroundColor Red
        exit 1
    }
}
$env:PATH = "$VenvScripts;$env:PATH"
$env:PLAYWRIGHT_DIR = $PlaywrightDir
$env:PYTHONIOENCODING = "utf-8"

$pyVer = cmd /c "`"$VenvScripts\python.exe`" --version 2>&1" | Out-String
Write-Host "[Windows Agent] PLAYWRIGHT_DIR = $env:PLAYWRIGHT_DIR" -ForegroundColor Cyan
Write-Host "[Windows Agent] Active Python  = $($pyVer.Trim())" -ForegroundColor Cyan

# 4. Download agent.jar from the Jenkins Controller container
$AgentJar = Join-Path $AgentWorkDir "agent.jar"
Write-Host "[Windows Agent] Downloading agent.jar from $JenkinsUrl/jnlpJars/agent.jar ..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "$JenkinsUrl/jnlpJars/agent.jar" -OutFile $AgentJar -UseBasicParsing

# 5. Retrieve JNLP secret for the pw-agent node
$pair = "${AdminUser}:${AdminPass}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$base64 = [System.Convert]::ToBase64String($bytes)
$headers = @{ Authorization = "Basic $base64" }

$jnlpUrl = "$JenkinsUrl/computer/$AgentName/jenkins-agent.jnlp"
Write-Host "[Windows Agent] Fetching JNLP token from $jnlpUrl ..." -ForegroundColor Cyan
$resp = Invoke-WebRequest -Uri $jnlpUrl -Headers $headers -UseBasicParsing
if ($resp.Content -is [byte[]]) {
    $jnlpXml = [System.Text.Encoding]::UTF8.GetString($resp.Content)
} else {
    $jnlpXml = [string]$resp.Content
}

$Secret = $null
if ($jnlpXml -match '<application-desc[^>]*><argument>([a-f0-9]+)</argument>') {
    $Secret = $Matches[1]
} else {
    # Fallback via Script Console (getJnlpMac) in case the node is still marked as connected
    try {
        $crumbResp = Invoke-RestMethod -Uri "$JenkinsUrl/crumbIssuer/api/json" -Headers $headers -SessionVariable jSession
        $postHeaders = @{
            Authorization = "Basic $base64"
            $crumbResp.crumbRequestField = $crumbResp.crumb
        }
        $mac = Invoke-RestMethod -Uri "$JenkinsUrl/scriptText" -Method Post -Headers $postHeaders -WebSession $jSession -Body @{
            script = "println(jenkins.model.Jenkins.instance.getComputer('$AgentName').getJnlpMac())"
        }
        if ($mac -and $mac.Trim() -match '^[a-f0-9]+$') {
            $Secret = $mac.Trim()
        }
    } catch {}
}

if (-not $Secret) {
    Write-Host "[ERROR] Could not extract JNLP secret for node '$AgentName'. Response: $jnlpXml" -ForegroundColor Red
    exit 1
}

Write-Host "[Windows Agent] Connecting agent '$AgentName' to $JenkinsUrl (WebSocket)..." -ForegroundColor Green
Write-Host "[Windows Agent] Keep this terminal window open while running Jenkins jobs (Ctrl+C to stop).`n" -ForegroundColor Yellow

$ErrorActionPreference = "Continue"
& $JavaExe -jar $AgentJar `
    -url "$JenkinsUrl/" `
    -name $AgentName `
    -secret $Secret `
    -webSocket `
    -workDir $AgentWorkDir
