param([string]$Output = '..\PawTwin-hackathon-submission-2026-10-15.en.mp4')
$ErrorActionPreference = 'Stop'
$taskNode = 'C:\Users\11831\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
if (Test-Path -LiteralPath $Output) { throw 'Refusing to overwrite an existing full-film delivery; select a new versioned path.' }
& $taskNode '.\node_modules\@remotion\cli\remotion-cli.js' render src/index.tsx PawTwinHackathonFilm $Output --codec=h264 --crf=18 --audio-bitrate=192k --pixel-format=yuv420p --concurrency=1 --media-cache-size-in-bytes=268435456 --offthreadvideo-cache-size-in-bytes=67108864 --offthreadvideo-threads=1 --browser-executable='C:\Program Files\Google\Chrome\Application\chrome.exe' --log=warn *> render-fullfilm.log
if ($LASTEXITCODE -ne 0) { Get-Content render-fullfilm.log -Tail 35; throw 'Full-film render failed; detailed log preserved.' }
Get-Content render-fullfilm.log -Tail 5
