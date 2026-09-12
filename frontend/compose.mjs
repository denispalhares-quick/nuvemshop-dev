/**
 * Monta as páginas do tema a partir de design/pages/*.yaml.
 *
 *   design/pages/home.yaml -> theme/templates/pages/home.json
 *
 * Cada item de `sections` é uma de duas coisas:
 *
 *   native: <id>      seção nativa do Ipanema. Se já existe no JSON, a config atual (Brand Editor)
 *                     é mantida e só o que o YAML declarar em settings/blocks é sobrescrito.
 *                     Se não existe, é criada — aí `type` é obrigatório.
 *   component: <nome> design/components/<nome>.html vira uma seção "Personalizada" (id cmp_<nome>)
 *                     com o HTML num block "Código". Sem fork, é o único jeito de ter HTML próprio.
 *
 * Strings `asset:<caminho>` (no YAML ou no HTML) viram URL do jsDelivr para design/assets/<caminho>,
 * fixada num commit: ASSETS_REF (padrão: HEAD) em ASSETS_REPO (padrão: remote origin).
 * O jsDelivr só serve commits que já estão no GitHub — commite e dê push nos assets antes do preview.
 *
 * Só grava quando o conteúdo muda. Uso: node compose.mjs [--watch]
 */
import { existsSync, readdirSync, readFileSync, watch, writeFileSync } from "node:fs";
import { basename, dirname, extname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import YAML from "yaml";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PAGES_DIR = resolve(root, "design/pages");
const COMPONENTS_DIR = resolve(root, "design/components");
const ASSETS_DIR = resolve(root, "design/assets");
const TEMPLATES_DIR = resolve(root, "theme/templates/pages");
const COMPONENT_PREFIX = "cmp_";

// ---------------------------------------------------------------------------
// git sem o binário (o container do frontend não tem git)

function readGit(file) {
  const p = resolve(root, ".git", file);
  return existsSync(p) ? readFileSync(p, "utf8").trim() : null;
}

function gitHead() {
  const head = readGit("HEAD");
  if (!head) return null;
  if (!head.startsWith("ref: ")) return head; // HEAD destacado
  const ref = head.slice(5);
  const loose = readGit(ref);
  if (loose) return loose;
  const packed = readGit("packed-refs") ?? "";
  return packed.split("\n").find((l) => l.endsWith(` ${ref}`))?.split(" ")[0] ?? null;
}

function gitRepo() {
  const config = readGit("config") ?? "";
  const url = config.match(/\[remote "origin"\][^[]*?url\s*=\s*(\S+)/)?.[1];
  // git@github.com-alias:owner/repo.git | https://github.com/owner/repo(.git)
  return url?.match(/[:/]([^/:]+)\/([^/]+?)(?:\.git)?$/)?.slice(1, 3).join("/") ?? null;
}

const ASSETS_REPO = process.env.ASSETS_REPO || gitRepo();
const warned = new Set();
const warnOnce = (msg) => warned.has(msg) || (warned.add(msg), console.warn(`compose: ⚠ ${msg}`));

function assetUrl(path) {
  const ref = process.env.ASSETS_REF || gitHead();
  if (!existsSync(resolve(ASSETS_DIR, path))) warnOnce(`asset não encontrado: design/assets/${path}`);
  if (!ASSETS_REPO || !ref) {
    warnOnce("não consegui descobrir repo/commit para os assets — defina ASSETS_REPO e ASSETS_REF");
    return `asset:${path}`;
  }
  return `https://cdn.jsdelivr.net/gh/${ASSETS_REPO}@${ref}/design/assets/${path}`;
}

const resolveAssets = (text) => text.replace(/asset:([\w./@-]+)/g, (_, p) => assetUrl(p));

function resolveAssetsDeep(value) {
  if (typeof value === "string") return resolveAssets(value);
  if (Array.isArray(value)) return value.map(resolveAssetsDeep);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, resolveAssetsDeep(v)]));
  }
  return value;
}

// ---------------------------------------------------------------------------
// merge de seções/blocks nativos

function mergeBlocks(current = {}, order = [], overrides = {}, path) {
  const blocks = { ...current };
  const blockOrder = [...order];
  for (const [id, over] of Object.entries(overrides)) {
    const base = blocks[id];
    if (!base && !over.type) throw new Error(`${path}.blocks.${id}: block novo precisa de "type"`);
    blocks[id] = mergeNode(base ?? { type: over.type, settings: {} }, over, `${path}.blocks.${id}`);
    if (!blockOrder.includes(id)) blockOrder.push(id);
  }
  return { blocks, block_order: blockOrder };
}

