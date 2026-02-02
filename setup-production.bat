@echo off
echo ========================================
echo VideoExpress AI - Production Setup
echo ========================================
echo.

echo [1/5] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [2/5] Installing Node dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node dependencies
    pause
    exit /b 1
)

echo.
echo [3/5] Checking environment configuration...
if not exist "backend\.env" (
    echo WARNING: backend\.env not found
    echo Please copy .env.production.template to backend\.env and configure
    pause
)

echo.
echo [4/5] Running database migration...
cd backend
python migrate.py
cd ..

echo.
echo [5/5] Setup complete!
echo.
echo Next steps:
echo 1. Configure backend\.env with your API keys
echo 2. Run Supabase migration: cd supabase ^&^& python migrate_supabase.py
echo 3. Start development: npm run dev
echo 4. Or build production: npm run make
echo.
pause
