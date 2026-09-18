/**
 * Barra de frete grátis logo abaixo dos totais. Refaz sozinha quando o carrinho muda
 * (quantidade, cupom, promoção). Valor mínimo: configuração `free_shipping_threshold`.
 */
import { Column, Progress, Text } from "@tiendanube/nube-sdk-jsx";
import { NAVY, ORANGE, SOFT } from "../brand";
import { eligibleAmount, formatMoney, freeShippingStatus } from "../free-shipping";
import type { Feature } from "./types";

export const freteGratis: Feature = {
	name: "frete-gratis",
	slot: "after_line_items_price",
	steps: ["start", "payment"],
	render(state, settings) {
		const prices = state.cart?.prices;
		if (!prices) return null;
		const currency = state.store?.currency_details;
		const threshold = settings.freeShippingThreshold;
		const status = freeShippingStatus(eligibleAmount(prices), threshold);

		const message = status.reached
			? "Parabéns! Seu pedido tem frete grátis 🎉"
			: `Faltam ${formatMoney(status.remaining, currency)} para ganhar frete grátis`;

		return (
			<Column key="frete-gratis" gap={8} padding={12} borderRadius={8} background={SOFT} style={{ marginTop: "12px" }}>
				{[
					<Text key="mensagem" color={NAVY} style={{ fontWeight: 700, fontSize: "14px", margin: 0 }}>
						{message}
					</Text>,
					<Progress
						key="barra"
						value={status.progress}
						max={100}
						aria-label="Progresso para frete grátis"
						style={{ width: "100%", accentColor: ORANGE }}
					/>,
					// o SDK não aceita `false` como filho: a linha do valor mínimo entra só se ainda falta
					...(status.reached
						? []
						: [
								<Text key="minimo" color={NAVY} style={{ fontSize: "12px", opacity: 0.75, margin: 0 }}>
									Frete grátis em compras a partir de {formatMoney(threshold, currency)}
								</Text>,
							]),
				]}
			</Column>
		);
	},
};
