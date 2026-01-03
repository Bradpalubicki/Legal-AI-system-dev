# Redis Installation Script for Windows
# Legal AI System - Production Readiness

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Redis Installation Helper for Windows" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[WARNING] Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Some installation methods require Administrator privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

Write-Host "Checking available installation methods..." -ForegroundColor Green
Write-Host ""

# Option 1: Check for Docker
Write-Host "[1] Checking for Docker..." -NoNewline
if (Test-CommandExists docker) {
    Write-Host " FOUND" -ForegroundColor Green
    Write-Host "    You can install Redis using Docker with:" -ForegroundColor Cyan
    Write-Host "    docker run -d --name redis-legal-ai -p 6379:6379 redis:7-alpine" -ForegroundColor White
    Write-Host ""
    $hasDocker = $true
} else {
    Write-Host " NOT FOUND" -ForegroundColor Yellow
    $hasDocker = $false
}

# Option 2: Check for WSL
Write-Host "[2] Checking for WSL..." -NoNewline
if (Test-CommandExists wsl) {
    Write-Host " FOUND" -ForegroundColor Green

    # Check if any distributions are installed
    $wslDistros = wsl -l -q 2>&1
    if ($wslDistros -match "Ubuntu|Debian|Alpine") {
        Write-Host "    WSL distributions found. You can install Redis in WSL:" -ForegroundColor Cyan
        Write-Host "    wsl sudo apt update && wsl sudo apt install redis-server -y" -ForegroundColor White
        Write-Host "    wsl sudo service redis-server start" -ForegroundColor White
        Write-Host ""
        $hasWSL = $true
    } else {
        Write-Host "    WSL available but no distributions installed" -ForegroundColor Yellow
        Write-Host "    Install Ubuntu: wsl --install -d Ubuntu" -ForegroundColor White
        Write-Host ""
        $hasWSL = $false
    }
} else {
    Write-Host " NOT FOUND" -ForegroundColor Yellow
    $hasWSL = $false
}

# Option 3: Check for Chocolatey
Write-Host "[3] Checking for Chocolatey..." -NoNewline
if (Test-CommandExists choco) {
    Write-Host " FOUND" -ForegroundColor Green
    Write-Host "    You can install Memurai (Windows Redis) with:" -ForegroundColor Cyan
    Write-Host "    choco install memurai-developer -y" -ForegroundColor White
    Write-Host ""
    $hasChoco = $true
} else {
    Write-Host " NOT FOUND" -ForegroundColor Yellow
    $hasChoco = $false
}

