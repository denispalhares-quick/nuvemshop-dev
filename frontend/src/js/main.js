/**
 * Entrypoint do JS do tema.
 *
 * Princípio: o HTML vem renderizado do servidor (Twig). O JS aqui é
 * progressive enhancement — melhora o que já funciona, nunca assume o DOM.
 */
import Alpine from "alpinejs";
import collapse from "@alpinejs/collapse";

import miniCart from "./components/mini-cart.js";
import productGallery from "./components/product-gallery.js";

Alpine.plugin(collapse);

// Componentes ficam disponíveis nos templates como x-data="miniCart()"
Alpine.data("miniCart", miniCart);
Alpine.data("productGallery", productGallery);

window.Alpine = Alpine;
Alpine.start();
