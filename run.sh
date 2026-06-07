#!/bin/bash

echo "========================================="
echo "🔒 LPX - SEGURANÇA E MONITORAMENTO"
echo "========================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale primeiro."
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt --quiet

# Executar
echo "🚀 Iniciando sistema..."
python app.py