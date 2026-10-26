[CmdletBinding()]
param(
    [string]$Repository = "paladini-maker/co-op-forge",
    [string]$Branch = "main",
    [string]$CommitMessage = "chore: publish Co-Op Forge project"
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

function Invoke-Gh {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & gh @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gh $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
    }
}

foreach ($toolName in @("git", "gh", "python")) {
    if (-not (Get-Command $toolName -ErrorAction SilentlyContinue)) {
        switch ($toolName) {
            "git"    { throw "Git for Windows is required. Install Git and reopen PowerShell." }
            "gh"     { throw "GitHub CLI is required. Install it from https://cli.github.com/ and reopen PowerShell." }
            "python" { throw "Python 3.10+ is required to validate the project." }
        }
    }
}

if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {
    throw "Repository must use OWNER/NAME format, for example paladini-maker/co-op-forge."
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot "index.html") -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot "README.md") -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot "scripts/validate_project.py") -PathType Leaf)) {
    throw "Run this script from the extracted co-op-forge-github project root."
}

$sourceRoot = $PSScriptRoot
$repoUrl = "https://github.com/$Repository"

# Authenticate and configure Git to reuse the credentials managed by gh.
Invoke-Gh -Arguments @("auth", "status", "--hostname", "github.com")
Invoke-Gh -Arguments @("auth", "setup-git", "--hostname", "github.com")

# Obtain the authenticated identity without requiring a preconfigured global Git identity.
$userOutput = & gh api user
if ($LASTEXITCODE -ne 0) { throw "Could not read the authenticated GitHub profile. Run 'gh auth login' and retry." }
$githubUser = ($userOutput -join [Environment]::NewLine) | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace([string]$githubUser.login) -or -not $githubUser.id) {
    throw "GitHub CLI returned incomplete profile data; refusing to create a commit."
}
$gitName = [string]$githubUser.name
if ([string]::IsNullOrWhiteSpace($gitName)) { $gitName = [string]$githubUser.login }
# Prefer GitHub's privacy-preserving noreply identity, so this script never publishes a private email.
$gitEmail = "$($githubUser.id)+$($githubUser.login)@users.noreply.github.com"

$remoteBranchOutput = & gh api "repos/$Repository" --jq .default_branch
if ($LASTEXITCODE -ne 0) { throw "Could not inspect '$Repository'. Check the repository URL and gh authentication." }
$remoteBranch = [string](($remoteBranchOutput -join "").Trim())
if ($remoteBranch -ne $Branch) {
    throw "Remote default branch is '$remoteBranch', but this script is configured for '$Branch'. No files were pushed."
}

# Run all project checks before modifying the clone or pushing any commit.
& python (Join-Path $sourceRoot "scripts/validate_project.py")
if ($LASTEXITCODE -ne 0) { throw "Project validation failed; nothing was pushed." }
& python -m unittest discover -s (Join-Path $sourceRoot "tests") -v
if ($LASTEXITCODE -ne 0) { throw "Project tests failed; nothing was pushed." }

if (Test-Path -LiteralPath (Join-Path $sourceRoot ".git") -PathType Container) {
    # Existing checkout: validate the destination before staging anything.
    $originOutput = & git -C $sourceRoot remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) { throw "This folder has Git metadata but no origin remote. No remote was changed." }
    $origin = [string](($originOutput -join "").Trim())
    $normalizedOrigin = $origin -replace '^git@github\.com:', 'https://github.com/'
    $normalizedOrigin = $normalizedOrigin -replace '\.git$', ''
    if ($normalizedOrigin.TrimEnd('/') -ne $repoUrl) {
        throw "This checkout's origin is '$origin', not '$repoUrl'. No files were pushed."
    }
    $branchOutput = & git -C $sourceRoot branch --show-current
    if ($LASTEXITCODE -ne 0) { throw "Could not determine the current Git branch." }
    $branchName = [string](($branchOutput -join "").Trim())
    if ($branchName -ne $Branch) { throw "Expected branch '$Branch', found '$branchName'. No files were pushed." }
    $workRoot = $sourceRoot
    $temporaryClone = $false
} else {
    # Clone the target through gh, then overlay the project while keeping the remote history.
    $workRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("co-op-forge-publish-" + [guid]::NewGuid().ToString("N"))
    Invoke-Gh -Arguments @("repo", "clone", $Repository, $workRoot)
    $temporaryClone = $true

    # Robocopy merges dot-directories such as .github into the clone rather than nesting them.
    $copyArgs = @($sourceRoot, $workRoot, "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:2", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS", "/NP")
    & robocopy @copyArgs
    $copyExitCode = $LASTEXITCODE
    if ($copyExitCode -ge 8) { throw "Robocopy failed with exit code $copyExitCode. Clone retained at '$workRoot'." }

    $branchOutput = & git -C $workRoot branch --show-current
    if ($LASTEXITCODE -ne 0) { throw "Could not determine the cloned branch. Clone retained at '$workRoot'." }
    $branchName = [string](($branchOutput -join "").Trim())
    if ($branchName -ne $Branch) { throw "Remote checkout branch is '$branchName', not '$Branch'. No push was attempted." }
}

# Configure identity locally only. This fixes 'Author identity unknown' without changing global Git settings.
Invoke-Git -WorkingDirectory $workRoot -Arguments @("config", "--local", "user.name", $gitName)
Invoke-Git -WorkingDirectory $workRoot -Arguments @("config", "--local", "user.email", $gitEmail)

Invoke-Git -WorkingDirectory $workRoot -Arguments @("add", "--all")
$changes = & git -C $workRoot status --porcelain
if ($LASTEXITCODE -ne 0) { throw "Could not inspect staged changes; no push was attempted." }
if ($changes) {
    Invoke-Git -WorkingDirectory $workRoot -Arguments @("commit", "-m", $CommitMessage)
} else {
    Write-Host "No tracked changes to commit. The repository is already up to date." -ForegroundColor Yellow
}

# Normal push only. Never force-push or rewrite remote history.
Invoke-Git -WorkingDirectory $workRoot -Arguments @("push", "--set-upstream", "origin", $Branch)
Write-Host "Published successfully: $repoUrl" -ForegroundColor Green
Write-Host "Next: select Settings > Pages > Build and deployment > GitHub Actions, then verify the Actions tab."
if ($temporaryClone) {
    Write-Host "Working clone retained at: $workRoot"
    Write-Host "You can use that folder as your checkout or delete it after verifying GitHub."
}
