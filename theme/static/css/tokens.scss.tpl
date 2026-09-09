{#
  Ponte entre o Brand Editor e o CSS compilado localmente (Tailwind).

  Este arquivo é compilado PELA NUVEMSHOP: passa primeiro pelo Twig
  (interpolando os settings do tema) e depois pelo compilador SASS.
  Por isso ele fica no repo como fonte, e não é gerado pelo build local.

  Carregue-o ANTES do style.css no layout:
    {{ 'css/tokens.scss.tpl' | static_url | css_tag }}
    {{ 'css/style.css'       | static_url | css_tag }}

  ATENÇÃO: os nomes dos settings abaixo são um chute razoável e precisam ser
  conferidos contra o tema real depois do `nuvemshop theme pull` — cada tema
  define os seus em config/. Se um setting não existir, o Twig renderiza vazio
  e a variável CSS cai no fallback definido em frontend/src/css/main.css.
#}
:root {
  --brand-primary: {{ settings.primary_color }};
  --brand-secondary: {{ settings.secondary_color }};
  --brand-background: {{ settings.background_color }};
  --brand-text: {{ settings.text_color }};

  --brand-font-heading: {{ settings.heading_font }};
  --brand-font-body: {{ settings.body_font }};
}
