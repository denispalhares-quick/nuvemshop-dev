---
name: brand-editor-sync
description: Guia e executa o ciclo de edição visual do tema Nuvemshop pelo Brand Editor sem perder mudanças — pausa o `theme watch` do Docker, orienta a edição na instalação de homolog, faz o `theme pull` dentro de theme/, reconstrói o CSS/JS injetado e commita. Use quando o usuário quiser montar ou alterar a home, imagens, textos, seções, cores ou fontes pelo Brand Editor / "Personalizar layout", ou disser "puxar do Brand Editor", "trazer mudanças da loja", "sincronizar o tema".
---

# Brand Editor ↔ repo

O Brand Editor grava direto na loja; o `theme watch` (Docker) e o job `homolog` do CI enviam o que está no
repo. Os dois sobrescrevem um ao outro. Esta skill conduz a ordem segura.

Tudo roda a partir da **raiz do repo** (`nuvemshop-dev/`). IDs e URL da loja vêm do `.env`
(`THEME_ID_HOMOLOG`, `THEME_ID_PROD`) — nunca assuma que estão exportados no terminal.

## Regras

- **Nunca publique.** Não rode `nuvemshop theme publish`, não sugira clicar em "Publicar" e não mexa no
  tema de `THEME_ID_PROD`. Publicar troca a loja no ar — só com pedido explícito do usuário para isso.
- **`theme pull` só dentro de `theme/`.** Na raiz ele baixa uma cópia do tema inteiro na raiz.
- **Todo pull apaga** `theme/static/css/tailwind.css` e `theme/static/js/app.js` (gerados, só locais) e
  remove o CSS/JS injetado dos JSON. Sempre reconstrua depois (passo 4).
- Não cole tokens nem secrets em comandos ou mensagens.

## Passo 1 — pausar o envio automático

```bash
docker compose stop theme
docker compose ps --format 'table {{.Service}}\t{{.Status}}'
```

Confirme que `theme` está `Exited`. Se o working tree tiver mudanças em `theme/` não commitadas, avise o
usuário antes de seguir: o pull vai sobrescrevê-las.

```bash
git status --short theme
```

## Passo 2 — edição (feita pelo usuário)

Passe estas instruções e **espere o usuário dizer que terminou**:

1. No admin da loja: **Loja online → Layout**.
2. A instalação de homolog (ID em `THEME_ID_HOMOLOG`) aparece como **rascunho** — abra a personalização
   dela, não a do layout publicado. A Nuvemshop permite um rascunho por vez.
3. Fazer as mudanças e usar **"Salvar rascunho"** — **não "Publicar"**.
4. Conferir no preview, logado no admin:
   `<STORE_URL>/?theme_installation_id=<THEME_ID_HOMOLOG>`

Para montar a URL:

```bash
(set -a && . ./.env && cd theme && nuvemshop theme preview --theme-id "$THEME_ID_HOMOLOG")
```

Os nomes de menu podem variar entre versões do admin; se o usuário não encontrar, peça um print.

## Passo 3 — trazer as mudanças

```bash
(set -a && . ./.env && cd theme && nuvemshop theme pull --theme-id "$THEME_ID_HOMOLOG")
```

O pull pede confirmação ("synced files will be deleted"). Sem TTY ele não recebe a resposta — nesse caso
peça ao usuário para rodar o comando no terminal dele.

Depois confira que nada caiu na raiz:

```bash
for p in blocks config layouts sections snippets static templates translations manifest.json; do [ -e "$p" ] && echo "RAIZ: $p"; done
```

Se aparecer algo, o pull rodou fora de `theme/`: compare com `theme/` antes de sugerir apagar.

## Passo 4 — reconstruir e religar

```bash
docker compose restart frontend
```

Espere o healthcheck e suba o watch:

```bash
for i in $(seq 1 40); do s=$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -q frontend)"); [ "$s" = healthy ] && break; sleep 3; done; echo "frontend: $s"
ls theme/static/css/tailwind.css theme/static/js/app.js
docker compose up -d theme
```

Se `frontend` não ficar `healthy`, veja `docker compose logs --tail=30 frontend`.

## Passo 5 — revisar e commitar

```bash
git status --short theme
git diff --stat theme
```

Resuma para o usuário o que mudou (seções da home em `theme/templates/pages/home.json`, configurações em
`theme/config/settings_data.json`, imagens etc.). O diff do `css_code` e do block `nuvemshop_dev_js` do
footer é esperado — é o build injetado.

**Páginas com `design/pages/<pagina>.yaml`** (ex.: home): o `compose.mjs` roda no restart do passo 4 e
reaplica o YAML por cima do que veio do pull.

- Seções **nativas**: o que o usuário mudou no Brand Editor fica, **exceto** as chaves que o YAML declara
  em `settings`/`blocks` — essas voltam ao valor do YAML. Se a mudança do editor deve valer, remova ou
  atualize a chave no YAML.
- **Componentes** (`cmp_*`): edições no block "Código" pelo editor são desfeitas — o conteúdo vem de
  `design/components/`. Leve a mudança para o `.html`.
- Seção **adicionada no editor** e ausente no YAML: fica no fim da página, com aviso no log. Pergunte ao
  usuário se ela entra no YAML (e em que posição).

Se estiver em `main`, crie uma branch antes. Commite só com o aval do usuário:

```bash
git add theme
git commit -m "feat(theme): <o que mudou no Brand Editor>"
```

Lembre: **mudança do Brand Editor não commitada é apagada no próximo PR** (o job `homolog` envia o repo).
Ofereça abrir o PR.