function mergeNode(base, over, path) {
  const node = { ...base, type: over.type ?? base.type };
  if (over.settings) node.settings = { ...(base.settings ?? {}), ...over.settings };
  if (over.blocks || over.block_order) {
    const merged = mergeBlocks(base.blocks, base.block_order, over.blocks, path);
    node.blocks = merged.blocks;
    node.block_order = over.block_order ?? merged.block_order;
  }
  return node;
}

// ---------------------------------------------------------------------------

function componentSection(name, entry) {
  const file = resolve(COMPONENTS_DIR, `${name}.html`);
  if (!existsSync(file)) throw new Error(`componente não encontrado: design/components/${name}.html`);
  const html = resolveAssets(readFileSync(file, "utf8").replace(/<!--[\s\S]*?-->/g, "").trim());
  return {
    type: "custom",
    settings: { section_width: "full", vertical_padding: 0, horizontal_padding: 0, gap: 0, ...(entry.settings ?? {}) },
    blocks: { code: { type: "code", settings: { code: html, width: "fill" } } },
    block_order: ["code"],
  };
}

function composePage(yamlFile) {
  const spec = YAML.parse(readFileSync(yamlFile, "utf8")) ?? {};
  const page = spec.page ?? basename(yamlFile, extname(yamlFile));
  const out = resolve(TEMPLATES_DIR, `${page}.json`);
  const current = existsSync(out) ? JSON.parse(readFileSync(out, "utf8")) : { sections: {}, order: [] };
  const sections = {};
  const order = [];

  for (const [i, raw] of (spec.sections ?? []).entries()) {
    const entry = resolveAssetsDeep(raw);
    const where = `${basename(yamlFile)} sections[${i}]`;
    if (entry.component) {
      const id = COMPONENT_PREFIX + String(entry.component).replace(/[^a-z0-9_]/gi, "_").toLowerCase();
      sections[id] = componentSection(entry.component, entry);
      order.push(id);
    } else if (entry.native) {
      const id = entry.native;
      const base = current.sections[id];
      if (!base && !entry.type) throw new Error(`${where}: seção nova "${id}" precisa de "type"`);
      sections[id] = mergeNode(base ?? { type: entry.type, settings: {} }, entry, `${where} (${id})`);
      order.push(id);
    } else {
      throw new Error(`${where}: use "native: <id>" ou "component: <nome>"`);
    }
  }

  // Seções que existem no JSON mas não no YAML (ex.: adicionadas pelo Brand Editor): mantidas no fim,
  // a menos que `unlisted: remove`. Componentes (cmp_*) fora do YAML sempre saem.
  for (const id of current.order ?? []) {
    if (order.includes(id) || id.startsWith(COMPONENT_PREFIX)) continue;
    if (spec.unlisted === "remove") continue;
    warnOnce(`${page}: seção "${id}" não está no YAML — mantida no fim (use unlisted: remove para tirar)`);
    sections[id] = current.sections[id];
    order.push(id);
  }

  const next = { ...current, sections, order };
  const text = JSON.stringify(next, null, 2) + "\n";
  if (existsSync(out) && readFileSync(out, "utf8") === text) return;
  writeFileSync(out, text);
  console.log(`compose: ${page}.json atualizado (${order.length} seções: ${order.join(", ")})`);
}

function run() {
  if (!existsSync(PAGES_DIR)) return;
  for (const f of readdirSync(PAGES_DIR).filter((f) => /\.ya?ml$/.test(f))) {
    try {
      composePage(resolve(PAGES_DIR, f));
    } catch (err) {
      console.error(`compose: ✗ ${err.message}`);
      if (!process.argv.includes("--watch")) process.exitCode = 1;
    }
  }
}

run();

if (process.argv.includes("--watch")) {
  let timer;
  const schedule = () => {
    clearTimeout(timer);
    timer = setTimeout(run, 150);
  };
  for (const dir of [PAGES_DIR, COMPONENTS_DIR]) if (existsSync(dir)) watch(dir, { recursive: true }, schedule);
  console.log("compose em watch — design/pages + design/components -> theme/templates/pages");
}
