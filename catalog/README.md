# catalog — importação de catálogo

Sobe **categorias, produtos (com variações) e imagens** para a loja a partir do CSV no formato de
importação/exportação da Nuvemshop (Produtos → Exportar no admin). Só biblioteca padrão do Python;
credenciais do `.env` da raiz.

```bash
python3 -m catalog validate produtos.csv                        # só valida o arquivo
python3 -m catalog import produtos.csv                          # dry-run: mostra o plano, não grava
python3 -m catalog import produtos.csv --apply                  # grava na loja
python3 -m catalog import produtos.csv --apply --images-dir fotos/
python3 -m catalog import produtos.csv --apply --update         # atualiza o que já existe
```

Rode da **raiz do repo**. Cada execução gera um relatório em `catalog/reports/` (gitignorado).

## O que acontece

1. **Valida** o CSV — erros impedem só o produto com problema; avisos e infos são listados.
2. **Categorias**: reaproveita as existentes (mesmo nome, sem diferenciar maiúsculas) e cria as que
   faltam. `Roupas > Camisetas` cria a hierarquia; várias categorias separadas por vírgula.
3. **Produtos**: cria com todas as variações numa chamada. Produto que já existe (mesmo
   **Identificador URL** ou algum **SKU**) é **pulado** — ou atualizado com `--update`
   (campos do produto + variações casadas por SKU ou valores; variações novas são criadas).
4. **Imagens**: só para produto que ainda não tem nenhuma (rodar de novo não duplica).

Rate limit da API (balde de 40, `x-rate-limit-*`) é respeitado; 429 e 5xx são repetidos com espera.

## Formato do CSV

As colunas padrão da exportação da Nuvemshop (separador `;` ou `,`, UTF-8 ou Windows-1252).

| Coluna | Uso |
|---|---|
| Identificador URL | handle do produto e **chave** para agrupar variações e achar o produto na loja |
| Nome | preenchido só na 1ª linha do produto; linhas seguintes com o mesmo identificador e Nome vazio = outras variações |
| Categorias | `Camisetas` · `Roupas > Camisetas` · `A, B` |
| Nome/Valor da variação 1–3 | atributos (Cor, Tamanho…) — máx. 3 |
| Preço, Preço promocional, Custo | aceita `59,90`, `59.90`, `R$ 1.234,56` |
| Estoque | vazio = **ilimitado** |
| Peso/Altura/Largura/Comprimento | kg / cm |
| Exibir na loja, Visibilidade | `Visível` / `Oculto` / `Não listado` |
| Frete gratis, Produto Físico | `SIM` / `NÃO` |
| Título/Descrição para SEO | cortados em 70 / 320 caracteres (limite da API), com aviso |
| MPN, Sexo, Faixa etária | **não enviados** — a API de produtos não tem esses campos (aparece como info) |
| **Imagens** (opcional, extra) | URLs separadas por vírgula, espaço ou `\|` |

### Imagens — de onde vêm (nesta ordem)

1. **Coluna `Imagens`** no CSV → enviadas por URL (`src`).
2. **`--images-dir pasta/`** → arquivos com o nome do produto: `<handle>.jpg`, `<handle>-2.jpg`,
   `<handle>_3.webp` (ordem natural) — ou pelo SKU, `<SKU>.png`. Enviados em base64, então não
   precisam estar publicados. Formatos jpg/png/gif/webp, até 10 MB.
3. **`--placeholder-images`** → imagens de exemplo do próprio tema (loja de demonstração sem fotos).

A primeira imagem é a capa; `alt` = nome do produto.

## Dicas para o CSV

- **Tamanhos numa linha só não viram seletor útil.** Produto com `Tamanho = M` e mais nada aparece
  com um seletor de uma opção. Para ter P/M/G, repita o **Identificador URL** em uma linha por
  tamanho (Nome vazio nas linhas seguintes) — o importador agrupa.
- **SKU único por variação** — é por ele que o `--update` acha a variação certa.
- **Não use o mesmo número no fim do handle e das fotos**: `camiseta-2.jpg` é lido como 2ª foto de
  `camiseta`. Prefira handles sem número final ou fotos pelo SKU.

## Testes

```bash
python3 -m unittest discover -s catalog/tests -t .
```

Cobrem leitura/validação do CSV, payloads, imagens, dry-run (só GET), criação com retry em 429 e
erro da API virando item do relatório — contra uma API simulada.
