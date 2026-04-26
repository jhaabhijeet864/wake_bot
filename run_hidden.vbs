Set WshShell = CreateObject("WScript.Shell")
' Run the batch file silently (the "0" at the end hides the window)
WshShell.Run chr(34) & "start_wakebot.bat" & Chr(34), 0
Set WshShell = Nothing
