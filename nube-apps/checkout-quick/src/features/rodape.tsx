/**
 * Fim da página do checkout: ajuda para quem travou. Link para a página de contato da loja
 * e, se configurado (`whatsapp`), para o WhatsApp com a mensagem já escrita.
 */
import { Column, Link, Row, Text } from "@tiendanube/nube-sdk-jsx";
import { NAVY, TEXT } from "../brand";
import { storeUrl, whatsappUrl } from "../checkout";
import type { Feature } from "./types";

export const rodape: Feature = {
	name: "rodape",
	slot: "after_main_content",
	steps: ["start", "payment"],
	render(state, settings) {
		const contact = storeUrl(state, "/contato/");
		const links = [
			...(contact ? [<Link key="contato" href={contact} variant="link">Fale com a gente</Link>] : []),
			...(settings.whatsapp
				? [
						<Link key="whatsapp" href={whatsappUrl(settings.whatsapp, "Oi! Preciso de ajuda para finalizar minha compra.")} target="_blank" variant="link">
							Chamar no WhatsApp
						</Link>,
					]
				: []),
		];
		return (
			<Column key="rodape" gap={6} padding={16} alignItems="center" style={{ marginTop: "24px", textAlign: "center" }}>
				{[
					<Text key="ajuda" color={NAVY} style={{ fontWeight: 700, fontSize: "14px", margin: 0 }}>
						Travou em alguma etapa? A gente resolve rápido.
					</Text>,
					...(links.length ? [<Row key="links" gap={16} justifyContent="center">{links}</Row>] : []),
					<Text key="loja" color={TEXT} style={{ fontSize: "12px", opacity: 0.7, margin: 0 }}>
						{`${state.store?.name ?? "Loja"} · compra segura`}
					</Text>,
				]}
			</Column>
		);
	},
};
