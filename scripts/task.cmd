@echo off
echo ERROR: Direct usage of 'task' is restricted in this environment. >&2
echo. >&2
echo Don't sweat it! Please use one of the official wrappers instead: >&2
echo   - 'taskp'   : Project-aware Taskwarrior wrapper (preserves isolation). >&2
echo   - 'tw-flow' : The official 7-phase workflow manager (ensures documentation). >&2
echo. >&2
echo Using the raw 'task' binary bypasses project isolation and safety checks. >&2
echo Keeping the lake clean is part of the mission! >&2
exit /b 1
