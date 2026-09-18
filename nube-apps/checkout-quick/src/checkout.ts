import type { NubeSDKState } from "@tiendanube/nube-sdk-types";

export type Step = "start" | "payment" | "success";

/** Etapa do checkout (start = entrega, payment, success) ou null fora do checkout. */
export function getStep(state: Readonly<NubeSDKState>): Step | null {
	const page = state.location?.page;
	return page?.type === "checkout" ? (page.data?.step ?? null) : null;
}

/** https://<domínio da loja>/<caminho> — null se o estado não trouxer o domínio. */
export function storeUrl(state: Readonly<NubeSDKState>, path = "/"): string | null {
	const domain = state.store?.domain?.replace(/^https?:\/\//, "").replace(/\/+$/, "");
	return domain ? `https://${domain}${path}` : null;
}

export function whatsappUrl(digits: string, message: string): string {
	return `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
}
