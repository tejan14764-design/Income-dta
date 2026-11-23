#!/usr/bin/env pwsh
<#
.SYNOPSIS
    INCOME – PostgreSQL database setup script for Windows.
.DESCRIPTION
    Creates the income_db database and income_user.
    Run as administrator if PostgreSQL is newly installed.
    You need to know the postgres superuser password.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PostgresPassword,
    
    [string]$DbName = "income_db",
    [string]$DbUser = "income_user",
    [string]$DbPassword = "Income@2024!",
    [string]$Host = "127.0.0.1",
    [int]$Port = 5432
)

$env:PGPASSWORD = $PostgresPassword

Write-Host "Creating database user '$DbUser'..." -ForegroundColor Cyan
$userSql = "DO `$`$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DbUser') THEN CREATE USER $DbUser WITH PASSWORD '$DbPassword'; END IF; END `$`$;"
psql -U postgres -h $Host -p $Port -c $userSql

Write-Host "Creating database '$DbName'..." -ForegroundColor Cyan
$dbCheck = psql -U postgres -h $Host -p $Port -t -c "SELECT 1 FROM pg_database WHERE datname='$DbName';"
if ($dbCheck -notmatch "1") {
    psql -U postgres -h $Host -p $Port -c "CREATE DATABASE $DbName OWNER $DbUser;"
} else {
    Write-Host "  Database '$DbName' already exists." -ForegroundColor Yellow
}

Write-Host "Granting privileges..." -ForegroundColor Cyan
psql -U postgres -h $Host -p $Port -c "GRANT ALL PRIVILEGES ON DATABASE $DbName TO $DbUser;"
psql -U postgres -h $Host -p $Port -d $DbName -c "GRANT ALL ON SCHEMA public TO $DbUser;"

Write-Host "`n✓ Database setup complete!" -ForegroundColor Green
Write-Host "  DB Name: $DbName" -ForegroundColor White
Write-Host "  DB User: $DbUser" -ForegroundColor White
Write-Host "  DB Password: $DbPassword" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Update backend/.env with these credentials"
Write-Host "  2. cd backend"
Write-Host "  3. .\\venv\\Scripts\\python manage.py migrate"
Write-Host "  4. .\\venv\\Scripts\\python manage.py seed_initial_data"
