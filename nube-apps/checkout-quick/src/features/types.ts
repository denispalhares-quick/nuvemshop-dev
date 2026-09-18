import type { NubeComponent, NubeSDKState } from "@tiendanube/nube-sdk-types";
import type { Step } from "../checkout";
import type { FeatureName, Settings } from "../settings";

/** Uma parte do layout do checkout: onde entra, em quais etapas e o que desenha. */
export type Feature = {
	name: FeatureName;
	slot: CheckoutSlot;
	steps: Step[];
	/** null = não mostrar nada neste estado */
	render(state: Readonly<NubeSDKState>, settings: Settings): NubeComponent | null;
};

/** Slots de checkout usados pelo app (lista completa em dev.nuvemshop.com.br › NubeSDK › Checkout Slots). */
export type CheckoutSlot =
	| "after_header"
	| "after_line_items_price"
	| "before_payment_options"
	| "after_main_content"
	| "after_order_number";
