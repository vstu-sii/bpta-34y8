# Run Disputa with this project's course, using the existing account login.
$previousRun = $env:DISPUTA_RUN
$env:DISPUTA_RUN = '01a0e971-7792-7108-951d-2a7a679ad220'
try {
    $cli = Get-Command disputa.cmd -ErrorAction SilentlyContinue
    if ($cli) {
        & $cli.Source @args
    } else {
        $nodeRoot = Join-Path $env:LOCALAPPDATA 'Programs\nodejs'
        $installedCli = Get-ChildItem -Path (Join-Path $nodeRoot 'node-*-win-x64\disputa.cmd') -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $installedCli) {
            throw 'Disputa CLI was not found. Install it with npm install -g disputa.'
        }
        & $installedCli.FullName @args
    }
    $cliExitCode = $LASTEXITCODE
} finally {
    $env:DISPUTA_RUN = $previousRun
}
exit $cliExitCode
