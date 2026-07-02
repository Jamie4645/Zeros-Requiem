@echo off
REM Weekly Falsifier Check — Round 8 Step 3
REM Register this once with Task Scheduler to run every Monday 08:00 UTC.
REM
REM Usage (from an Admin shell):
REM   schtasks /Create /SC WEEKLY /D MON /TN "SBRS_WeeklyFalsifier" ^
REM           /TR "C:\Users\jamie\OneDrive\Documents\Jamie VS Code\Git\Zeros Requiem\scripts\schedule_weekly_falsifier.bat" ^
REM           /ST 08:00 /F

cd /d "C:\Users\jamie\OneDrive\Documents\Jamie VS Code\Git\Zeros Requiem"
py scripts\weekly_falsifier_check.py >> logs\paper\weekly_falsifier.log 2>&1
