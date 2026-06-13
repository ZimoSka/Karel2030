# Synchronizácia svetov medzi bežiacim kontajnerom (volume /data/worlds)
# a repozitárom (worlds/). Rieši problém "in-app úpravy sa pri rebuilde zabudnú".
#
# POUŽITIE:
#   pwsh scripts/sync_worlds.ps1 pull   # volume -> repo (zachytí in-app úpravy do gitu)
#   pwsh scripts/sync_worlds.ps1 push   # repo  -> volume (nahrá repo svety do kontajnera)
#   pwsh scripts/sync_worlds.ps1 list   # vypíše svety na oboch stranách
#
# Workflow zapamätania úprav:
#   1) učiteľ edituje svet v appke a Publikuje (📤, admin) → uloží sa na volume
#   2) `pull` skopíruje zmenené .karxml z volume do worlds/
#   3) git commit → úpravy sú v gite a zapečú sa do ďalšieho image (prežijú rebuild)
#
# POZOR: pri konflikte (rovnaké id na oboch stranách s rôznym obsahom) skript
# NEPREPÍŠE ticho — vypíše rozdiel a nechá rozhodnutie na teba.

param(
    [Parameter(Mandatory = $true)][ValidateSet('pull', 'push', 'list')]
    [string]$Action,
    [string]$Container = 'karel2030'
)

$ErrorActionPreference = 'Stop'
$repoWorlds = Join-Path $PSScriptRoot '..\worlds'
$volPath = '/data/worlds'

function Get-VolWorlds {
    (docker exec $Container sh -c "ls $volPath 2>/dev/null") -split "`n" |
        Where-Object { $_ -match '\.karxml$' } | ForEach-Object { $_.Trim() }
}

switch ($Action) {
    'list' {
        Write-Output "=== repo worlds/ ==="
        Get-ChildItem $repoWorlds -Filter *.karxml | ForEach-Object { $_.Name }
        Write-Output "=== volume $volPath ($Container) ==="
        Get-VolWorlds
    }
    'pull' {
        $tmp = Join-Path $env:TEMP ("karelsync_" + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $tmp | Out-Null
        foreach ($f in Get-VolWorlds) {
            docker cp "${Container}:$volPath/$f" (Join-Path $tmp $f) | Out-Null
            $dest = Join-Path $repoWorlds $f
            if (Test-Path $dest) {
                $diff = Compare-Object (Get-Content $dest) (Get-Content (Join-Path $tmp $f))
                if ($diff) {
                    Write-Output "⚠ KONFLIKT: $f sa líši (repo vs volume). Skontroluj ručne:"
                    Write-Output "   repo:   $dest"
                    Write-Output "   volume: $(Join-Path $tmp $f)"
                    continue
                } else { Write-Output "= $f (bez zmeny)"; continue }
            }
            Copy-Item (Join-Path $tmp $f) $dest
            Write-Output "+ $f (nový → repo)"
        }
        Write-Output "Hotovo. Skontroluj `git status` a commitni."
    }
    'push' {
        foreach ($f in Get-ChildItem $repoWorlds -Filter *.karxml) {
            docker cp $f.FullName "${Container}:$volPath/$($f.Name)" | Out-Null
            Write-Output "→ $($f.Name) (repo → volume)"
        }
    }
}
