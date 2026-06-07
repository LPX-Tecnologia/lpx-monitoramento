#!/bin/bash

echo "========================================="
echo "🔒 LPX MONITORAMENTO - INSTALADOR"
echo "========================================="

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar sistema
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${GREEN}✅ Linux detectado${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}✅ macOS detectado${NC}"
else
    echo -e "${RED}❌ Sistema não suportado${NC}"
    exit 1
fi

# Instalar Python se necessário
if ! command -v python3 &> /dev/null; then
    echo "📦 Instalando Python 3..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-full python3-venv python3-pip
    elif command -v brew &> /dev/null; then
        brew install python3
    fi
fi

# Criar ambiente virtual
echo "📦 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "========================================="
echo -e "${GREEN}✅ INSTALAÇÃO CONCLUÍDA!${NC}"
echo "========================================="
echo "Para executar:"
echo "  ./run.sh"
echo "========================================="