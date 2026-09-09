# Frontend do tema

Como o CSS e o JS deste repo são escritos, construídos e entregues ao tema.

## O que a plataforma realmente executa

Não é "só HTML, CSS e JS". Três camadas rodam **no servidor da Nuvemshop**:

| Camada | Onde roda | Consequência |
|---|---|---|
| **Twig** (`.tpl`) | servidor | o HTML já chega pronto no navegador — nada de SPA |
| **SASS** (`.scss.tpl`) | servidor | dá para interpolar settings do tema dentro do CSS |
| CSS/JS estáticos (`static/`) | navegador | é aqui que entra o build local |

Por isso o build local cuida só de Tailwind e do bundle de JS. O que precisa dos
settings do lojista fica em `.scss.tpl` e é compilado lá.

## Stack

- **Tailwind v4** → `theme/static/css/style.css`
- **esbuild + Alpine.js** → `theme/static/js/store.js`
- **`tokens.scss.tpl`** → ponte entre o Brand Editor e o Tailwind

Fonte em `frontend/src/`, saída em `theme/static/`. A saída é **gitignorada** — quem
gera é o build (local ou CI).

```
frontend/
├── package.json
├── build.mjs                  esbuild, saída de nome fixo
└── src/
    ├── css/main.css           Tailwind + @theme + @source
    └── js/
        ├── main.js            entrypoint: registra os componentes Alpine
        └── components/        um arquivo por componente

theme/static/
├── css/tokens.scss.tpl        FONTE (compilado pela Nuvemshop)
├── css/style.css              GERADO pelo build
└── js/store.js                GERADO pelo build
```

## Comandos

```bash
cd frontend
npm install        # primeira vez
npm run build      # gera style.css e store.js minificados
npm run dev        # watch de CSS e JS ao mesmo tempo
```

Fluxo completo de desenvolvimento, com recarga na loja:

```bash
# terminal 1 — recompila o build a cada save
cd frontend && npm run dev

# terminal 2 — envia para a instalação de homologação
cd theme && nuvemshop theme watch --theme-id $THEME_ID_HOMOLOG
```

## Referenciando os assets no `.tpl`

A plataforma usa o filtro `static_url`, encadeado com `css_tag` / `script_tag`:

```twig
{{ 'css/tokens.scss.tpl' | static_url | css_tag }}
{{ 'css/style.css'       | static_url | css_tag }}
{{ 'js/store.js'         | static_url | script_tag }}
```

O `tokens.scss.tpl` precisa vir **antes** do `style.css`: ele define as variáveis
que o Tailwind consome.

Dentro de CSS/SASS, imagens também precisam do helper — caminho relativo não funciona:

```twig
.hero { background-image: url("{{ 'img/hero.jpg' | static_url }}"); }
```

## Por que o bundle não tem hash no nome

O `.tpl` referencia o arquivo **literalmente**. Não existe manifest de assets na
plataforma para reescrever `store.a3f9c1.js` a cada build, então a saída tem nome
fixo (`style.css`, `store.js`).

**Isso deixa o cache-busting em aberto** — não está documentado se o `static_url`
versiona a URL a cada revisão do tema. Confirme no primeiro deploy: publique uma
mudança de cor óbvia e veja se aparece sem hard refresh. Se não aparecer, a saída é
um sufixo manual controlado por setting (`style.css?v={{ settings.asset_version }}`).

## Ponte com o Brand Editor

Sem isso, você ganha Tailwind e perde o editor visual do lojista — troca ruim
para loja de cliente.

`theme/static/css/tokens.scss.tpl` (compilado pela Nuvemshop, com os settings):

```scss
:root {
  --brand-primary: {{ settings.primary_color }};
}
```

`frontend/src/css/main.css` (compilado localmente, consome a variável):

```css
@theme {
  --color-brand: var(--brand-primary, #1a1a1a);
}
```

No template, `bg-brand` passa a seguir a cor escolhida no editor.

