# nuvemshop-dev

Kit de desenvolvimento Nuvemshop: um **servidor MCP** (catálogo, pedidos, clientes, cupons, **webhooks** e **tema**) + **tema versionado em git**, com **build de frontend** (Tailwind + Alpine) e **deploy por CI**.

> **Status:** repo pronto para uso, ainda não rodado contra uma loja real. O primeiro projeto que usar isto deve validar os pontos listados em [Pendências](#pendências).

Construído sobre o [nuvemshop-mcp-server](https://github.com/AlexandreProenca/nuvemshop-mcp-server) (MIT), com:

- credenciais só por variável de ambiente (o upstream tinha token fixo no código);
- tools de **webhooks** (`list/get/create/update/delete_webhook`, `list_webhook_events`);
- tools de **tema** que embrulham a CLI oficial `@tiendanube/cli` (`theme_list`, `theme_pull`, `theme_diff`, `theme_push`, `theme_publish`, `theme_preview`, `theme_performance`, `theme_fork`);
- escrita perigosa (push/publish/fork) exige `confirm=True`;
- pipeline GitHub Actions: PR → diff + push em **homolog**; merge em `main` → push em **prod**; publish manual.

```
nuvemshop-dev/
├── mcp-server/            servidor MCP (Python) — main.py + extensions/{webhooks,theme}.py
├── frontend/              fonte do CSS/JS — Tailwind v4 + esbuild + Alpine
│   ├── build.mjs          bundle com nome fixo (sem hash)
│   └── src/{css,js}/
├── theme/                 tema da loja (pull via CLI) — versionado aqui
│   └── static/            css/tokens.scss.tpl é fonte; style.css e store.js são gerados
├── scripts/
│   ├── get-token.py       troca o code do OAuth pelo access_token e grava no .env
│   └── theme-push.sh      build + deploy manual: homolog | prod [--publish]
├── docs/frontend.md       stack do front, assets, sections, restrições
├── .github/workflows/     theme-deploy.yml (build → diff → push)
├── .mcp.json              config para Claude Code (raiz do projeto)
└── claude-desktop.example.json
```


---

## Começando uma loja do zero

Passo a passo completo. Marque conforme for fazendo — o que trava a maioria das pessoas é o passo 2.

### 1. Ferramentas

```bash
cd mcp-server && pip install -r requirements.txt && cd ..
cd frontend && npm ci && cd ..
npm install -g @tiendanube/cli
nuvemshop --version          # confirma a instalação (o comando `tiendanube` é equivalente)
```

Requisitos: Python 3.11+, Node 20+.

### 2. Credenciais da Admin API (OAuth)

O token da API sai de um **app de parceiro**, não do painel da loja.

1. Cadastre-se em <https://www.nuvemshop.com.br/parceiros>.
2. No painel de parceiro, **Apps → criar app**. Anote o **App ID** (`client_id`) e o **Client Secret**.
   Nos scopes, marque o que o projeto vai usar (produtos, pedidos, clientes, webhooks…).
3. Logado como **dono da loja**, abra no navegador:
   `https://www.tiendanube.com/apps/<APP_ID>/authorize`
4. Após autorizar, a URL de redirect traz `?code=XXXX`. **Esse code expira em 5 minutos.**
5. Troque o code pelo token:

```bash
python3 scripts/get-token.py --app-id <APP_ID> --secret <SECRET> --code <CODE>
```

O script grava `TIENDANUBE_ACCESS_TOKEN` e `TIENDANUBE_STORE_ID` no `.env` (crie antes com `cp .env.example .env`).
**O access_token não expira** — só é invalidado se você gerar outro ou o lojista desinstalar o app.

### 3. Autorizar a CLI (tema)

```bash
nuvemshop theme authorize
```

Autenticação da CLI é separada da API — uma coisa não substitui a outra.

### 4. Trazer o tema para o repo

```bash
cd theme
nuvemshop theme list                    # anote o THEME_ID da instalação
nuvemshop theme pull --theme-id <ID>    # ou --published para o tema ativo
cd ..
git add theme && git commit -m "chore: tema inicial"
```

Loja nova sem tema próprio? Crie a partir de um tema base:

```bash
nuvemshop theme create --base-theme ipanema --title "Loja do Cliente"
```

Prefira o **Ipanema** como base: é o único tema *sectionable* hoje, o que te dá sections e blocks editáveis pelo lojista no Brand Editor.

Para editar além de `templates/`, `custom/` e `config/settings_data.json` — ou seja, para tocar em `static/`, `sections/`, `blocks/` e `layouts/` — a instalação precisa estar **forkada** (operação irreversível):

```bash
nuvemshop theme fork
```

### 5. Ambientes homolog e prod

Cada ambiente é uma **instalação de tema diferente** na mesma loja (ou uma loja de teste separada). Duplique o tema (`nuvemshop theme clone`), pegue os dois IDs em `theme list` e coloque no `.env`:

```
THEME_ID_HOMOLOG=...
THEME_ID_PROD=...
```

**Limite da plataforma: 2 instalações de tema por loja.** Homolog e prod cabem exatos, sem folga para uma terceira. Nunca desenvolva direto contra o tema publicado.

### 6. Ligar o MCP no Claude

```bash
cd mcp-server && python3 main.py                  # stdio (teste)
MCP_TRANSPORT=streamable-http python3 main.py     # http://localhost:8080/mcp
```

- **Claude Code:** abrir a pasta já carrega o `.mcp.json` (exporte as env vars do `.env` antes).
- **Claude Desktop:** copie `claude-desktop.example.json` para a config do app e preencha o token/store_id.

Teste rápido pelo chat: *"lista as categorias da loja"* e *"roda theme_diff"*.

### 7. Desenvolver

```bash
git checkout -b feat/home-banner

# terminal 1 — recompila CSS/JS a cada save
cd frontend && npm run dev

# terminal 2 — envia para a instalação de homologação
cd theme && nuvemshop theme watch --theme-id $THEME_ID_HOMOLOG
```

Daí em diante vale o [fluxo de tema](#fluxo-de-tema-git--loja). Detalhes do front em **[docs/frontend.md](docs/frontend.md)**.

---

## Frontend

O tema **não** é só HTML/CSS/JS: a Nuvemshop roda **Twig** e compila **SASS** no servidor. O build local cobre só a parte estática.

| Camada | Onde roda | No repo |
|---|---|---|
| Twig (`.tpl`) | servidor da Nuvemshop | `theme/` |
| SASS (`.scss.tpl`) | servidor da Nuvemshop | `theme/static/css/tokens.scss.tpl` |
| CSS/JS estáticos | navegador | build de `frontend/src/` → `theme/static/` |

- **Tailwind v4** → `theme/static/css/style.css`
- **esbuild + Alpine.js** → `theme/static/js/store.js` (nome fixo: o `.tpl` referencia o arquivo literalmente, e não há manifest de assets na plataforma)
- **`tokens.scss.tpl`** faz a ponte entre as cores do Brand Editor e o Tailwind, via CSS custom properties

Saída de build é gitignorada — quem gera é o CI. Nada de SPA: o HTML já vem renderizado, o JS é progressive enhancement.

Guia completo: **[docs/frontend.md](docs/frontend.md)**.

## O que a plataforma permite (e o que este repo cobre)

| Frente | Como funciona na Nuvemshop | Neste repo |
|---|---|---|
| Catálogo, pedidos, clientes, cupons | Admin API | ✅ tools MCP |
| Webhooks | Admin API `/webhooks` | ✅ tools MCP |
| Tema / layout | Só pela CLI (`pull/push/diff/watch`), sem API pública | ✅ tools MCP + git + CI |
| Frete próprio | Shipping Carrier API — app que responde cotações | ❌ (projeto à parte) |
| Pagamento próprio | Payment Provider API — app homologado | ❌ (projeto à parte) |
| Checkout | Hospedado; só scripts/estilo via app | ❌ |

## Fluxo de tema (git → loja)

1. `git checkout -b feat/home-banner` → edita `theme/` e/ou `frontend/src/`
2. `theme_diff` (ou `nuvemshop theme diff`) → abre o PR
3. CI faz o build do frontend, push em **homolog** e imprime a URL de preview
4. Merge em `main` → CI faz push em **prod**
5. `workflow_dispatch` com `publish=true` (ou `scripts/theme-push.sh prod --publish`) para ativar

Secrets do GitHub: `NUVEMSHOP_CLI_TOKEN`, `THEME_ID_HOMOLOG`, `THEME_ID_PROD` (crie os environments `homolog` e `production`).

## Multi-loja

Um `.env`/instância por loja. Para vários clientes, rode uma instância do MCP por loja (ou troque as env vars) e um repo/branch de tema por loja.

## Pendências

Validar no primeiro projeto real:

- [ ] `--token` da CLI junto com `--theme-id` em CI, sem `.nuvem` local. Se o workflow reclamar, rode um `pull` antes do `push` no job.
- [ ] Import do SDK `mcp` no servidor (só a sintaxe foi validada até agora — nada rodou contra a API).
- [ ] Qual header a API aceita: o server manda `Authentication: bearer` **e** `Authorization: Bearer`; confirmar e remover o que sobrar.
- [ ] Comportamento sob rate limit em carga de catálogo grande (ver abaixo).
- [ ] **Cache-busting dos assets**: com nome fixo e sem hash, não está documentado se o `static_url` versiona a URL a cada revisão do tema. Testar no primeiro deploy; se não versionar, usar sufixo manual via setting.
- [ ] Nomes dos settings em `theme/static/css/tokens.scss.tpl` — conferir contra o tema real depois do `theme pull`.

## Ressalvas

- **Rate limit:** 40 requisições de bucket, 2 req/s por par loja-app (×10 nos planos Next/Evolution). Estourou, vem `429` — o server **não** faz retry. Cargas grandes precisam de throttle manual.
- **User-Agent é obrigatório**; sem ele a API responde `400`.
- Tools de exclusão (produto, cliente, webhook) não pedem confirmação. Teste numa loja de teste.
- `manifest.json` e `.nuvem` são por máquina/ambiente e ficam fora do git.
- Webhooks exigem URL **HTTPS pública** — em dev, use um túnel (ngrok/cloudflared).

## Docs

- `mcp-server/docs/` — guias do upstream (quick start, deploy, variantes, SSE x streamable)
- CLI: <https://dev.nuvemshop.com.br/docs/developer-tools/cli/overview>
- API: <https://tiendanube.github.io/api-documentation/resources>
- Autenticação: <https://tiendanube.github.io/api-documentation/authentication>
