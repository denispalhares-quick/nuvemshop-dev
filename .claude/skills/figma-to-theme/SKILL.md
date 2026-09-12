---
name: figma-to-theme
description: Transforma um layout do Figma em páginas do tema Nuvemshop (Ipanema) e leva até o deploy — confere credenciais e Docker, lê o frame no Figma, aplica tokens (cores/fontes), mapeia cada bloco para seção nativa do Ipanema ou componente custom (HTML + Tailwind tw:), exporta imagens para design/assets, aplica no homolog, abre PR e acompanha o CI; publicar só com ok explícito. Use quando o usuário mandar um link do Figma, pedir "aplicar o layout", "montar a home a partir do Figma", "implementar o design na loja" ou quiser criar/alterar componentes custom do tema.
---

# Figma → tema Nuvemshop

Fluxo: **credenciais → Docker → Figma → aplicar → homolog → PR/CI → deploy (só com ok)**.

Leia antes, se ainda não leu nesta sessão: `design/README.md` (formato de páginas e componentes) e a
seção "Sem fork" de `docs/frontend.md`.

## Regras que não mudam

- **Nunca publique sem ok explícito** do usuário naquela conversa (`nuvemshop theme publish`, botão
  "Salvar e publicar" do Brand Editor, secret `THEME_ID_PROD`). Publicar troca a loja no ar.
- **Sem fork**, só `theme/templates/**` e `theme/config/settings_data.json` chegam na loja. Não crie nem
  edite `theme/sections/`, `blocks/`, `snippets/`, `layouts/` ou `static/` — o push ignora ("Skipped").
- **Não edite `theme/templates/pages/*.json` à mão** para páginas que têm `design/pages/*.yaml`: o
  `compose.mjs` sobrescreve. Edite o YAML.
- Tokens e secrets nunca em mensagens ou comandos visíveis. IDs vêm do `.env` (carregue num subshell:
  `(set -a && . ./.env && ...)`).
- Ajustes feitos pelo usuário no Brand Editor seguem a skill `brand-editor-sync`.

## 1. Credenciais e ambiente

Rode e reporte só o que falhar:

```bash
(set -a && . ./.env && for v in TIENDANUBE_ACCESS_TOKEN TIENDANUBE_STORE_ID THEME_ID_HOMOLOG; do [ -n "$(printenv "$v")" ] && echo "ok $v" || echo "FALTA $v"; done)
test -f theme/.nuvem && echo "ok theme/.nuvem" || echo "FALTA theme/.nuvem (nuvemshop theme authorize dentro de theme/)"
gh auth status >/dev/null 2>&1 && echo "ok gh" || echo "FALTA gh auth login"
docker compose ps --format 'table {{.Service}}\t{{.Status}}'
```

- Faltando `.env`/token: aponte o README (seção de credenciais) — não gere tokens pelo usuário.
- Docker parado: `docker compose up -d`. `frontend` precisa ficar `healthy`; se não, `docker compose restart frontend`.
- Figma: chame a tool `whoami` do MCP do Figma. Sem acesso ao arquivo, peça ao usuário para compartilhar.
- Trabalhe numa branch (`git switch -c feat/<pagina>-figma`), nunca em `main`.

## 2. Ler o Figma

Precisa de uma URL de frame (`figma.com/design/<fileKey>/...?node-id=<id>`). Peça frames **desktop e
mobile** da página.

1. **Carregue a skill `figma:figma-design-to-code` antes de `get_design_context`** (obrigatório pelo MCP).
2. `get_metadata` no frame → árvore de filhos. Os filhos diretos de primeiro nível costumam ser as seções.
3. `get_screenshot` do frame inteiro → referência visual para mostrar ao usuário e comparar no fim.
4. `get_variable_defs` → cores, tipografia, espaçamentos nomeados.
5. `get_design_context` **por seção** (não no frame inteiro — sai grande e impreciso).

Resuma para o usuário a lista de seções que você identificou antes de gerar código.

## 3. Tokens globais → `theme/config/settings_data.json`

Edite só estas chaves dentro de `settings` (o resto é do Brand Editor; o `inject.mjs` preserva):

| Figma | chave |
|---|---|
| fundo da página | `background_color` |
| texto principal | `text_color` |
| cor de destaque / links | `accent_color` |
| botão primário (fundo / texto) | `button_primary_background_color` / `button_primary_foreground_color` |
| botão secundário | `button_secondary_background_color` / `button_secondary_foreground_color` |
| cabeçalho (fundo / texto) | `header_background_color` / `header_foreground_color` |
| rodapé (fundo / texto) | `footer_background_color` / `footer_foreground_color` |
| etiqueta de produto | `label_background_color` / `label_foreground_color` |
| fonte de títulos | `font_headings` — formato `"\"Nome\", sans-serif"` |
| fonte de texto | `font_rest` — mesmo formato |

**Fontes**: só as da lista `set fonts` em `theme/layouts/resources/style-tokens.tpl` carregam. Fonte do
Figma fora da lista → escolha a mais próxima da lista e **avise o usuário** da troca.

Esses valores também alimentam o Tailwind (`tw:bg-brand`, `tw:text-brand-accent`, `tw:font-display`…).

## 4. Mapear cada seção: nativa ou componente

**Use seção nativa** quando o bloco precisar de dados da loja (produtos, preço, estoque, categorias,
posts) — componente não tem Twig — ou quando um tipo nativo reproduz o layout pelas próprias settings.
**Use componente** para blocos puramente visuais/marketing sem equivalente fiel.

