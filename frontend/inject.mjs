/**
 * Leva o build para o tema SEM fork.
 *
 * A plataforma ainda não libera fork ("Forking not yet allowed"), e sem fork o
 * `theme push/watch` só envia templates/ e config/settings_data.json — static/,
 * layouts/ e sections/ são ignorados. Então o build entra por esses dois arquivos:
 *
 *   theme/static/css/tailwind.css -> config/settings_data.json  settings.css_code
 *     (o layout do Ipanema imprime {{ settings.css_code | raw }} em todas as páginas;
 *      o CSS gerado fica entre marcadores e o resto do campo é preservado)
 *
 *   theme/static/js/app.js -> templates/layout/footer.json
 *     (section "custom" + block "code" com o JS inline e o Alpine via CDN,
 *      na versão travada no package-lock)
 *
 * Só grava quando o conteúdo muda, para não entrar em loop com os watchers.
 *
 * Uso: node inject.mjs [--watch]
 */
import { existsSync, readFileSync, watch, writeFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CSS_OUT = resolve(root, "theme/static/css/tailwind.css");
const JS_OUT = resolve(root, "theme/static/js/app.js");
const SETTINGS = resolve(root, "theme/config/settings_data.json");
const FOOTER = resolve(root, "theme/templates/layout/footer.json");

const CSS_START = "/* nuvemshop-dev:start — gerado por frontend/inject.mjs, não edite este trecho */";
const CSS_END = "/* nuvemshop-dev:end */";
const SECTION_ID = "nuvemshop_dev_js";

const lock = JSON.parse(readFileSync(resolve(root, "frontend/package-lock.json"), "utf8"));
const version = (name) => lock.packages[`node_modules/${name}`].version;

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const kb = (s) => `${(Buffer.byteLength(s) / 1024).toFixed(1)}kb`;

// Mesmo formato dos JSON que vêm do `theme pull`: 2 espaços, UTF-8 cru, \n no fim.
function writeJson(file, data) {
  const out = JSON.stringify(data, null, 2) + "\n";
  if (readFileSync(file, "utf8") === out) return false;
  writeFileSync(file, out);
  return true;
}

function injectCss() {
  if (!existsSync(CSS_OUT)) return;
  const css = readFileSync(CSS_OUT, "utf8")
    .replace(/\/\*![\s\S]*?\*\/\s*/, "") // banner de licença do Tailwind
    .trim();

  const data = JSON.parse(readFileSync(SETTINGS, "utf8"));
  const current = data.settings.css_code ?? "";
  const block = `${CSS_START}\n${css}\n${CSS_END}`;
  const re = new RegExp(`${escapeRe(CSS_START)}[\\s\\S]*?${escapeRe(CSS_END)}`);

  data.settings.css_code = re.test(current)
    ? current.replace(re, () => block)
    : [current.trim(), block].filter(Boolean).join("\n\n");

  if (writeJson(SETTINGS, data)) console.log(`inject: css_code atualizado (${kb(css)})`);
}

function injectJs() {
  if (!existsSync(JS_OUT)) return;
  const js = readFileSync(JS_OUT, "utf8")
    .replace(/\/\/# sourceMappingURL=.*$/m, "") // sourcemap inline do modo watch
    .replace(/<\/script/gi, "<\\/script")
    .trim();

  // Ordem importa: o inline registra o listener de alpine:init antes dos
  // scripts defer (plugin primeiro, depois o core) executarem.
  const code = [
    `<script>${js}</script>`,
    `<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@${version("@alpinejs/collapse")}/dist/cdn.min.js"></script>`,
    `<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@${version("alpinejs")}/dist/cdn.min.js"></script>`,
  ].join("\n");

  const data = JSON.parse(readFileSync(FOOTER, "utf8"));
  data.sections[SECTION_ID] = {
    type: "custom",
    settings: { section_width: "full", vertical_padding: 0, horizontal_padding: 0 },
    blocks: { code: { type: "code", settings: { code } } },
    block_order: ["code"],
  };
  if (!data.order.includes(SECTION_ID)) data.order.push(SECTION_ID);

  if (writeJson(FOOTER, data)) console.log(`inject: block de JS no footer atualizado (${kb(js)})`);
}

function run(fn) {
  try {
    fn();
  } catch (err) {
    // arquivo no meio da escrita pelo tailwind/esbuild — o próximo evento resolve
    console.error(`inject: ${err.message}`);
  }
}

run(injectCss);
run(injectJs);

if (process.argv.includes("--watch")) {
  const timers = {};
  const onChange = (file, fn) => (_event, name) => {
    if (name && name !== basename(file)) return;
    clearTimeout(timers[file]);
    timers[file] = setTimeout(() => run(fn), 150);
  };
  // observa a pasta, não o arquivo: tailwind/esbuild podem recriar o arquivo
  watch(dirname(CSS_OUT), onChange(CSS_OUT, injectCss));
  watch(dirname(JS_OUT), onChange(JS_OUT, injectJs));
  console.log("inject em watch — tailwind.css -> css_code, app.js -> footer.json");
}