# Option 4: Check for Scoop
Write-Host "[4] Checking for Scoop..." -NoNewline
if (Test-CommandExists scoop) {
    Write-Host " FOUND" -ForegroundColor Green
    Write-Host "    Note: Scoop doesn't have Redis directly" -ForegroundColor Yellow
    Write-Host ""
    $hasScoop = $true
} else {
    Write-Host " NOT FOUND" -ForegroundColor Yellow
    $hasScoop = $false
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Recommended Installation Method" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

if ($hasDocker) {
    Write-Host "[RECOMMENDED] Use Docker (Easiest)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run this command to install Redis:" -ForegroundColor Cyan
    Write-Host "docker run -d --name redis-legal-ai -p 6379:6379 -v redis-data:/data redis:7-alpine redis-server --appendonly yes" -ForegroundColor White
    Write-Host ""
    Write-Host "Then update backend\.env:" -ForegroundColor Cyan
    Write-Host "USE_FAKE_REDIS=false" -ForegroundColor White
    Write-Host ""

} elseif ($hasWSL) {
    Write-Host "[RECOMMENDED] Use WSL + Ubuntu" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run these commands to install Redis:" -ForegroundColor Cyan
    Write-Host "wsl sudo apt update" -ForegroundColor White
    Write-Host "wsl sudo apt install redis-server -y" -ForegroundColor White
    Write-Host "wsl sudo service redis-server start" -ForegroundColor White
    Write-Host ""
    Write-Host "Then update backend\.env:" -ForegroundColor Cyan
    Write-Host "USE_FAKE_REDIS=false" -ForegroundColor White
    Write-Host ""

} elseif ($hasChoco) {
    Write-Host "[RECOMMENDED] Use Chocolatey + Memurai" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run this command to install Memurai:" -ForegroundColor Cyan
    Write-Host "choco install memurai-developer -y" -ForegroundColor White
    Write-Host ""
    Write-Host "Then update backend\.env:" -ForegroundColor Cyan
    Write-Host "USE_FAKE_REDIS=false" -ForegroundColor White
    Write-Host ""

} else {
    Write-Host "[MANUAL INSTALLATION REQUIRED]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "No package managers found. Please use one of these options:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option A: Install Docker Desktop" -ForegroundColor Cyan
    Write-Host "  Download: https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host ""
    Write-Host "Option B: Install WSL + Ubuntu" -ForegroundColor Cyan
    Write-Host "  Run in PowerShell (as Admin): wsl --install -d Ubuntu" -ForegroundColor White
    Write-Host ""
    Write-Host "Option C: Install Memurai (Native Windows Redis)" -ForegroundColor Cyan
    Write-Host "  Download: https://www.memurai.com/get-memurai" -ForegroundColor White
    Write-Host ""
    Write-Host "Option D: Use Redis Cloud (Free Tier)" -ForegroundColor Cyan
    Write-Host "  Sign up: https://redis.com/try-free/" -ForegroundColor White
    Write-Host ""
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "For detailed instructions, see:" -ForegroundColor Cyan
Write-Host "docs\REDIS_SETUP_GUIDE.md" -ForegroundColor White
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Offer to install with available package manager
if ($hasDocker -or $hasWSL -or $hasChoco) {
    Write-Host "Would you like to install Redis now? (Y/N): " -NoNewline -ForegroundColor Green
    $response = Read-Host

    if ($response -eq "Y" -or $response -eq "y") {
        if ($hasDocker) {
            Write-Host ""
            Write-Host "Installing Redis via Docker..." -ForegroundColor Green
            docker run -d --name redis-legal-ai -p 6379:6379 -v redis-data:/data redis:7-alpine redis-server --appendonly yes

            if ($LASTEXITCODE -eq 0) {
                Write-Host "[SUCCESS] Redis installed and running!" -ForegroundColor Green
                Write-Host "Testing connection..." -ForegroundColor Cyan
                Start-Sleep -Seconds 2
                docker exec redis-legal-ai redis-cli ping

                Write-Host ""
                Write-Host "Next step: Update backend\.env" -ForegroundColor Cyan
                Write-Host "Set: USE_FAKE_REDIS=false" -ForegroundColor White
            } else {
                Write-Host "[ERROR] Docker installation failed" -ForegroundColor Red
            }

        } elseif ($hasWSL) {
            Write-Host ""
            Write-Host "Installing Redis via WSL..." -ForegroundColor Green
            wsl sudo apt update
            wsl sudo apt install redis-server -y
            wsl sudo service redis-server start

            Write-Host ""
            Write-Host "Testing connection..." -ForegroundColor Cyan
            wsl redis-cli ping

            Write-Host ""
            Write-Host "Next step: Update backend\.env" -ForegroundColor Cyan
            Write-Host "Set: USE_FAKE_REDIS=false" -ForegroundColor White

        } elseif ($hasChoco) {
            Write-Host ""
            Write-Host "Installing Memurai via Chocolatey..." -ForegroundColor Green
            choco install memurai-developer -y

            if ($LASTEXITCODE -eq 0) {
                Write-Host "[SUCCESS] Memurai installed!" -ForegroundColor Green
                Write-Host ""
                Write-Host "Next step: Update backend\.env" -ForegroundColor Cyan
                Write-Host "Set: USE_FAKE_REDIS=false" -ForegroundColor White
            } else {
                Write-Host "[ERROR] Chocolatey installation failed" -ForegroundColor Red
            }
        }
    } else {
        Write-Host ""
        Write-Host "Installation skipped. You can run this script again later." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Script complete!" -ForegroundColor Green
Write-Host ""