| Padrão no Figma | tipo nativo (`theme/sections/<tipo>.tpl`) |
|---|---|
| banner grande com texto/CTA | `hero`, `hero-divided` |
| carrossel de banners | `slideshow` |
| grade de banners/categorias com imagem | `banners`, `featured-categories` |
| vitrine de produtos | `product-list` |
| um produto em destaque | `featured-product` |
| imagem + texto lado a lado | `image-with-text`, `video-with-text` |
| ícones com texto (benefícios) | `icon-text` |
| depoimentos | `testimonials` |
| perguntas frequentes | `faq` |
| newsletter | `newsletter` |
| logos de marcas | `featured-brands` |
| contagem regressiva com produtos | `timer-offers` |
| texto editorial | `rich-text` |
| barra de avisos no topo | `announcement-bar` (fica no header: `templates/layout/header.json`) |

Para cada nativa, **leia o `{% schema %}` do `.tpl`** (e dos blocks em `theme/blocks/`) para saber as
settings válidas, e use valores de settings existentes nos JSON do tema como referência de formato.
Setting inventada é ignorada pela plataforma.

Mostre o mapeamento ao usuário (seção do Figma → nativa/componente e por quê) antes de aplicar.

## 5. Gerar

### Imagens → `design/assets/<pagina>/`

- Exporte com a tool `download_assets` do MCP do Figma (ou as URLs de `get_design_context`), salve em
  `design/assets/<pagina>/<nome-descritivo>.webp` (converta para webp se vier png/jpg grande).
- Referencie como `asset:<pagina>/<arquivo>.webp` — no YAML e no HTML.
- Largura máxima ~2400px para banners, ~1200px para cards. Nada de imagem acima de 1 MB.

### Página → `design/pages/<pagina>.yaml`

```yaml
sections:
  - native: slideshow            # existente: só sobrescreve o que declarar
    blocks:
      slide_1:
        settings: { image: "asset:home/slide-1.webp" }
  - component: beneficios        # design/components/beneficios.html
  - native: vitrine_novidades    # nova: precisa de type
    type: product-list
    settings: { ... }            # conforme o schema de sections/product-list.tpl
```

### Componentes → `design/components/<nome>.html`

- HTML semântico, **todas as classes com prefixo `tw:`** (variantes depois do prefixo: `tw:md:grid-cols-3`,
  `tw:hover:opacity-80`). Mobile first; breakpoints `tw:md:` / `tw:lg:` conforme os frames do Figma.
- Cores e fontes via tokens (`tw:bg-brand`, `tw:text-brand-text`, `tw:font-display`); valores do Figma
  que não são token → valores arbitrários (`tw:bg-[#F4EFE9]`, `tw:text-[40px]`).
- Imagens: `<img src="asset:..." alt="..." loading="lazy" width height>`.
- Interação: Alpine (`x-data`, `x-show`). Componente JS novo → `frontend/src/js/components/` e registro
  em `frontend/src/js/main.js`.
- Sem Twig, sem `<style>` com ids, sem scripts externos além do Alpine.

## 6. Aplicar no homolog

As URLs do jsDelivr apontam para o commit atual — **o commit precisa estar no GitHub** antes do preview:

```bash
git add design theme/config/settings_data.json frontend/src
git commit -m "feat(design): <pagina> a partir do Figma"
git push -u origin HEAD
docker compose restart frontend     # recompõe com o novo HEAD; o theme watch envia
```

Confirme:

```bash
docker compose logs --tail=20 frontend | grep -E "compose|inject|✗|⚠"
docker compose logs --tail=20 theme
docker compose exec -T theme sh -c 'nuvemshop theme diff --theme-id "$THEME_ID_HOMOLOG"'
```

- `compose: ✗` → erro no YAML/componente; corrija e repita.
- `theme` com erro de validação num setting → confira o schema da seção.
- `diff` com "0 changes" = homolog em sincronia.

Preview (o usuário abre **logado no admin**; você não consegue ver sem login):
`<STORE_URL do repo var>/?theme_installation_id=<THEME_ID_HOMOLOG>`. Peça um print e compare com o
`get_screenshot` do Figma, seção por seção. Itere nos arquivos de `design/` e repita o passo 6.

## 7. PR e CI

```bash
gh pr create --base main --title "feat(design): <pagina> a partir do Figma" --body "<mapeamento + prints>"
```

Acompanhe o run do PR (`gh run list --branch <branch>` → `gh run watch <id> --exit-status`) e traga o
resultado de `diff` e `homolog`. Falhou → leia `gh run view <id> --log-failed` e corrija.

Merge só com ok do usuário.

## 8. Deploy (só com ok explícito)

Enquanto `THEME_ID_PROD` estiver vazio, merge na `main` **não** publica nada (o job `prod` pula).
Publicar é trocar o tema da loja. Antes, mostre ao usuário o que vai acontecer e peça confirmação
explícita. Com o ok:

1. `(set -a && . ./.env && cd theme && nuvemshop theme publish --theme-id "$THEME_ID_HOMOLOG")`
2. A instalação publicada vira a de prod; o tema antigo precisa sair para caber o novo homolog
   (limite de 2): `nuvemshop theme delete --theme-id <antigo>` — **confirme de novo**, é irreversível.
3. `nuvemshop theme clone --theme-id <publicado> --title "<nome> Homolog"` → novo homolog.
4. Atualizar `.env` e secrets (`THEME_ID_PROD`, `THEME_ID_HOMOLOG`) — o usuário roda os `gh secret set`.
