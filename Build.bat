@echo off
cd /d %~dp0

call Env.bat

SET WORKING_SPACE=%CD%

ruff format .

pyinstaller --noconfirm --onefile --windowed  ^
              --icon "%WORKING_SPACE%\app_icon.ico" ^
              --add-data "%WORKING_SPACE%\app_icon.png;." ^
              --version-file "%WORKING_SPACE%\TerminalOutGui.ffi" ^
              --distpath "%WORKING_SPACE%\output" ^
              --workpath "%WORKING_SPACE%\temp\build" ^
              --specpath "%WORKING_SPACE%\temp" ^
              --clean ^
              "%WORKING_SPACE%\TerminalOutGui.py"

rmdir /s /q "%WORKING_SPACE%\temp"
@echo on