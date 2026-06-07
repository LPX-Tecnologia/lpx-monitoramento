@echo off
echo =========================================
echo 🔒 LPX - SEGURANÇA E MONITORAMENTO
echo =========================================

if not exist "venv" (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

call venv\Scripts\activate

echo 📦 Instalando dependencias...
pip install -r requirements.txt --quiet

echo 🚀 Iniciando sistema...
python app.py
pause