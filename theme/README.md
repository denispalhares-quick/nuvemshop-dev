# theme/

Pasta do tema da loja (estrutura da Nuvemshop CLI). Está vazia de propósito — traga o tema com:

```bash
cd theme
nuvemshop theme authorize            # uma vez
nuvemshop theme list                 # pega o THEME_ID da instalação
nuvemshop theme pull --theme-id ID   # ou --published
```

Estrutura esperada após o pull:

```
blocks/ config/ layouts/ locales/ sections/ snippets/ static/ templates/ manifest.json
```

`manifest.json` e `.nuvem` são metadados locais (installation_id, revision_token) e ficam fora do git.
Cada ambiente (homolog / prod) é uma instalação diferente — use `--theme-id` para escolher.

Para editar código além de `templates/` e `config/settings_data.json`, a instalação precisa estar **forkada** (`nuvemshop theme fork`).
