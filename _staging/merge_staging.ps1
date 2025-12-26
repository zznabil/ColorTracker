$ErrorActionPreference = "Stop"
$root = "C:\Users\Admin\Documents\ColorTracker"
$staging = "C:\Users\Admin\Documents\ColorTracker\_staging"
$branchesDir = "C:\Users\Admin\Documents\ColorTracker\branches"

# 1. Clean and Create Staging
Write-Host "Creating Staging Environment..."
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Path $staging | Out-Null

# 2. Clone Root to Staging (Exclude .git, branches, logs, cache)
Write-Host "Cloning Root to Staging..."
Get-ChildItem $root -Exclude "_staging", "branches", ".git", ".pytest_cache", "__pycache__", "logs", ".crush", ".trae", ".serena" | Copy-Item -Destination $staging -Recurse -Force

# 3. Define Branch Order (Oldest -> Newest)
$branches = @(
    "jules_session_9615231172239414088", # 8:21:30 PM
    "jules_session_8740257305312548174", # 8:21:33 PM
    "jules_session_8974379022554920590", # 8:21:36 PM
    "jules_session_711382254875663711",  # 8:21:39 PM
    "jules_session_15843490540246739593", # 8:21:42 PM
    "jules_session_8351364434548740962", # 8:21:45 PM
    "jules_session_11259048994863219544", # 8:21:48 PM
    "jules_session_16036241064796884863", # 8:21:50 PM
    "jules_session_5134313519030389649"   # 8:21:54 PM
)

# 4. Overlay Branches
foreach ($branch in $branches) {
    $branchPath = Join-Path $branchesDir $branch
    if (Test-Path $branchPath) {
        Write-Host "Overlaying Branch: $branch"
        Copy-Item -Path "$branchPath\*" -Destination $staging -Recurse -Force
    } else {
        Write-Warning "Branch not found: $branch"
    }
}

Write-Host "Staging Merge Complete."
