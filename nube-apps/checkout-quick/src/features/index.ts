import { faixaTopo } from "./faixa-topo";
import { freteGratis } from "./frete-gratis";
import { posCompra } from "./pos-compra";
import { rodape } from "./rodape";
import { selosPagamento } from "./selos-pagamento";
import type { Feature } from "./types";

/** Ordem aproximada em que aparecem no checkout (de cima para baixo). */
export const FEATURES: Feature[] = [faixaTopo, freteGratis, selosPagamento, rodape, posCompra];
