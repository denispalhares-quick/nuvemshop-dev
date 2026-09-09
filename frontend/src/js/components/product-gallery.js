/**
 * Galeria da página de produto.
 *
 * Uso no .tpl:
 *   <div x-data="productGallery()" x-cloak>
 *     <img :src="current" alt="">
 *     <button @click="select(img)" x-for=...>...</button>
 *   </div>
 */
export default function productGallery() {
  return {
    current: null,
    index: 0,

    init() {
      const first = this.$el.querySelector("[data-image]");
      this.current = first ? first.dataset.image : null;
    },

    select(src, index = 0) {
      this.current = src;
      this.index = index;
    },
  };
}
