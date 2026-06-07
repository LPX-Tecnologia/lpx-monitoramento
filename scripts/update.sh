#!/bin/bash

echo "🔄 Atualizando LPX Monitoramento..."

# Pull do GitHub
git pull origin main

# Ativar ambiente virtual
source venv/bin/activate

# Atualizar dependências
pip install -r requirements.txt --upgrade

echo "✅ Sistema atualizado!"