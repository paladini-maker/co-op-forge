[CmdletBinding()]
param(
    [string]$RepositoryUrl = "https://github.com/paladini-maker/co-op-forge.git"
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & git -C $WorkingDirectory @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git -C `"$WorkingDirectory`" $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git was not found. Install Git for Windows and reopen PowerShell."
}
if (-not (Test-Path -LiteralPath "index.html" -PathType Leaf) -or -not (Test-Path -LiteralPath "README.md" -PathType Leaf)) {
    throw "Run this script from the extracted co-op-forge-github project root."
}

$sourceRoot = (Get-Location).Path
python scripts/validate_project.py
if ($LASTEXITCODE -ne 0) { throw "Project validation failed; nothing was pushed." }

if (Test-Path -LiteralPath (Join-Path $sourceRoot ".git") -PathType Container) {
    # For an existing local checkout, require an exact remote match and never rewrite history.
    $origin = (& git -C $sourceRoot remote get-url origin 2>$null)
    if ($LASTEXITCODE -ne 0 -or $origin.Trim() -ne $RepositoryUrl) {
        throw "This folder already contains Git metadata but origin is missing or does not match '$RepositoryUrl'. Clone the intended repo and copy the files instead; no remote was changed."
    }
    $branch = (& git -C $sourceRoot branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $branch -ne "main") {
        throw "Expected branch 'main', found '$branch'. Switch/review branches manually; no branch was renamed."
    }
    $workRoot = $sourceRoot
    $temporaryClone = $false
} else {
    # Clone first so an existing starter README/history is preserved. Then copy the project over it.
    $workRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("co-op-forge-publish-" + [guid]::NewGuid().ToString("N"))
    Invoke-Git -WorkingDirectory ([System.IO.Path]::GetTempPath()) -Arguments @("clone", $RepositoryUrl, $workRoot)
    $temporaryClone = $true
    $localEntries = Get-ChildItem -LiteralPath $sourceRoot -Force | Where-Object { $_.Name -ne ".git" }
    foreach ($entry in $localEntries) {
        Copy-Item -LiteralPath $entry.FullName -Destination $workRoot -Recurse -Force
    }
    $branch = (& git -C $workRoot branch --show-current).Trim()
    if ([string]::IsNullOrWhiteSpace($branch)) {
        Invoke-Git -WorkingDirectory $workRoot -Arguments @("switch", "--orphan", "main")
    } elseif ($branch -ne "main") {
        throw "Remote default branch is '$branch', not 'main'. The cloned folder is at '$workRoot'; no push was attempted."
    }
}

Invoke-Git -WorkingDirectory $workRoot -Arguments @("add", "--all")
$changes = & git -C $workRoot status --porcelain
if ($LASTEXITCODE -ne 0) { throw "Could not inspect staged changes." }
if ($changes) {
    Invoke-Git -WorkingDirectory $workRoot -Arguments @("commit", "-m", "chore: publish Co-Op Forge project")
} else {
    Write-Host "No tracked changes to commit."
}

# A normal push is deliberate: it refuses non-fast-forward updates and never force-overwrites remote history.
Invoke-Git -WorkingDirectory $workRoot -Arguments @("push", "--set-upstream", "origin", "main")
Write-Host "Published to $RepositoryUrl" -ForegroundColor Green
Write-Host "Next: enable Settings > Pages > Build and deployment > GitHub Actions, then inspect the Actions tab."
if ($temporaryClone) {
    Write-Host "The working clone is at: $workRoot"
    Write-Host "Keep it as your checkout or delete it after verifying the remote."
}
