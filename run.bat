@echo off
cd /d "%~dp0"
set "PROJECT=sample"
if not "%~1"=="" set "PROJECT=%~1"
py -3.11 -c "from make_video import ffmpeg_path; print(ffmpeg_path())"
if errorlevel 1 goto error
py -3.11 generate_audio.py "%PROJECT%"
if errorlevel 1 goto error
py -3.11 make_video.py "%PROJECT%"
if errorlevel 1 goto error
start "" "%PROJECT%\output.mp4"
pause
exit /b 0
:error
echo Failed. Check the error message above.
pause
exit /b 1
