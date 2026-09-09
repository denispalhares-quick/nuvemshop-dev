/**
 * Bundle do JS do tema.
 *
 * Saída com NOME FIXO (theme/static/js/store.js) — sem hash.
 * Motivo: o .tpl referencia o arquivo literalmente em
 *   {{ 'js/store.js' | static_url | script_tag }}
 * e a plataforma não tem manifest de assets para resolver nome com hash.
 */
import { build, context } from "esbuild";

const watch = process.argv.includes("--watch");

/** @type {import('esbuild').BuildOptions} */
const options = {
  entryPoints: ["src/js/main.js"],
  outfile: "../theme/static/js/store.js",
  bundle: true,
  format: "iife",
  target: ["es2019"],
  minify: !watch,
  sourcemap: watch ? "inline" : false,
  legalComments: "none",
  logLevel: "info",
};

if (watch) {
  const ctx = await context(options);
  await ctx.watch();
  console.log("esbuild em watch — editando src/js/** recompila store.js");
} else {
  await build(options);
}
