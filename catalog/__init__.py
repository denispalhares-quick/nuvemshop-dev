"""Importação de catálogo (produtos, categorias e imagens) para a Nuvemshop.

Uso rápido (a partir da raiz do repo):

    python3 -m catalog validate produtos.csv
    python3 -m catalog import produtos.csv                 # dry-run: só mostra o plano
    python3 -m catalog import produtos.csv --apply         # grava na loja

Detalhes em catalog/README.md.
"""
