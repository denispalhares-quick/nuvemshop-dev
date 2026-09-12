/**
 * Entrypoint do JS do tema.
 *
 * Princípio: o HTML vem renderizado do servidor (Twig). O JS aqui é
 * progressive enhancement — melhora o que já funciona, nunca assume o DOM.
 *
 * O Alpine NÃO é importado: sem fork, este bundle vai inline num block "code"
 * do footer (frontend/inject.mjs) e o Alpine + collapse vêm do CDN, na versão
 * do package-lock. Aqui só registramos os componentes no alpine:init, que o
 * Alpine dispara antes de iniciar.
 */
import miniCart from "./components/mini-cart.js";
import productGallery from "./components/product-gallery.js";

document.addEventListener("alpine:init", () => {
  // Componentes ficam disponíveis nos templates como x-data="miniCart()"
  window.Alpine.data("miniCart", miniCart);
  window.Alpine.data("productGallery", productGallery);
});
