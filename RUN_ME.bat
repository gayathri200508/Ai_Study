@echo off
echo ========================================
echo    AI Study Generator - Setup & Run
echo ========================================
echo.
echo Step 1: Installing required packages...
pip install streamlit anthropic python-dotenv
echo.
echo Step 2: Starting app...
streamlit run app.py
pause