> Os nomes dos settings em `tokens.scss.tpl` são um palpite e **precisam ser
> conferidos** contra o tema real depois do `theme pull` — cada tema define os
> seus. Setting inexistente renderiza vazio e a variável cai no fallback.

## JavaScript: progressive enhancement

O HTML já vem do servidor, então o JS **melhora** o que existe, não assume o DOM.
Padrão: um `x-data` por bloco, estado local, sem store global.

```twig
<div x-data="miniCart()" x-cloak>
  <button @click="toggle()" class="js-minicart-toggle">Carrinho</button>
  <aside x-show="open" x-collapse @click.outside="close()">…</aside>
</div>
```

Use os hooks `js-*` como gancho de comportamento e mantenha as classes de estilo
separadas — trocar o visual não pode quebrar o JS.

### O que evitar

**React/Vue como SPA.** Brigaria com o Twig que já renderiza tudo, prejudica LCP e
SEO da vitrine, e o checkout nem é seu — você reescreveria a parte fácil e não
tocaria na difícil. Para uma ilha interativa pesada (um configurador de produto,
por exemplo), aí sim vale um Preact isolado num único ponto de montagem.

**Seletores de ID no CSS.** IDs são reservados para funções internas da plataforma.
Use classes.

## Restrições da plataforma que afetam o front

- **Fork obrigatório**: sem forkar a instalação, só dá para enviar `templates/`,
  `custom/` e `config/settings_data.json`. `static/`, `sections/`, `blocks/`,
  `layouts/` e `snippets/` ficam bloqueados. O fork é irreversível na instalação.
- **Máximo de 2 instalações de tema por loja** — homolog e prod cabem exatos, sem
  folga para uma terceira.
- **Arquivos vazios (0 bytes) são ignorados** pela CLI no push.
- **Ipanema é o único tema base sectionable** hoje; começar de um tema clássico te
  prende ao `config/settings.txt` em vez de sections editáveis.
- Scripts de CDN externo são permitidos (`{{ '//cdn…/lib.js' | script_tag(true) }}`),
  mas cada um é um request a mais no caminho crítico da vitrine.

## Sections e blocks

O schema fica dentro do próprio `.tpl` da section:

```twig
<section class="banner" {{ block | block_attributes }}>
  {{ block.settings.text | raw }}
</section>

{% schema %}
{
  "name": "Banner",
  "settings": [
    { "type": "setting", "setting_type": "text", "id": "text", "label": "t:settings.text" }
  ]
}
{% endschema %}
```

Blocks só ficam editáveis no Brand Editor se tiverem o filtro `block_attributes`.
Tipos de setting disponíveis: `text`, `richtext`, `html`, `url`, `select`, `radio`,
`toggle`, `checkbox`, `range`, `color`, `image_picker`, `text_alignment`, `alignment`.

## Performance

```bash
cd theme && nuvemshop theme performance --device mobile --detailed
```

Vale rodar antes de publicar. Vitrine lenta custa conversão, e o peso do bundle é
a parte que está sob seu controle.

## Referências

- [Static](https://docs.nuvemshop.com.br/help/static) · [Métodos (filtros Twig)](https://docs.nuvemshop.com.br/help/mtodos)
- [Carregar CSS](https://docs.nuvemshop.com.br/help/como-carrego-uma-folha-de-estilos-css) · [Carregar JS](https://docs.nuvemshop.com.br/help/como-carrego-um-javascript)
- [Sections e Blocks](https://docs.nuvemshop.com.br/help/sections-e-blocks) · [Schema reference](https://docs.nuvemshop.com.br/help/schema-reference) · [JSON templates](https://docs.nuvemshop.com.br/help/json-templates)
- [Hooks de JavaScript](https://docs.nuvemshop.com.br/help/hooks-de-javascript) · [Seletores ID](https://docs.nuvemshop.com.br/help/selectores-id)
- [Temas sectionable](https://docs.nuvemshop.com.br/help/sectionable-themes) · [CLI — desenvolvimento de tema](https://dev.nuvemshop.com.br/docs/developer-tools/cli/theme-development)
