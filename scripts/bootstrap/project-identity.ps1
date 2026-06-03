# [Jacazul] Project Identity Resolver (PowerShell Version)

function Resolve-JacazulProjectAnchor ($cwd) {
    if (!$cwd) { $cwd = (Get-Location).Path }
    
    # Resolve absolute path safely
    $resolved = Resolve-Path $cwd -ErrorAction SilentlyContinue
    if ($resolved) { $cwd = $resolved.Path }
    
    if (!(Get-Command git -ErrorAction SilentlyContinue)) {
        return $cwd
    }
    
    # Check if inside git work tree
    $isWorkTree = git -C $cwd rev-parse --is-inside-work-tree 2>$null
    if ($LastExitCode -eq 0 -and $isWorkTree -eq "true") {
        $topLevel = (git -C $cwd rev-parse --show-toplevel 2>$null)
        $gitDir = (git -C $cwd rev-parse --path-format=absolute --git-dir 2>$null)
        $commonDir = (git -C $cwd rev-parse --path-format=absolute --git-common-dir 2>$null)
        
        if ($topLevel -and $gitDir -and $commonDir -and ($gitDir -ne $commonDir)) {
            $commonBase = Split-Path $commonDir -Leaf
            if ($commonBase -eq ".git" -or $commonBase -eq ".bare") {
                return (Split-Path $commonDir -Parent)
            }
        }
        
        if ($topLevel) {
            # Make sure to return resolved absolute path
            $resolvedTop = Resolve-Path $topLevel -ErrorAction SilentlyContinue
            if ($resolvedTop) { return $resolvedTop.Path }
            return $topLevel
        }
    }
    
    return $cwd
}

function Export-JacazulProjectIdentity ($cwd) {
    if (!$cwd) { $cwd = (Get-Location).Path }
    
    $anchorDir = Resolve-JacazulProjectAnchor $cwd
    
    $parentDir = Split-Path (Split-Path $anchorDir -Parent) -Leaf
    $currentDir = Split-Path $anchorDir -Leaf
    
    $env:JACAZUL_PROJECT_ANCHOR = $anchorDir
    $env:PARENT_DIR = $parentDir
    $env:CURRENT_DIR = $currentDir
    $env:PROJECT_ID = "${parentDir}_${currentDir}"
}