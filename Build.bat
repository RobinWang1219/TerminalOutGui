@echo off
cd /d %~dp0

call Env.bat

SET WORKING_SPACE=%CD%

ruff format .

REM windows detect has various in pyinstaller
REM pyinstaller --noconfirm --onedir --windowed  ^
              REM --icon "%WORKING_SPACE%\app_icon.ico" ^
              REM --add-data "%WORKING_SPACE%\app_icon.png;." ^
              REM --version-file "%WORKING_SPACE%\TerminalOutGui.ffi" ^
              REM --distpath "%WORKING_SPACE%\output2" ^
              REM --workpath "%WORKING_SPACE%\temp\build" ^
              REM --specpath "%WORKING_SPACE%\temp" ^
              REM --clean ^
              REM --debug noarchive ^
              REM "%WORKING_SPACE%\TerminalOutGui.py"

REM rmdir /s /q "%WORKING_SPACE%\temp"

auto-py-to-exe -nc -c TerminalOutGui.json

@echo on