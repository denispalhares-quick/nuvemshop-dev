/**
 * Configurações do app (portal de parceiros), lidas com `nube.getAppSettings()`.
 *
 * O SDK entrega `{ chave: { type, value } }` (AppSettingsValues) — só existem os tipos
 * string, enrichedText, image e collection. Por isso não há booleano: partes são
 * desligadas listando o nome em `disabled_features`.
 *
 * | chave                    | tipo                  | padrão |
 * |--------------------------|-----------------------|--------|
 * | free_shipping_threshold  | string ("299,90")     | 299 |
 * | disabled_features        | collection de string  | nenhuma (ex.: ["rodape", "pos-compra"]) |
 * | top_bar_messages         | collection de string  | segurança · frete grátis · parcelamento |
 * | payment_note             | string                | "Até 6x sem juros no cartão" |
 * | whatsapp                 | string (só números)   | sem link de WhatsApp |
 *
 * Também aceita valores "soltos" (sem { type, value }), para testes e compatibilidade.
 */
export const FEATURE_NAMES = ["faixa-topo", "frete-gratis", "selos-pagamento", "rodape", "pos-compra"] as const;
export type FeatureName = (typeof FEATURE_NAMES)[number];

export type Settings = {
	freeShippingThreshold: number;
	disabled: Set<string>;
	/** null = usar os textos padrão da faixa */
	topBarMessages: string[] | null;
	paymentNote: string;
	/** Só dígitos, com DDI (ex.: 5521999999999); null = sem WhatsApp */
	whatsapp: string | null;
};

export const DEFAULTS = {
	freeShippingThreshold: 299,
	paymentNote: "Até 6x sem juros no cartão",
} as const;

export function readSettings(raw: unknown): Settings {
	const settings = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
	const get = (key: string) => unwrap(settings[key]);

	const threshold = toNumber(get("free_shipping_threshold"));
	const messages = toList(get("top_bar_messages"));
	const note = toText(get("payment_note"));
	const digits = (toText(get("whatsapp")) ?? "").replace(/\D/g, "");

	return {
		freeShippingThreshold: threshold !== null && threshold > 0 ? threshold : DEFAULTS.freeShippingThreshold,
		disabled: new Set(toList(get("disabled_features")).map((s) => s.toLowerCase())),
		topBarMessages: messages.length ? messages : null,
		paymentNote: note ?? DEFAULTS.paymentNote,
		whatsapp: digits.length >= 10 ? digits : null,
	};
}

function unwrap(v: unknown): unknown {
	if (v && typeof v === "object" && !Array.isArray(v) && "value" in v) {
		return (v as { value: unknown }).value;
	}
	return v;
}

function toText(v: unknown): string | null {
	if (typeof v === "number") return String(v);
	if (typeof v !== "string") return null;
	const t = v.trim();
	return t ? t : null;
}

function toNumber(v: unknown): number | null {
	if (typeof v === "number") return Number.isFinite(v) ? v : null;
	const t = toText(v);
	if (!t) return null;
	const n = Number(t.replace(/[^\d,.-]/g, "").replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", "."));
	return Number.isFinite(n) ? n : null;
}

/** collection -> string[]; string -> separado por quebra de linha, "|" ou "," */
function toList(v: unknown): string[] {
	if (Array.isArray(v)) {
		return v.map((x) => toText(unwrap(x))).filter((x): x is string => Boolean(x));
	}
	const t = toText(v);
	return t ? t.split(/\r?\n|\||,/).map((s) => s.trim()).filter(Boolean) : [];
}
