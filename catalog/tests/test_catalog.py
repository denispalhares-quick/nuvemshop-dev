"""python3 -m unittest discover -s catalog/tests -t ."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from catalog.client import ApiError, Client, load_env
from catalog.csvfile import parse_number, parse_visibility, read_csv, validate
from catalog.images import ImageSource
from catalog.importer import Importer, product_payload

HEADER = ('"Identificador URL";Nome;Categorias;"Nome da variação 1";"Valor da variação 1";"Nome da variação 2";'
          '"Valor da variação 2";"Nome da variação 3";"Valor da variação 3";Preço;"Preço promocional";"Peso (kg)";'
          '"Altura (cm)";"Largura (cm)";"Comprimento (cm)";Estoque;SKU;"Código de barras";"Exibir na loja";'
          '"Frete gratis";Descrição;Tags;"Título para SEO";"Descrição para SEO";Marca;"Produto Físico";'
          '"MPN (Cód. Exclusivo Modelo Fabricante)";Sexo;"Faixa etária";Custo;Visibilidade;Imagens')

ROWS = [
    # produto com 2 variações (Cor x Tamanho), categoria com hierarquia, imagem por URL
    'camisa;Camisa;Roupas > Camisas;Cor;Branco;Tamanho;G;;;450,00;;2;1.5;30;15;;A1;;SIM;NÃO;<p>Oi</p>;new, verão;;;Marca;SIM;;;;2.99;Visível;https://x.test/a.jpg | https://x.test/b.jpg',
    'camisa;;;Cor;Preto;Tamanho;G;;;450.00;;2;1.5;30;15;10;A2;;;NÃO;;;;;;SIM;;;;;;',
    # promo maior que o preço + SKU repetido + MPN preenchido
    'short;Short;Calças;;;;;;;100;120;1;2;20;30;5;A1;;NÃO;SIM;;;;;;NÃO;M-1;;;;Oculto;',
]


def write_csv(rows: list[str], extra_header: str = HEADER) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
    f.write("\r\n".join([extra_header, *rows]) + "\r\n")
    f.close()
    return Path(f.name)


class CsvTests(unittest.TestCase):
    def setUp(self):
        self.products = read_csv(write_csv(ROWS))

    def test_agrupa_variacoes_pelo_identificador(self):
        camisa = self.products[0]
        self.assertEqual(len(self.products), 2)
        self.assertEqual(camisa.attributes, ["Cor", "Tamanho"])
        self.assertEqual([v.values for v in camisa.variants], [["Branco", "G"], ["Preto", "G"]])

    def test_conversoes(self):
        camisa, short = self.products
        self.assertEqual(camisa.variants[0].price, "450.00")
        self.assertIsNone(camisa.variants[0].stock)  # vazio = ilimitado
        self.assertEqual(camisa.variants[1].stock, 10)
        self.assertEqual(camisa.categories, [["Roupas", "Camisas"]])
        self.assertEqual(camisa.tags, ["new", "verão"])
        self.assertEqual(camisa.images, ["https://x.test/a.jpg", "https://x.test/b.jpg"])
        self.assertEqual(short.visibility, "hidden")
        self.assertTrue(short.free_shipping)
        self.assertFalse(short.requires_shipping)

    def test_validacao(self):
        issues = validate(self.products)
        messages = [(i.level, i.handle, i.message) for i in issues]
        self.assertTrue(any(l == "erro" and "SKU A1 repetido" in m for l, _, m in messages))
        self.assertTrue(any(l == "aviso" and h == "short" and "promocional" in m for l, h, m in messages))
        self.assertTrue(any(l == "info" and "MPN" in m for l, _, m in messages))

    def test_parse_number_e_visibilidade(self):
        self.assertEqual(parse_number("R$ 1.234,56"), "1234.56")
        self.assertEqual(parse_number("59,9"), "59.9")
        self.assertIsNone(parse_number(""))
        self.assertEqual(parse_visibility("Não listado", "SIM"), "unlisted")
        self.assertEqual(parse_visibility("", "NÃO"), "hidden")

    def test_colunas_obrigatorias(self):
        with self.assertRaises(ValueError):
            read_csv(write_csv([], extra_header="Nome;Preço"))


class PayloadTests(unittest.TestCase):
    def test_payload_do_produto(self):
        camisa = read_csv(write_csv(ROWS))[0]
        d = product_payload(camisa, [11])
        self.assertEqual(d["categories"], [11])
        self.assertEqual(d["visibility"], "visible")
        self.assertNotIn("published", d)  # API responde 422 com published + visibility
        self.assertEqual(d["attributes"], [{"pt": "Cor"}, {"pt": "Tamanho"}])
        self.assertEqual(d["variants"][0]["stock"], "")
        self.assertEqual(d["variants"][0]["values"], [{"pt": "Branco"}, {"pt": "G"}])
        self.assertEqual(d["tags"], "new, verão")


class ImageTests(unittest.TestCase):
    def test_pasta_por_handle_e_sku_em_ordem_natural(self):
        d = Path(tempfile.mkdtemp())
        for name in ["camisa-10.jpg", "camisa-2.jpg", "camisa.jpg", "A2.png", "outro.txt"]:
            (d / name).write_bytes(b"x")
        p = read_csv(write_csv(ROWS[:2]))[0]
        p.images = []
        specs, problems = ImageSource(d).for_product(p, 0)
        self.assertEqual([s.label for s in specs], ["camisa.jpg", "camisa-2.jpg", "camisa-10.jpg"])
        self.assertIn("attachment", specs[0].payload)
        self.assertEqual(problems, [])

    def test_placeholder(self):
        p = read_csv(write_csv(ROWS[:2]))[0]
        p.images = []
        specs, _ = ImageSource(placeholder_base="https://cdn/x@sha").for_product(p, 9)
        self.assertEqual(specs[0].payload["src"],
                         "https://cdn/x@sha/theme/static/images/placeholders/products/product-2.webp")


class FakeResponse(io.BytesIO):
    def __init__(self, body, headers=None):
        super().__init__(json.dumps(body).encode())
        self.headers = headers or {"x-rate-limit-remaining": "39", "x-rate-limit-reset": "1000"}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeStore:
    """Simula a API: guarda POSTs e responde listas vazias/ids."""

    def __init__(self, fail_first_with_429=False):
        self.calls = []
        self.fail = fail_first_with_429
        self.next_id = 100

    def __call__(self, req, timeout=None):
        method, url = req.get_method(), req.full_url
        body = json.loads(req.data) if req.data else None
        self.calls.append((method, url.split("/8/")[-1], body))
        if self.fail:
            self.fail = False
            raise urllib.error.HTTPError(url, 429, "Too Many", {"x-rate-limit-reset": "10"}, io.BytesIO(b"{}"))
        if method == "GET":
            return FakeResponse([])
        self.next_id += 1
        return FakeResponse({"id": self.next_id})


class ImporterTests(unittest.TestCase):
    def make(self, store):
        sleeps = []
        client = Client("8", "t", "ua", base_url="https://api.test", sleep=sleeps.append, opener=store)
        return client, sleeps

    def test_dry_run_so_le(self):
        store = FakeStore()
        client, _ = self.make(store)
        products = read_csv(write_csv(ROWS[:2]))
        report = Importer(client, products, dry_run=True, log=lambda *_: None).run()
        self.assertTrue(all(m == "GET" for m, _, _ in store.calls))
        self.assertEqual(report.count("criar"), 1)
        self.assertEqual(report.categories_created, ["Roupas", "Roupas > Camisas"])

    def test_apply_cria_categorias_produto_e_imagens_com_retry_429(self):
        store = FakeStore(fail_first_with_429=True)
        client, sleeps = self.make(store)
        products = read_csv(write_csv(ROWS[:2]))
        report = Importer(client, products, images=ImageSource(), dry_run=False, log=lambda *_: None).run()
        posts = [(path, body) for m, path, body in store.calls if m == "POST"]
        self.assertEqual([p for p, _ in posts][:3], ["categories", "categories", "products"])
        self.assertEqual(posts[1][1]["parent"], 101)  # subcategoria aponta para a pai (id 101)
        self.assertEqual(len([p for p, _ in posts if p.endswith("/images")]), 2)
        self.assertEqual(report.count("criar"), 1)
        self.assertTrue(sleeps)  # esperou depois do 429

    def test_erro_da_api_vira_outcome(self):
        def failing(req, timeout=None):
            if req.get_method() == "GET":
                return FakeResponse([])
            raise urllib.error.HTTPError(req.full_url, 422, "x", {}, io.BytesIO('{"price":["inválido"]}'.encode()))
        client, _ = self.make(failing)
        report = Importer(client, read_csv(write_csv(ROWS[:2])), dry_run=False, log=lambda *_: None).run()
        self.assertEqual(report.count("erro"), 1)


class EnvTests(unittest.TestCase):
    def test_load_env(self):
        f = Path(tempfile.mkdtemp()) / ".env"
        f.write_text('A=1\nB="com (parênteses)"\nC=stdio   # comentário\n# X=2\nVAZIO=\n')
        self.assertEqual(load_env(f), {"A": "1", "B": "com (parênteses)", "C": "stdio", "VAZIO": ""})

    def test_repr_nao_expoe_token(self):
        self.assertNotIn("segredo", repr(Client("8", "segredo", "ua")))


if __name__ == "__main__":
    unittest.main()
