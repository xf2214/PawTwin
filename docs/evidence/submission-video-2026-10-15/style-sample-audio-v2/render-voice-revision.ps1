param([string]$Output = '..\PawTwin-style-sample-2026-10-15.en.v2.mp4')
$ErrorActionPreference = 'Stop'
$taskNode = 'C:\Users\11831\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
& $taskNode '.\node_modules\@remotion\cli\remotion-cli.js' render src/index.tsx PawTwinVoiceRevision $Output --codec=h264 --crf=18 --audio-bitrate=192k --pixel-format=yuv420p --concurrency=1 --media-cache-size-in-bytes=268435456 --offthreadvideo-cache-size-in-bytes=67108864 --offthreadvideo-threads=1 --browser-executable='C:\Program Files\Google\Chrome\Application\chrome.exe' --log=warn *> render-voice-revision.log
if ($LASTEXITCODE -ne 0) { Get-Content render-voice-revision.log -Tail 35; throw 'Local revision render failed; full log preserved.' }
Get-Content render-voice-revision.log -Tail 5
