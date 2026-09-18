/**
 * Regra da barra de frete grátis — sem UI, para testar isolado.
 *
 * Base de cálculo: subtotal dos produtos menos descontos de promoção e cupom (o que o
 * cliente paga pelos produtos). Frete e desconto de meio de pagamento ficam de fora.
 * A barra é informativa: quem concede o frete grátis é a promoção/regra configurada
 * na loja — mantenha o mesmo valor mínimo dos dois lados.
 */
import type { CurrencyDetails, Prices } from "@tiendanube/nube-sdk-types";

export type FreeShippingStatus = {
	/** Valor considerado para o frete grátis. */
	base: number;
	/** Quanto falta (0 quando já atingiu). */
	remaining: number;
	/** 0–100, para a barra. */
	progress: number;
	reached: boolean;
};

export function eligibleAmount(prices: Pick<Prices, "subtotal" | "discount_promotion" | "discount_coupon">): number {
	const value = (prices.subtotal ?? 0) - (prices.discount_promotion ?? 0) - (prices.discount_coupon ?? 0);
	return Math.max(0, round2(value));
}

export function freeShippingStatus(base: number, threshold: number): FreeShippingStatus {
	if (!(threshold > 0)) {
		return { base, remaining: 0, progress: 100, reached: true };
	}
	const remaining = Math.max(0, round2(threshold - base));
	return {
		base,
		remaining,
		progress: Math.min(100, Math.round((base / threshold) * 100)),
		reached: remaining === 0,
	};
}

/** 1234.5 -> "R$ 1.234,50" usando as regras de moeda da loja (padrão: BRL). */
export function formatMoney(value: number, currency?: Partial<CurrencyDetails>): string {
	const symbol = currency?.display_short ?? "R$";
	const cents = currency?.cents_separator ?? ",";
	const thousands = currency?.thousands_separator ?? ".";
	const [int, dec] = Math.abs(value).toFixed(2).split(".");
	const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, thousands);
	return `${value < 0 ? "-" : ""}${symbol} ${grouped}${cents}${dec}`;
}

function round2(n: number): number {
	return Math.round(n * 100) / 100;
}
