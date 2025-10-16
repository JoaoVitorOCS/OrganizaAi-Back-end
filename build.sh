#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Criar diretório de uploads
mkdir -p uploads

echo "✅ Build concluído com sucesso!"
