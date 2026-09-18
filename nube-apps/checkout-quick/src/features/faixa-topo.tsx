/**
 * Faixa abaixo do cabeçalho do checkout: os argumentos que fazem o cliente seguir em frente.
 * Padrão = o que a loja já anuncia (frete grátis pelo valor mínimo configurado, parcelamento).
 * Textos próprios: configuração `top_bar_messages`.
 */
import { Row, Text } from "@tiendanube/nube-sdk-jsx";
import { NAVY } from "../brand";
import { formatMoney } from "../free-shipping";
import type { Feature } from "./types";

export const faixaTopo: Feature = {
	name: "faixa-topo",
	slot: "after_header",
	steps: ["start", "payment"],
	render(state, settings) {
		const messages = settings.topBarMessages ?? [
			"🔒 Compra 100% segura",
			`🚚 Frete grátis acima de ${formatMoney(settings.freeShippingThreshold, state.store?.currency_details)}`,
			`💳 ${settings.paymentNote}`,
		];
		return (
			<Row
				key="faixa-topo"
				gap={24}
				padding={10}
				background={NAVY}
				justifyContent="center"
				alignItems="center"
				style={{ flexWrap: "wrap", width: "100%" }}
			>
				{messages.map((message, i) => (
					<Text key={`faixa-${i}`} color="#FFFFFF" style={{ fontSize: "13px", fontWeight: 600, margin: 0 }}>
						{message}
					</Text>
				))}
			</Row>
		);
	},
};
