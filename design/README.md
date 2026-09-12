# design/

Fonte do layout da loja. O `frontend/compose.mjs` transforma isto em `theme/templates/pages/*.json`
(roda no `npm run build`, no Docker em watch e no CI). Para ir do Figma até aqui, use a skill
`figma-to-theme`.

```
design/
├── pages/        uma página por arquivo: home.yaml -> theme/templates/pages/home.json
├── components/   componentes custom: HTML + Tailwind (tw:) + Alpine
└── assets/       imagens usadas como asset:<caminho> (servidas pelo jsDelivr)
```

## Páginas (`pages/<pagina>.yaml`)

A lista `sections` é a ordem na loja. Cada item é **nativo** ou **componente**:

```yaml
sections:
  - native: slideshow              # seção do Ipanema que já existe no JSON
    blocks:
      slide_1:
        settings:
          image: "asset:home/slide-1.webp"
  - component: beneficios          # design/components/beneficios.html
    settings: { vertical_padding: 32 }
  - native: vitrine                # seção nativa nova: precisa de type
    type: product-list
    settings: { title: "Novidades" }
unlisted: keep                     # keep (padrão) | remove
```

| | Seção nativa (`native`) | Componente (`component`) |
|---|---|---|
| O que é | seção do Ipanema (`theme/sections/<type>.tpl`) | HTML próprio numa seção "Personalizada" (`cmp_<nome>`) |
| Dados da loja (produtos, preços, categorias) | ✅ | ❌ sem Twig |
| Editável no Brand Editor | ✅ | ❌ muda só pelo repo |
| Settings válidas | as do `{% schema %}` do `.tpl` | as da seção `custom` (padding, largura…) |

**Quem manda em quê:**

- **Nativas**: o Brand Editor manda. O YAML só sobrescreve as chaves que declarar; o resto vem do JSON
  atual (traga com `theme pull` — skill `brand-editor-sync`).
- **Componentes**: o repo manda. Edição do block "Código" pelo Brand Editor é desfeita no próximo build.
- **Seções fora do YAML** (ex.: adicionadas no Brand Editor) ficam no fim, com aviso. `unlisted: remove` tira.
- **Apagar uma chave do YAML não desfaz o valor**: o JSON já guardou o valor anterior e passa a ser a base.
  Para voltar ao padrão, apague a chave também em `theme/templates/pages/<pagina>.json` (ou mude pelo Brand Editor).

## Componentes (`components/<nome>.html`)

- Classes Tailwind **sempre com `tw:`** — variantes depois do prefixo: `tw:md:grid-cols-3`, `tw:hover:underline`.
- Cores e fontes do Brand Editor: `tw:bg-brand`, `tw:text-brand-accent`, `tw:bg-brand-bg`,
  `tw:text-brand-text`, `tw:font-display`, `tw:font-sans`.
- Imagens: `src="asset:home/banner.webp"`.
- Interação com Alpine; componentes JS em `frontend/src/js/components/`.
- Sem Twig, sem id em CSS. Comentários HTML são removidos no build.

## Assets e jsDelivr

`asset:home/x.webp` vira `https://cdn.jsdelivr.net/gh/<repo>@<commit>/design/assets/home/x.webp`.

- Local: commit = `HEAD` do checkout. **O commit precisa estar no GitHub** — commite, dê push e rode
  `docker compose restart frontend` antes de olhar o preview.
- CI: usa o commit do PR (`ASSETS_REF`).
- O repo é público: tudo em `assets/` fica público.

## Quando o fork for liberado

Cada `components/<nome>.html` pode virar `theme/sections/<nome>.tpl` com `{% schema %}` — ganha Twig,
dados da loja e campos editáveis no Brand Editor, sem refazer o HTML.
