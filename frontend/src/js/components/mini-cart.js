/**
 * Mini-carrinho.
 *
 * Exemplo de componente Alpine. A fonte da verdade continua sendo o
 * carrinho da Nuvemshop — este componente só reflete o estado e abre/fecha
 * o drawer. Não reimplemente a lógica de carrinho no front.
 *
 * Uso no .tpl:
 *   <div x-data="miniCart()" x-cloak>
 *     <button @click="toggle()" class="js-minicart-toggle">Carrinho</button>
 *     <aside x-show="open" @click.outside="close()"> ... </aside>
 *   </div>
 */
export default function miniCart() {
  return {
    open: false,

    toggle() {
      this.open = !this.open;
    },

    close() {
      this.open = false;
    },

    init() {
      // A plataforma dispara eventos ao alterar o carrinho; o nome exato
      // varia por tema — confirme no tema pulado antes de confiar neste hook.
      document.addEventListener("cart.updated", () => {
        this.open = true;
      });
    },
  };
}
