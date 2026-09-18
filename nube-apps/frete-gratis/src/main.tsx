/**
 * App NubeSDK — barra de frete grátis no checkout.
 *
 * Renderiza logo abaixo dos totais do pedido (slot `after_line_items_price`, etapas
 * "start" e "payment"). Como `render` recebe uma função do estado, a barra se refaz
 * sozinha quando o carrinho muda (quantidade, cupom, promoção).
 *
 * Valor mínimo: configuração do app `free_shipping_threshold`; sem ela, R$ 299 —
 * o mesmo do aviso no topo da loja.
 */
import { Column, Progress, Text } from "@tiendanube/nube-sdk-jsx";
import type { NubeSDK, NubeSDKState } from "@tiendanube/nube-sdk-types";
import { eligibleAmount, formatMoney, freeShippingStatus, readThreshold } from "./free-shipping";

export const SLOT = "after_line_items_price";

// Identidade Quick Digital
const NAVY = "#000066";
const ORANGE = "#FB4516";
const SOFT = "#FFF1EC";

export function FreeShippingBar({ state, threshold }: { state: Readonly<NubeSDKState>; threshold: number }) {
	const prices = state.cart?.prices;
	if (!prices) {
		return <Column key="frete-gratis-vazio" />;
	}
	const currency = state.store?.currency_details;
	const status = freeShippingStatus(eligibleAmount(prices), threshold);

	const message = status.reached
		? "Parabéns! Seu pedido tem frete grátis 🎉"
		: `Faltam ${formatMoney(status.remaining, currency)} para ganhar frete grátis`;

	return (
		<Column
			key="frete-gratis"
			gap={8}
			padding={12}
			borderRadius={8}
			background={SOFT}
			style={{ marginTop: "12px" }}
		>
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
}

export function App(nube: NubeSDK) {
	const threshold = readThreshold(nube.getAppSettings?.());
	nube.render(SLOT, (state) => <FreeShippingBar state={state} threshold={threshold} />);
}
