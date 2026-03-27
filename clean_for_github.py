#!/usr/bin/env python3
"""
Script para limpar dados sensíveis antes de publicar no GitHub
"""

import os
import shutil
from pathlib import Path

def limpar_projeto():
    """Remove arquivos sensíveis e dados de teste"""

    # Arquivos/diretórios a remover
    remover = [
        'data/',           # Banco de dados com dados reais
        '__pycache__/',    # Arquivos compilados
        '.env',            # Credenciais reais
        '*.pyc',           # Arquivos compilados
        '*.pyo',
        '*.pyd',
        '.pytest_cache/',  # Cache de testes
        '.coverage',       # Relatórios de cobertura
        'htmlcov/',        # Relatórios HTML
        '*.log',           # Logs
        'logs/',           # Diretório de logs
    ]

    print("🧹 Limpando arquivos sensíveis...")

    for item in remover:
        # Usar glob para arquivos com wildcard
        if '*' in item:
            for file_path in Path('.').glob(item):
                if file_path.exists():
                    try:
                        file_path.unlink()
                        print(f"  ❌ Removido: {file_path}")
                    except Exception as e:
                        print(f"  ⚠️  Não conseguiu remover {file_path}: {e}")
        else:
            path = Path(item)
            if path.exists():
                try:
                    if path.is_file():
                        path.unlink()
                        print(f"  ❌ Removido: {item}")
                    elif path.is_dir():
                        shutil.rmtree(path)
                        print(f"  ❌ Removido: {item}/")
                except Exception as e:
                    print(f"  ⚠️  Não conseguiu remover {item}: {e}")

    # Tentar remover data/ especificamente (pode ser recriado por imports)
    data_path = Path('data')
    if data_path.exists():
        try:
            shutil.rmtree(data_path)
            print("  ❌ Removido: data/")
        except Exception as e:
            print(f"  ⚠️  Não conseguiu remover data/: {e}")
            # Tentar remover apenas o arquivo do banco
            db_path = data_path / 'produtos.db'
            if db_path.exists():
                try:
                    db_path.unlink()
                    print("  ❌ Removido: data/produtos.db")
                except Exception as e2:
                    print(f"  ⚠️  Não conseguiu remover data/produtos.db: {e2}")

    # Verificar se há dados no .gitignore
    gitignore_path = Path('.gitignore')
    if gitignore_path.exists():
        print("✅ .gitignore encontrado")
    else:
        print("⚠️  .gitignore não encontrado - crie um!")

    print("\n🎯 Projeto limpo para publicação!")
    print("📝 Lembre-se:")
    print("   - Configure .env com suas credenciais (não commite)")
    print("   - Teste a aplicação antes de publicar")
    print("   - Use .env.example como template")

if __name__ == "__main__":
    limpar_projeto()