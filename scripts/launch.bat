@echo off
REM ═══════════════════════════════════════════════════════════════
REM  NimbusBill — One-Command Launch Script (Windows)
REM ═══════════════════════════════════════════════════════════════
echo.
echo  ☁️  NimbusBill Launch Script
echo  ════════════════════════════
echo.

REM ── Step 1: Generate sample data ────────────────────────────
echo [1/5] Generating sample data...
python datagen\generate_usage_events.py --output datagen\data
python datagen\generate_customers.py --output datagen\data
python datagen\generate_pricing.py --output datagen\data
echo       ✅ Data generated in datagen\data\
echo.

REM ── Step 2: Initialize Snowflake ────────────────────────────
echo [2/5] Initializing Snowflake schemas...
python scripts\init_snowflake.py
echo       ✅ Snowflake initialized
echo.

REM ── Step 3: Load seed/reference data ────────────────────────
echo [3/5] Loading reference data into Snowflake...
python scripts\load_seed_data.py
echo       ✅ Reference data loaded
echo.

REM ── Step 4: Start Airflow (Docker) ──────────────────────────
echo [4/5] Starting Airflow containers...
cd airflow
docker-compose up -d --build
cd ..
echo       ✅ Airflow running at http://localhost:8081 (admin/admin)
echo.

REM ── Step 5: Start API ───────────────────────────────────────
echo [5/5] Starting FastAPI server...
echo       API will be available at http://localhost:8000/docs
echo       Press Ctrl+C to stop.
echo.
cd api
start "NimbusBill API" cmd /k "uvicorn main:app --reload --port 8000"
cd ..

echo.
echo  ════════════════════════════════════════════════════════
echo  All services started!
echo.
echo   Airflow UI:   http://localhost:8081
echo   API Swagger:  http://localhost:8000/docs
echo   Dashboard:    cd web ^&^& npm run dev
echo  ════════════════════════════════════════════════════════
echo.
pause
