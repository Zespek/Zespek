"""
Fira Code embutida nos SVGs do perfil.

Um SVG aberto como imagem (o <img> do README) não baixa fonte de fora, então cada SVG leva a
fonte dentro, em base64. Para ficar leve, o Google Fonts devolve só os caracteres usados
(parâmetro text=), o mesmo que o readme-typing-svg faz. A fonte é OFL.
"""
import base64
import re
import urllib.parse
import urllib.request

# Sem um navegador moderno no User-Agent o Google Fonts devolve TTF em vez de WOFF2
NAVEGADOR = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'


def _baixar(url):
    pedido = urllib.request.Request(url, headers={'User-Agent': NAVEGADOR})
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return resposta.read()


def fira_code(texto, peso=600):
    """Devolve o @font-face da Fira Code com só os caracteres de `texto`."""
    caracteres = ''.join(sorted(set(texto) - {'\n'}))
    consulta = urllib.parse.urlencode({'family': f'Fira Code:wght@{peso}', 'text': caracteres})
    css = _baixar(f'https://fonts.googleapis.com/css2?{consulta}').decode()
    url = re.search(r'url\((https://[^)]+)\)', css).group(1)
    dados = base64.b64encode(_baixar(url)).decode()
    return (f"@font-face {{ font-family: 'Fira Code Zespek'; font-weight: {peso}; "
            f"src: url(data:font/woff2;base64,{dados}) format('woff2'); }}")


# Pilha usada nos SVGs: a embutida primeiro, depois as monoespaçadas comuns
FAMILIA = "'Fira Code Zespek', 'Fira Code', ui-monospace, Consolas, Menlo, monospace"
