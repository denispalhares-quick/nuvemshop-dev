# App NubeSDK — barra de frete grátis no checkout

Mostra, logo abaixo dos totais do pedido, quanto falta para o frete grátis — e comemora quando o
cliente atinge. Visual da Quick Digital (fundo `#FFF1EC`, texto `#000066`, barra `#FB4516`).

```
┌────────────────────────────────────────────┐
│ Faltam R$ 124,10 para ganhar frete grátis  │
│ ██████████████░░░░░░░░░░  58%              │
│ Frete grátis em compras a partir de R$ 299 │
└────────────────────────────────────────────┘
```

O checkout da Nuvemshop é hospedado — nenhum tema altera o HTML dele. O caminho oficial para colocar
UI lá é um **app NubeSDK**: o script roda isolado num Web Worker e desenha componentes em *slots*
predefinidos. Base: template oficial `minimal-ui-jsx` do
[TiendaNube/nube-sdk](https://github.com/TiendaNube/nube-sdk).

## Como funciona

| | |
|---|---|
| Slot | `after_line_items_price` — abaixo dos totais, etapas **start** (entrega) e **payment** |
| Atualização | `nube.render(slot, (state) => …)`: refaz sozinho quando o carrinho muda |
| Base de cálculo | `subtotal − desconto de promoção − desconto de cupom` (sem frete e sem desconto de meio de pagamento) |
| Valor mínimo | configuração do app `free_shipping_threshold`; sem ela, **R$ 299** (o mesmo aviso do topo da loja) |
| Moeda | `state.store.currency_details` (símbolo e separadores da loja) |

A barra é **informativa**: quem concede o frete grátis é a regra/promoção configurada na loja
(Nuvem Envio ou meios de envio). Mantenha o mesmo valor mínimo nos dois lugares.

## Desenvolvimento

```bash
cd nube-apps/frete-gratis
npm install
npm test            # vitest: regra + árvore de componentes
npm run typecheck   # tipos oficiais do SDK (@tiendanube/nube-sdk-types)
npm run build       # -> dist/main.min.js (ESM único, ~6 KB)
npm run dev         # build em watch + servidor em http://localhost:8080/main.min.js (CORS)
```

- `src/free-shipping.ts` — regra pura (quanto falta, progresso, formatação de dinheiro).
- `src/main.tsx` — componente e `App(nube)`.
- O SDK **não aceita `false` como filho** (`{cond && <X/>}` do React não compila) — use listas.
- Fora do Worker o runtime exige `self.__APP_DATA__.id` (a plataforma injeta); nos testes os
  componentes são simulados, como no template oficial.

O CI (`.github/workflows/nube-apps.yml`) roda typecheck, testes e build em PRs que tocam
`nube-apps/**` e publica o `main.min.js` como artefato.

## Publicar na loja

Feito pelo **dono do app no portal de parceiros** (login do usuário — não automatizado aqui):

1. No app (ex.: *Dev01*), garanta a permissão **Scripts** e ligue a opção **"Uses NubeSDK"**.
2. **Criar script** com local **Checkout**, usando o `dist/main.min.js` (do `npm run build` ou do
   artefato do CI).
3. Para testar antes de publicar: rode `npm run dev` e aponte o script de desenvolvimento para
   `http://localhost:8080/main.min.js`, com o app instalado na loja de teste.
4. Configure `free_shipping_threshold` nas configurações do app, se quiser outro valor mínimo.

> O fluxo exato da tela do portal (envio do arquivo × URL, ativação na loja) não está detalhado na
> documentação pública — confira na própria tela e em
> [DevHub › NubeSDK](https://dev.nuvemshop.com.br/en/docs/applications/nube-sdk/overview).
