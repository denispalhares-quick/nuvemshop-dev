/**
 * Acima das formas de pagamento: segurança + condição de pagamento (configuração `payment_note`).
 * Não promete desconto nem prazo — só o que vale para qualquer compra na plataforma.
 */
import { Column, Text } from "@tiendanube/nube-sdk-jsx";
import { LIGHT, NAVY, ORANGE, TEXT } from "../brand";
import type { Feature } from "./types";

export const selosPagamento: Feature = {
	name: "selos-pagamento",
	slot: "before_payment_options",
	steps: ["payment"],
	render(_state, settings) {
		return (
			<Column key="selos-pagamento" gap={4} padding={12} borderRadius={8} background={LIGHT} style={{ marginBottom: "12px" }}>
				{[
					<Text key="titulo" color={NAVY} style={{ fontWeight: 700, fontSize: "14px", margin: 0 }}>
						🔒 Pagamento rápido e protegido
					</Text>,
					<Text key="seguranca" color={TEXT} style={{ fontSize: "13px", margin: 0 }}>
						Ambiente seguro, com seus dados enviados de forma criptografada. É só escolher como pagar e finalizar.
					</Text>,
					...(settings.paymentNote
						? [
								<Text key="condicao" color={ORANGE} style={{ fontWeight: 700, fontSize: "13px", margin: 0 }}>
									{settings.paymentNote}
								</Text>,
							]
						: []),
				]}
			</Column>
		);
	},
};
