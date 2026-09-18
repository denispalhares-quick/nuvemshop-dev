import { describe, expect, it } from "vitest";
import { DEFAULTS, readSettings } from "./settings";

describe("readSettings", () => {
	it("sem configuração usa os padrões", () => {
		const s = readSettings(undefined);
		expect(s.freeShippingThreshold).toBe(299);
		expect(s.disabled.size).toBe(0);
		expect(s.topBarMessages).toBeNull();
		expect(s.paymentNote).toBe(DEFAULTS.paymentNote);
		expect(s.whatsapp).toBeNull();
	});

	it("lê o formato real do SDK: { chave: { type, value } }", () => {
		const s = readSettings({
			free_shipping_threshold: { type: "string", value: "249,90" },
			disabled_features: { type: "collection", value: ["Rodape", "pos-compra"] },
			top_bar_messages: { type: "collection", value: ["Entrega expressa", "Troca fácil"] },
			payment_note: { type: "string", value: "Pix com aprovação na hora" },
			whatsapp: { type: "string", value: "+55 (21) 99999-8888" },
		});
		expect(s.freeShippingThreshold).toBe(249.9);
		expect([...s.disabled]).toEqual(["rodape", "pos-compra"]);
		expect(s.topBarMessages).toEqual(["Entrega expressa", "Troca fácil"]);
		expect(s.paymentNote).toBe("Pix com aprovação na hora");
		expect(s.whatsapp).toBe("5521999998888");
	});

	it("aceita valores soltos e listas em texto", () => {
		const s = readSettings({ free_shipping_threshold: 199, disabled_features: "faixa-topo | rodape", top_bar_messages: "A\nB" });
		expect(s.freeShippingThreshold).toBe(199);
		expect([...s.disabled]).toEqual(["faixa-topo", "rodape"]);
		expect(s.topBarMessages).toEqual(["A", "B"]);
	});

	it("valor mínimo com milhar e inválido", () => {
		expect(readSettings({ free_shipping_threshold: "1.299,90" }).freeShippingThreshold).toBe(1299.9);
		expect(readSettings({ free_shipping_threshold: "abc" }).freeShippingThreshold).toBe(299);
		expect(readSettings({ free_shipping_threshold: "-5" }).freeShippingThreshold).toBe(299);
	});

	it("WhatsApp curto demais é ignorado", () => {
		expect(readSettings({ whatsapp: "12345" }).whatsapp).toBeNull();
	});
});
