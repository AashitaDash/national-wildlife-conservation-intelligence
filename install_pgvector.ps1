Write-Host "Taking ownership of PostgreSQL 16 directories..."
takeown /F "C:\Program Files\PostgreSQL\16\lib" /A /R /D Y
takeown /F "C:\Program Files\PostgreSQL\16\share\extension" /A /R /D Y

Write-Host "Granting Administrators full control..."
icacls "C:\Program Files\PostgreSQL\16\lib" /grant Administrators:F /T
icacls "C:\Program Files\PostgreSQL\16\share\extension" /grant Administrators:F /T

Write-Host "Stopping PostgreSQL 16 service just in case files are locked..."
Stop-Service -Name postgresql-x64-16 -Force -ErrorAction SilentlyContinue

Write-Host "Copying files..."
Copy-Item -Path "C:\Users\KIIT0001\Downloads\pgvector_temp\lib\vector.dll" -Destination "C:\Program Files\PostgreSQL\16\lib\" -Force -Verbose
Copy-Item -Path "C:\Users\KIIT0001\Downloads\pgvector_temp\share\extension\vector*" -Destination "C:\Program Files\PostgreSQL\16\share\extension\" -Force -Verbose

Write-Host "Starting PostgreSQL 16 service..."
Start-Service -Name postgresql-x64-16 -ErrorAction SilentlyContinue
