/**
 * App NubeSDK — layout do checkout na identidade Quick Digital, num script só.
 *
 * Cada parte (features/) declara o slot, as etapas em que aparece e o que desenha.
 * `render` recebe uma função do estado, então tudo se refaz sozinho quando carrinho,
 * etapa ou frete mudam. Partes podem ser desligadas pela configuração `disabled_features`.
 */
import { Column } from "@tiendanube/nube-sdk-jsx";
import type { NubeSDK } from "@tiendanube/nube-sdk-types";
import { getStep } from "./checkout";
import { FEATURES } from "./features";
import { readSettings } from "./settings";

export function App(nube: NubeSDK) {
	const settings = readSettings(nube.getAppSettings?.());

	for (const feature of FEATURES) {
		if (settings.disabled.has(feature.name)) continue;
		nube.render(feature.slot, (state) => {
			const step = getStep(state);
			const node = step && feature.steps.includes(step) ? feature.render(state, settings) : null;
			// slot vazio: o render precisa devolver um componente
			return node ?? <Column key={`${feature.name}-vazio`} />;
		});
	}
}
