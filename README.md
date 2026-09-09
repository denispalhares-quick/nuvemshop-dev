# nuvemshop-dev

Kit de desenvolvimento Nuvemshop da Acta Publicidade: um **servidor MCP** (catálogo, pedidos, clientes, cupons, **webhooks** e **tema**) + **tema versionado em git** com **deploy por CI**.

Base: fork de [AlexandreProenca/nuvemshop-mcp-server](https://github.com/AlexandreProenca/nuvemshop-mcp-server) (MIT), com:

- credenciais só por variável de ambiente (o upstream tinha token fixo no código);
- tools de **webhooks** (`list/get/create/update/delete_webhook`, `list_webhook_events`);
- tools de **tema** que embrulham a CLI oficial `@tiendanube/cli` (`theme_list`, `theme_pull`, `theme_diff`, `theme_push`, `theme_publish`, `theme_preview`, `theme_performance`, `theme_fork`);
- escrita perigosa (push/publish/fork) exige `confirm=True`;
- pipeline GitHub Actions: PR → diff + push em **homolog**; merge em `main` → push em **prod**; publish manual.

```
nuvemshop-dev/
├── mcp-server/           servidor MCP (Python) — main.py + extensions/{webhooks,theme}.py
├── theme/                tema da loja (pull via CLI) — versionado aqui
├── scripts/theme-push.sh deploy manual: homolog | prod [--publish]
├── .github/workflows/    theme-deploy.yml
├── .mcp.json             config para Claude Code (raiz do projeto)
└── claude-desktop.example.json
```

## O que a plataforma permite (e o que este repo cobre)

| Frente | Como funciona na Nuvemshop | Neste repo |
|---|---|---|
| Catálogo, pedidos, clientes, cupons | Admin API | ✅ tools MCP |
| Webhooks | Admin API `/webhooks` | ✅ tools MCP |
| Tema / layout | Só pela CLI (`pull/push/diff/watch`), sem API pública | ✅ tools MCP + git + CI |
| Frete próprio | Shipping Carrier API — app que responde cotações | ❌ (projeto à parte) |
| Pagamento próprio | Payment Provider API — app homologado | ❌ (projeto à parte) |
| Checkout | Hospedado; só scripts/estilo via app | ❌ |

## Setup

```bash
# 1. dependências
cd mcp-server && pip install -r requirements.txt && cd ..
npm install -g @tiendanube/cli

# 2. credenciais
cp .env.example .env   # preencha TIENDANUBE_ACCESS_TOKEN e TIENDANUBE_STORE_ID
nuvemshop theme authorize

# 3. tema
cd theme && nuvemshop theme list && nuvemshop theme pull --theme-id <ID> && cd ..

# 4. testar o MCP
cd mcp-server && python3 main.py          # stdio
MCP_TRANSPORT=streamable-http python3 main.py   # http://localhost:8080/mcp
```

**Token da API**: crie um app em `partners.nuvemshop.com.br`, instale na loja e faça o fluxo OAuth — o `access_token` não expira.
**Claude Code**: abrir a pasta já carrega `.mcp.json` (exporta as env vars antes).
**Claude Desktop**: copie `claude-desktop.example.json` para a config do app e preencha.

## Fluxo de tema (git → loja)

1. `git checkout -b feat/home-banner` → edita `theme/`
2. `theme_diff` (ou `nuvemshop theme diff`) → PR
3. CI faz push em **homolog** e imprime a URL de preview
4. Merge em `main` → CI faz push em **prod**
5. `workflow_dispatch` com `publish=true` (ou `scripts/theme-push.sh prod --publish`) para ativar

Secrets do GitHub: `NUVEMSHOP_CLI_TOKEN`, `THEME_ID_HOMOLOG`, `THEME_ID_PROD` (crie os environments `homolog` e `production`).

## Multi-loja

Um `.env`/instância por loja. Para vários clientes, rode uma instância do MCP por loja (ou troque as env vars) e um repo/branch de tema por loja.

## Ressalvas

- API tem rate limit; operações em lote grandes podem retornar 429 — o server não faz retry.
- Tools de exclusão (produto, cliente, webhook) não pedem confirmação. Teste numa loja de teste.
- `manifest.json` e `.nuvem` são por máquina/ambiente e ficam fora do git.

## Docs

- `mcp-server/docs/` — guias do upstream (quick start, deploy, variantes, SSE x streamable)
- CLI: https://dev.nuvemshop.com.br/docs/developer-tools/cli/overview
- API: https://tiendanube.github.io/api-documentation/resources
