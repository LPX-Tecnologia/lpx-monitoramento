#!/bin/bash

echo "🧹 Limpando arquivos temporários..."

# Remover cache Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Remover bancos de dados
rm -f *.db

# Remover logs
rm -f *.log

echo "✅ Limpeza concluída!"