import { describe, expect, it, vi } from "vitest";

// Componentes do SDK viram objetos simples para inspecionar a árvore (mesma técnica do template oficial).
vi.mock("@tiendanube/nube-sdk-jsx", () => {
	const make = (type: string) => (props: Record<string, unknown>) => ({ type, props });
	return { Column: make("col"), Text: make("txt"), Progress: make("progress") };
});

import { App, FreeShippingBar, SLOT } from "./main";

type Node = { type: string; props: Record<string, unknown> };

function texts(node: unknown): string[] {
	if (node == null || node === false) return [];
	if (typeof node === "string" || typeof node === "number") return [String(node)];
	if (Array.isArray(node)) return node.flatMap(texts);
	const n = node as Node;
	if (typeof n.type === "function") {
		return texts((n.type as (p: unknown) => unknown)(n.props));
	}
	return texts(n.props?.children);
}

function find(node: unknown, type: string): Node | undefined {
	if (!node || typeof node !== "object") return undefined;
	if (Array.isArray(node)) return node.map((c) => find(c, type)).find(Boolean);
	const n = node as Node;
	if (typeof n.type === "function") return find((n.type as (p: unknown) => unknown)(n.props), type);
	if (n.type === type) return n;
	return find(n.props?.children, type);
}

const state = (subtotal: number, extra: Partial<{ discount_coupon: number; discount_promotion: number }> = {}) =>
	({
		cart: {
			prices: { subtotal, discount_coupon: 0, discount_promotion: 0, discount_gateway: 0, shipping: 0, total: subtotal, subtotal_without_taxes: subtotal, ...extra },
		},
		store: { currency_details: { code: "BRL", display_short: "R$", display_long: "R$", cents_separator: ",", thousands_separator: "." } },
	}) as never;

describe("FreeShippingBar", () => {
	it("mostra quanto falta (caso do print: Mochila R$ 174,90)", () => {
		const tree = FreeShippingBar({ state: state(174.9), threshold: 299 });
		expect(texts(tree).join(" ")).toContain("Faltam R$ 124,10 para ganhar frete grátis");
		expect(find(tree, "progress")?.props.value).toBe(58);
	});

	it("parabeniza quando atinge, sem a linha do valor mínimo", () => {
		const tree = FreeShippingBar({ state: state(320), threshold: 299 });
		const all = texts(tree).join(" ");
		expect(all).toContain("Parabéns");
		expect(all).not.toContain("a partir de");
	});

	it("considera cupom e promoção", () => {
		const tree = FreeShippingBar({ state: state(320, { discount_coupon: 40 }), threshold: 299 });
		expect(texts(tree).join(" ")).toContain("Faltam R$ 19,00");
	});

	it("sem carrinho no estado não quebra", () => {
		expect(() => FreeShippingBar({ state: {} as never, threshold: 299 })).not.toThrow();
	});
});

describe("App", () => {
	it("registra no slot abaixo dos totais, com o valor das configurações do app", () => {
		const render = vi.fn();
		App({ render, getAppSettings: () => ({ free_shipping_threshold: 199 }) } as never);
		expect(render).toHaveBeenCalledWith(SLOT, expect.any(Function));
		const component = render.mock.calls[0][1](state(100));
		expect(texts(component).join(" ")).toContain("Faltam R$ 99,00");
	});

	it("sem configuração usa R$ 299", () => {
		const render = vi.fn();
		App({ render, getAppSettings: () => ({}) } as never);
		expect(texts(render.mock.calls[0][1](state(100))).join(" ")).toContain("Faltam R$ 199,00");
	});
});
