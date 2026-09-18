# checkout-quick — layout do checkout (app NubeSDK)

Todo o layout do checkout na identidade Quick Digital **num script só**. O checkout da Nuvemshop é
hospedado — nenhum tema altera o HTML dele —; o caminho oficial para colocar UI lá é um app
**NubeSDK**: o script roda isolado num Web Worker e desenha componentes em *slots* predefinidos.
Um app pode chamar `nube.render()` em quantos slots quiser, então cada parte do layout é um módulo
em `src/features/`.

## As partes

| Parte | Slot | Etapas | Texto padrão |
|---|---|---|---|
| **faixa-topo** | `after_header` | entrega, pagamento | 🔒 Compra 100% segura · 🚚 Frete grátis acima de R$ 299,00 · 💳 Até 6x sem juros no cartão |
| **frete-gratis** | `after_line_items_price` | entrega, pagamento | Faltam R$ X para ganhar frete grátis · barra · Frete grátis em compras a partir de R$ 299,00 — ao atingir: "Parabéns! Seu pedido tem frete grátis 🎉" |
| **selos-pagamento** | `before_payment_options` | pagamento | 🔒 Pagamento rápido e protegido · Ambiente seguro, com seus dados enviados de forma criptografada. É só escolher como pagar e finalizar. · Até 6x sem juros no cartão |
| **rodape** | `after_main_content` | entrega, pagamento | Travou em alguma etapa? A gente resolve rápido. · [Fale com a gente] (`/contato/` da loja) · [Chamar no WhatsApp] · QuickStart · compra segura |
| **pos-compra** | `after_order_number` | pedido confirmado | Pedido confirmado! 🚀 · Agora é com a gente: cada atualização do seu pedido chega no seu e-mail. · [Alguma dúvida? Chama no WhatsApp] |

Tom da Quick (direto, "agilidade/performance"), **sem prometer o que a loja não garante**: nada de
prazo de entrega ou política de troca. O frete grátis e o parcelamento repetem o que a loja já anuncia
no topo do site — e ambos são configuráveis. Links de WhatsApp só aparecem com o número configurado.

Cada parte se refaz sozinha quando carrinho, etapa ou frete mudam (`render` com função do estado).

## Configurações do app (portal de parceiros)

Lidas com `nube.getAppSettings()` — o SDK entrega `{ chave: { type, value } }` e só tem os tipos
`string`, `enrichedText`, `image` e `collection` (não há booleano).

| Chave | Tipo | Padrão | Exemplo |
|---|---|---|---|
| `free_shipping_threshold` | string | `299` | `249,90` |
| `disabled_features` | collection de string | nenhuma | `["rodape", "pos-compra"]` |
| `top_bar_messages` | collection de string | os 3 textos acima | `["Entrega expressa", "Troca fácil"]` |
| `payment_note` | string | `Até 6x sem juros no cartão` | `Pix com aprovação na hora` |
| `whatsapp` | string (com DDI) | sem WhatsApp | `5521999998888` |

Mudar configuração **não** exige nova versão do script.

> A barra de frete grátis é **informativa**: quem concede o frete grátis é a regra configurada na
> loja. Mantenha `free_shipping_threshold` igual ao valor dela.

## Estrutura

```
src/
  main.tsx              App(nube): registra cada parte no seu slot, filtrando por etapa
  settings.ts           leitura das configurações (formato { type, value } do SDK)
  checkout.ts           etapa atual, URL da loja, link de WhatsApp
  free-shipping.ts      regra da barra (quanto falta, progresso, moeda da loja)
  brand.ts              cores da Quick
  features/             uma parte por arquivo + index.ts com a ordem
```

Nova parte: crie `src/features/<nome>.tsx` exportando um `Feature` (`name`, `slot`, `steps`,
`render`), adicione em `features/index.ts` e o nome em `FEATURE_NAMES` (`settings.ts`). Slots
disponíveis: [Checkout Slots](https://dev.nuvemshop.com.br/en/docs/applications/nube-sdk/slots/checkout-slots).

Cuidados do SDK:
- não aceita `false` como filho (`{cond && <X/>}` do React não compila) — use listas;
- não dá para esconder/mover campos nativos nem trocar o cabeçalho da Nuvemshop, só acrescentar;
- fora do Worker o runtime exige `self.__APP_DATA__.id` (a plataforma injeta).

## Desenvolvimento

```bash
cd nube-apps/checkout-quick
npm install
npm test            # vitest: configurações, regra, cada parte e o App (slots × etapas)
npm run typecheck   # tipos oficiais (@tiendanube/nube-sdk-types)
npm run build       # -> dist/main.min.js (ESM único, ~10 KB)
npm run dev         # watch + http://localhost:8080/main.min.js (CORS)
```

CI: `.github/workflows/nube-apps.yml` roda typecheck, testes e build em PRs que tocam `nube-apps/**`
e publica o `main.min.js` como artefato.

## Publicar uma versão

O script já existe no portal (**Dev01 → Scripts → "Barra de frete grátis"**, id da associação na loja
`10349`: checkout, instalação automática, **Use NubeSDK** ligado). Para cada mudança:

1. `npm run build` (ou baixe o artefato do CI);
2. no portal, edite o script e **carregue o `dist/main.min.js` como nova versão**;
3. **publique** a versão (enquanto está em teste, só roda na loja demo);
4. confira: `GET /scripts` deve mostrar `status: "active"` e o novo `current_version.version`.

Evento atual: `onload` (a documentação da Nuvemshop pede aprovação para `onload` na loja; no checkout
ele está funcionando). Se algo não carregar, `onfirstinteraction` não depende de aprovação.
