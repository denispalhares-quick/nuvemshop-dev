import { describe, expect, it, vi } from "vitest";

// Componentes do SDK viram objetos simples para inspecionar a árvore (mesma técnica do template oficial).
vi.mock("@tiendanube/nube-sdk-jsx", () => {
	const make = (type: string) => (props: Record<string, unknown>) => ({ type, props });
	return { Column: make("col"), Row: make("row"), Text: make("txt"), Progress: make("progress"), Link: make("link") };
});

import { faixaTopo } from "./features/faixa-topo";
import { freteGratis } from "./features/frete-gratis";
import { posCompra } from "./features/pos-compra";
import { rodape } from "./features/rodape";
import { selosPagamento } from "./features/selos-pagamento";
import { App } from "./main";
import { readSettings } from "./settings";

type Node = { type: unknown; props: Record<string, unknown> };
const expand = (n: Node): unknown => (typeof n.type === "function" ? (n.type as (p: unknown) => unknown)(n.props) : n);

function texts(node: unknown): string[] {
	if (node == null || node === false) return [];
	if (typeof node === "string" || typeof node === "number") return [String(node)];
	if (Array.isArray(node)) return node.flatMap(texts);
	const n = expand(node as Node) as Node;
	return texts(n.props?.children);
}

function findAll(node: unknown, type: string): Node[] {
	if (!node || typeof node !== "object") return [];
	if (Array.isArray(node)) return node.flatMap((c) => findAll(c, type));
	const n = expand(node as Node) as Node;
	return [...(n.type === type ? [n] : []), ...findAll(n.props?.children, type)];
}

const state = (step: "start" | "payment" | "success" | null, subtotal = 174.9) =>
	({
		location: step ? { page: { type: "checkout", data: { step } } } : { page: { type: "home", data: {} } },
		cart: { prices: { subtotal, discount_coupon: 0, discount_promotion: 0, discount_gateway: 0, shipping: 0, total: subtotal, subtotal_without_taxes: subtotal } },
		store: { name: "QuickStart", domain: "quickstart2.lojavirtualnuvem.com.br", currency_details: { code: "BRL", display_short: "R$", display_long: "R$", cents_separator: ",", thousands_separator: "." } },
	}) as never;

const all = (node: unknown) => texts(node).join(" ");
const defaults = readSettings(undefined);
const withWhats = readSettings({ whatsapp: { type: "string", value: "5521999998888" } });

describe("partes", () => {
	it("faixa-topo: segurança, frete grátis pelo valor mínimo e parcelamento", () => {
		const t = all(faixaTopo.render(state("start"), defaults));
		expect(t).toContain("Compra 100% segura");
		expect(t).toContain("Frete grátis acima de R$ 299,00");
		expect(t).toContain("Até 6x sem juros no cartão");
	});

	it("faixa-topo: textos próprios substituem os padrões", () => {
		const s = readSettings({ top_bar_messages: { type: "collection", value: ["Entrega expressa"] } });
		expect(all(faixaTopo.render(state("start"), s))).toBe("Entrega expressa");
	});

	it("frete-gratis: quanto falta e parabéns", () => {
		expect(all(freteGratis.render(state("start", 174.9), defaults))).toContain("Faltam R$ 124,10");
		expect(all(freteGratis.render(state("start", 320), defaults))).toContain("Parabéns");
		expect(findAll(freteGratis.render(state("start", 174.9), defaults), "progress")[0].props.value).toBe(58);
	});

	it("selos-pagamento: segurança + condição configurável", () => {
		const t = all(selosPagamento.render(state("payment"), defaults));
		expect(t).toContain("Pagamento rápido e protegido");
		expect(t).toContain("Até 6x sem juros no cartão");
	});

	it("rodape: contato da loja; WhatsApp só se configurado", () => {
		const sem = rodape.render(state("start"), defaults);
		expect(findAll(sem, "link").map((l) => l.props.href)).toEqual(["https://quickstart2.lojavirtualnuvem.com.br/contato/"]);
		const com = rodape.render(state("start"), withWhats);
		const whats = findAll(com, "link").find((l) => String(l.props.href).startsWith("https://wa.me/5521999998888"));
		expect(whats?.props.target).toBe("_blank");
		expect(all(com)).toContain("A gente resolve rápido");
	});

	it("pos-compra: confirmação e próximos passos", () => {
		const t = all(posCompra.render(state("success"), withWhats));
		expect(t).toContain("Pedido confirmado!");
		expect(t).toContain("chega no seu e-mail");
		expect(t).toContain("Chama no WhatsApp");
	});
});

describe("App", () => {
	const setup = (settings: unknown = {}) => {
		const calls = new Map<string, (s: unknown) => unknown>();
		App({ render: (slot: string, fn: (s: unknown) => unknown) => calls.set(slot, fn), getAppSettings: () => settings } as never);
		return calls;
	};

	it("registra uma parte por slot", () => {
		expect([...setup().keys()]).toEqual([
			"after_header",
			"after_line_items_price",
			"before_payment_options",
			"after_main_content",
			"after_order_number",
		]);
	});

	it("cada parte só aparece nas suas etapas", () => {
		const calls = setup();
		expect(all(calls.get("before_payment_options")?.(state("start")))).toBe("");
		expect(all(calls.get("before_payment_options")?.(state("payment")))).toContain("Pagamento rápido");
		expect(all(calls.get("after_order_number")?.(state("payment")))).toBe("");
		expect(all(calls.get("after_order_number")?.(state("success")))).toContain("Pedido confirmado");
		expect(all(calls.get("after_header")?.(state(null)))).toBe("");
	});

	it("disabled_features desliga partes; valor mínimo vem das configurações reais", () => {
		const calls = setup({
			disabled_features: { type: "collection", value: ["rodape", "faixa-topo"] },
			free_shipping_threshold: { type: "string", value: "199" },
		});
		expect(calls.has("after_main_content")).toBe(false);
		expect(calls.has("after_header")).toBe(false);
		expect(all(calls.get("after_line_items_price")?.(state("start", 100)))).toContain("Faltam R$ 99,00");
	});
});
