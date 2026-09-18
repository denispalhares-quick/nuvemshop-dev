import { describe, expect, it } from "vitest";
import { eligibleAmount, formatMoney, freeShippingStatus } from "./free-shipping";

describe("eligibleAmount", () => {
	it("desconta promoção e cupom, ignora frete e gateway", () => {
		expect(eligibleAmount({ subtotal: 300, discount_promotion: 20, discount_coupon: 10 })).toBe(270);
	});
	it("nunca fica negativo", () => {
		expect(eligibleAmount({ subtotal: 10, discount_promotion: 50, discount_coupon: 0 })).toBe(0);
	});
});

describe("freeShippingStatus", () => {
	it("calcula o que falta e o progresso", () => {
		expect(freeShippingStatus(174.9, 299)).toEqual({ base: 174.9, remaining: 124.1, progress: 58, reached: false });
	});
	it("atinge exatamente no valor mínimo", () => {
		expect(freeShippingStatus(299, 299)).toMatchObject({ remaining: 0, progress: 100, reached: true });
	});
	it("não passa de 100% acima do mínimo", () => {
		expect(freeShippingStatus(500, 299).progress).toBe(100);
	});
	it("valor mínimo inválido = já atingido", () => {
		expect(freeShippingStatus(10, 0).reached).toBe(true);
	});
	it("arredonda centavos (0.1 + 0.2)", () => {
		expect(freeShippingStatus(0.1 + 0.2, 1).remaining).toBe(0.7);
	});
});

describe("formatMoney", () => {
	it("formata em BRL por padrão", () => {
		expect(formatMoney(124.1)).toBe("R$ 124,10");
		expect(formatMoney(1234567.5)).toBe("R$ 1.234.567,50");
	});
	it("respeita as regras de moeda da loja", () => {
		expect(formatMoney(1234.5, { display_short: "US$", cents_separator: ".", thousands_separator: "," })).toBe("US$ 1,234.50");
	});
});
