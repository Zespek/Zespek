#!/usr/bin/env python3
"""
Gera os SVGs animados do README (pasta svg/): os títulos das seções, o terminal de abertura, as
janelas de terminal de cada seção e a caveira do rodapé.

    python ferramentas/gerar_svgs.py

Tudo fica no próprio repositório, sem depender de serviço de fora: o título não aparece mais
pela metade quando o serviço demora. A animação é SMIL e CSS dentro do SVG, que o GitHub
mostra no <img>. As janelas têm a cara do Windows (ícone e título à esquerda, minimizar,
maximizar e fechar à direita).

O texto de cada seção vem do próprio README: o bloco ```ini logo depois de cada
<img src="./svg/secao-NOME.svg"> vira a janela secao-NOME.svg, que digita o comando e imprime
as linhas. Para mudar um texto, edite o bloco no README (ou TITULOS e TERMINAL abaixo) e rode
de novo. Requisitos: Python 3.10+ e internet (a Fira Code vem do Google Fonts, ver fonte.py).
"""
import base64
import math
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fonte import FAMILIA, fira_code  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'svg'

# Cores da marca (as mesmas do painel e do banner)
ROXO, ROXO_ESCURO, ROXO_VIVO = '#bd00ff', '#8300b3', '#d14dff'
LILAS, CLARO, AZUL = '#c08cff', '#f3daff', '#6f86ff'
OK, ALERTA, ERRO = '#2ee8d0', '#ffb000', '#ff1f3d'
TEXTO, SUAVE, FUNDO, BORDA = '#e8e9eb', '#8a919c', '#0d0b11', '#2b2733'
BARRA = '#15121b'

TITULOS = {
    'resumo': '>_ ./resumo_profissional.sh',
    'engenharia': '>_ ./dominio_em_engenharia_e_deploy.sh',
    'seguranca': '>_ ./seguranca_em_producao.sh',
    'lideranca': '>_ ./lideranca_tecnica_e_agil.sh',
    'formacao': '>_ ./formacao_academica.sh',
    'arsenal': '>_ ./arsenal_tecnologico.sh',
    'stats': '>_ ./github_stats.sh',
    'conecte': '>_ ./conecte_se.sh',
}

PROMPT = [('zespek@server', ROXO_VIVO), (':~', AZUL), ('$ ', TEXTO)]
# Cada linha: (partes fixas, comando digitado ou None, instante em que aparece). Na linha que
# aparece em 0 s o comando começa a ser digitado em 0,4 s; nas outras, 0,35 s depois de aparecer
TERMINAL = [
    (PROMPT, 'whoami', 0),
    ([('José Felipe · CTO | Tech Governance | KMP® | Agile Coach | Teacher', CLARO)], None, 1.5),
    (PROMPT, 'cat ./foco_atual.txt', 2.2),
    ([('> ', OK), ('segurança de aplicações e servidores em produção', TEXTO)], None, 3.7),
    ([('> ', OK), ('acho a falha antes de outra pessoa e fecho com o time', TEXTO)], None, 4.0),
    ([('> ', OK), ('governança técnica e times ágeis com Kanban', TEXTO)], None, 4.3),
    (PROMPT, None, 4.8),
]
CICLO, SOME = 16.0, 15.2  # o terminal de abertura limpa em SOME e recomeça a cada CICLO segundos
LARGURA = 860


def svg(largura, altura, corpo, estilo, titulo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" '
            f'aria-label="{escape(titulo)}">\n<title>{escape(titulo)}</title>\n'
            f'<style>\n{estilo}\n</style>\n{corpo}\n</svg>\n')


def lista(valores):
    return ';'.join(f'{v:g}' if isinstance(v, (int, float)) else v for v in valores)


# ---------- Títulos: digitados uma vez, cursor piscando e um glitch nos dois roxos ----------

def titulo(texto, fonte):
    tam, passo = 22, 0.055
    cw = tam * 0.6  # avanço da Fira Code: 600/1000 em
    n = len(texto)
    largura_texto = n * cw
    largura, altura = math.ceil(largura_texto + cw * 1.6 + 6), 40
    x0, y = 2, 21
    # O rect já nasce com a largura do título inteiro: quem não roda SMIL vê o texto parado. A
    # animação começa no 0 s e espera 0,3 s com zeros; os 3 px a mais não cortam a última letra
    atraso = round(0.3 / passo)
    larguras = [0] * atraso + [round(i * cw + 3, 2) if i else 0 for i in range(n + 1)]
    cursor_x = [x0 + 3] * atraso + [round(x0 + i * cw + 3, 2) for i in range(n + 1)]
    duracao = f'{len(larguras) * passo:.2f}s'
    texto_svg = (f'<text x="{x0}" y="{y}" textLength="{largura_texto:g}" lengthAdjust="spacingAndGlyphs" '
                 f'dominant-baseline="central">{escape(texto)}</text>')
    corpo = f'''<defs>
  <clipPath id="digitado"><rect x="0" y="0" height="{altura}" width="{larguras[-1]}">
    <animate attributeName="width" values="{lista(larguras)}" calcMode="discrete" begin="0s" dur="{duracao}" fill="freeze"/>
  </rect></clipPath>
</defs>
<g clip-path="url(#digitado)">
  <g class="glitch">
    <g class="fantasma f1">{texto_svg}</g>
    <g class="fantasma f2">{texto_svg}</g>
    <g class="principal">{texto_svg}</g>
  </g>
</g>
<rect class="cursor" x="{cursor_x[-1]}" y="{y - 11}" width="{cw * 0.62:.1f}" height="22" fill="{ROXO}">
  <animate attributeName="x" values="{lista(cursor_x)}" calcMode="discrete" begin="0s" dur="{duracao}" fill="freeze"/>
</rect>'''
    estilo = f'''{fonte}
text {{ font: 600 {tam}px {FAMILIA}; }}
.principal {{ fill: {ROXO}; }}
.f1 {{ fill: {ROXO_ESCURO}; transform: translateX(-3px); }}
.f2 {{ fill: {ROXO_VIVO}; transform: translateX(3px); }}
.fantasma {{ opacity: 0; animation: fantasma 7s 2.5s steps(1) infinite; }}
.glitch {{ transform-box: fill-box; transform-origin: center; animation: glitch 7s 2.5s infinite; }}
.cursor {{ animation: pisca 1.1s steps(1) infinite; }}
@keyframes pisca {{ 50% {{ opacity: 0; }} }}
@keyframes fantasma {{ 0%, 88%, 93%, 100% {{ opacity: 0; }} 89%, 91% {{ opacity: .85; }} }}
@keyframes glitch {{
  0%, 88%, 93%, 100% {{ transform: none; }}
  89% {{ transform: translate(-2px, 1px) skewX(-8deg); }}
  90% {{ transform: translate(3px, -1px); }}
  91% {{ transform: translate(-1px, 0) skewX(5deg); }}
}}
@media (prefers-reduced-motion: reduce) {{ .glitch, .fantasma, .cursor {{ animation: none; }} }}'''
    return svg(largura, altura, corpo, estilo, texto)


# ---------- Janela no estilo do Windows, usada pelos terminais e pelo cartão de estatísticas ----------

def barra_windows(largura, titulo_barra):
    """Barra de título do Windows: ícone do terminal e título à esquerda; minimizar, maximizar e
    fechar à direita, cada botão com 46 px como no Windows 11."""
    fechar, maximizar, minimizar = largura - 23, largura - 69, largura - 115
    return f'''<rect width="{largura}" height="34" fill="{BARRA}"/>
  <rect y="34" width="{largura}" height="1" fill="{BORDA}"/>
  <rect x="12" y="9" width="16" height="16" rx="3" fill="{ROXO}"/>
  <path d="M15.5 13l3.2 3.8-3.2 3.8" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="20.2" y="19.8" width="5" height="1.6" fill="#fff"/>
  <text class="barra" x="38" y="17.5" dominant-baseline="central">{escape(titulo_barra)}</text>
  <g fill="none" stroke="{TEXTO}" stroke-width="1" opacity=".8">
    <path d="M{minimizar - 5} 17.5h10"/>
    <rect x="{maximizar - 4.5}" y="12.5" width="9" height="9"/>
    <path d="M{fechar - 4.5} 12.5l9 9M{fechar + 4.5} 12.5l-9 9"/>
  </g>'''


def janela(largura, altura, titulo_barra, conteudo, defs_extra=''):
    """Fundo, barra do Windows, o conteúdo, linhas de tubo, a faixa de varredura descendo e a luz
    correndo na borda de baixo."""
    return f'''<defs>
  <pattern id="tubo" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".028"/></pattern>
  <linearGradient id="faixa" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{ROXO}" stop-opacity="0"/><stop offset=".85" stop-color="{ROXO}" stop-opacity=".10"/>
    <stop offset=".98" stop-color="{ROXO}" stop-opacity=".22"/><stop offset="1" stop-color="{ROXO}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="topo" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{ROXO}" stop-opacity=".16"/><stop offset="1" stop-color="{ROXO}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="luz" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{ROXO}" stop-opacity="0"/><stop offset=".5" stop-color="{ROXO_VIVO}"/><stop offset="1" stop-color="{ROXO}" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="moldura"><rect x="1" y="1" width="{largura - 2}" height="{altura - 2}" rx="8"/></clipPath>
  {defs_extra}
</defs>
<g clip-path="url(#moldura)">
  <rect width="{largura}" height="{altura}" fill="{FUNDO}"/>
  <rect width="{largura}" height="120" fill="url(#topo)"/>
  {barra_windows(largura, titulo_barra)}
  {conteudo}
  <rect width="{largura}" height="{altura}" fill="url(#tubo)"/>
  <rect class="varre" width="{largura}" height="110" fill="url(#faixa)"/>
  <rect class="luz" y="{altura - 2}" width="220" height="2" fill="url(#luz)"/>
</g>
<rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="8.5" fill="none" stroke="{BORDA}"/>'''


def estilo_janela(altura, largura=LARGURA):
    return f'''.barra {{ fill: {SUAVE}; font-size: 13px; }}
.cursor {{ animation: pisca 1s steps(1) infinite; }}
.varre {{ animation: varre 8s cubic-bezier(.4, 0, .6, 1) 1s infinite; transform: translateY(-110px); }}
.luz {{ animation: corre 6s linear infinite; transform: translateX(-220px); }}
@keyframes pisca {{ 50% {{ opacity: 0; }} }}
@keyframes varre {{ 0% {{ transform: translateY(-110px); }} 45%, 100% {{ transform: translateY({altura}px); }} }}
@keyframes corre {{ to {{ transform: translateX({largura}px); }} }}
@media (prefers-reduced-motion: reduce) {{ .cursor, .varre, .luz {{ animation: none; }} .varre, .luz {{ display: none; }} }}'''


# ---------- Linhas de terminal: o comando é digitado e a resposta aparece linha a linha ----------

def animar_linhas(linhas, x0, y0, alt_linha, cw, tecla, ciclo=None, some=None):
    """Com ciclo, limpa em `some` e recomeça (terminal de abertura); sem ciclo, roda uma vez e
    fica parado no fim com o cursor piscando (seções). Sem SMIL, tudo já aparece inteiro."""
    eventos_linhas, cursor = [], []  # cursor: (instante, x, y)
    for i, (partes, comando, t) in enumerate(linhas):
        y = y0 + i * alt_linha
        n_fixo = len(''.join(p for p, _ in partes))
        eventos = [(0, n_fixo)] if t <= 0 else [(0, 0), (t, n_fixo)]
        if comando:
            cursor.append((t, x0 + n_fixo * cw, y))
            inicio = t + (0.4 if t <= 0 else 0.35)
            for k in range(1, len(comando) + 1):
                eventos.append((inicio + k * tecla, n_fixo + k))
                cursor.append((inicio + k * tecla, x0 + (n_fixo + k) * cw, y))
        elif i == len(linhas) - 1:
            cursor.append((t, x0 + n_fixo * cw, y))
        eventos_linhas.append(eventos)
    total = ciclo or max(t for ev in eventos_linhas for t, _ in ev) + 0.01
    repete = 'repeatCount="indefinite"' if ciclo else 'fill="freeze"'
    corpo = []
    for i, ((partes, comando, _), eventos) in enumerate(zip(linhas, eventos_linhas)):
        if not partes and not comando:
            continue
        y = y0 + i * alt_linha
        if ciclo:
            eventos = eventos + [(some, 0)]
        larguras = [round(n * cw + 4, 1) if n else 0 for _, n in eventos]
        tempos = ';'.join(f'{min(t / total, 1):.4f}' for t, _ in eventos)
        comprimento = sum(len(p) for p, _ in partes) + len(comando or '')
        tspans = ''.join(f'<tspan fill="{cor}">{escape(p)}</tspan>' for p, cor in partes)
        if comando:
            tspans += f'<tspan fill="{TEXTO}">{escape(comando)}</tspan>'
        corpo.append(f'''<clipPath id="l{i}"><rect x="{x0 - 2}" y="{y - alt_linha / 2}" height="{alt_linha}" width="{comprimento * cw + 4:g}">
  <animate attributeName="width" values="{lista(larguras)}" keyTimes="{tempos}" calcMode="discrete" dur="{total:.2f}s" {repete}/>
</rect></clipPath>
<g clip-path="url(#l{i})"><text x="{x0}" y="{y}" textLength="{comprimento * cw:g}" lengthAdjust="spacingAndGlyphs" dominant-baseline="central">{tspans}</text></g>''')
    cursor.sort()
    _, fim_x, fim_y = cursor[-1]
    if ciclo:
        cursor.append((some, -40, y0))
    tempos_c = ';'.join(f'{min(t / total, 1):.4f}' for t, _, _ in cursor)
    alto = round(alt_linha * 0.68)
    corpo.append(f'''<rect class="cursor" x="{fim_x + 1:g}" y="{fim_y - alto / 2:g}" width="{cw:g}" height="{alto}" fill="{ROXO}">
  <animate attributeName="x" values="{lista([x + 1 for _, x, _ in cursor])}" keyTimes="{tempos_c}" calcMode="discrete" dur="{total:.2f}s" {repete}/>
  <animate attributeName="y" values="{lista([y - alto / 2 for _, _, y in cursor])}" keyTimes="{tempos_c}" calcMode="discrete" dur="{total:.2f}s" {repete}/>
</rect>''')
    return '\n  '.join(corpo)


def terminal(fonte):
    tam, cw, alt_linha = 15, 9.0, 27
    altura = 262
    conteudo = animar_linhas(TERMINAL, 26, 72, alt_linha, cw, 0.06, CICLO, SOME)
    estilo = f'''{fonte}
text {{ font: 500 {tam}px {FAMILIA}; white-space: pre; }}
{estilo_janela(altura)}'''
    return svg(LARGURA, altura, janela(LARGURA, altura, 'zespek@server: ~', conteudo), estilo,
               'zespek@server: whoami. José Felipe, CTO | Tech Governance | KMP® | Agile Coach | Teacher')


# ---------- Seções: o bloco ini do README vira uma janela que digita o cat e imprime o arquivo ----------

SECAO_TAM, SECAO_CW, SECAO_LINHA, SECAO_MAX = 14, 8.4, 23, 96


def quebrar(linha):
    """Linha maior que a janela quebra na última palavra que cabe, com recuo de continuação."""
    saida = []
    while len(linha) > SECAO_MAX:
        corte = linha.rfind(' ', 0, SECAO_MAX)
        saida.append(linha[:corte])
        linha = '      ' + linha[corte + 1:]
    return saida + [linha]


def partes_ini(linha):
    if not linha:
        return []
    if linha.startswith('  - '):
        return [('  - ', SUAVE), (linha[4:], CLARO)]
    if linha.startswith('      '):
        return [(linha, CLARO)]
    if linha.startswith('[ '):
        return [(linha, AZUL)]
    if linha.startswith('['):
        return [(linha, LILAS)]
    return [(linha, TEXTO)]


def secoes_do_readme():
    readme = (RAIZ / 'README.md').read_text(encoding='utf-8')
    achadas = re.findall(r'<img src="\./svg/secao-([\w-]+)\.svg"[^>]*>.*?```ini\n(.*?)\n```', readme, re.S)
    return {nome: bloco.splitlines() for nome, bloco in achadas}


def secao(linhas_ini, fonte):
    comando = linhas_ini[0].split('$ ', 1)[1]
    saida = [l for linha in linhas_ini[1:] for l in quebrar(linha)]
    linhas = [(PROMPT, comando, 0)]
    t = 0.4 + len(comando) * 0.035 + 0.3
    for k, linha in enumerate(saida):
        linhas.append((partes_ini(linha), None, t + k * 0.06))
    linhas.append((PROMPT, None, t + len(saida) * 0.06 + 0.2))
    y0 = 34 + 26
    altura = y0 + (len(linhas) - 1) * SECAO_LINHA + 26
    conteudo = animar_linhas(linhas, 24, y0, SECAO_LINHA, SECAO_CW, 0.035)
    estilo = f'''{fonte}
text {{ font: 500 {SECAO_TAM}px {FAMILIA}; white-space: pre; }}
{estilo_janela(altura)}'''
    rotulo = f'zespek@server: {comando}. ' + ' '.join(l.strip() for l in linhas_ini[1:] if l.strip())
    return svg(LARGURA, altura, janela(LARGURA, altura, 'zespek@server: ~', conteudo), estilo, rotulo)


# ---------- Caveira do rodapé: a faixa de varredura atravessa a arte e um glitch de vez em quando ----------

def caveira():
    png = (RAIZ / 'banner' / 'caveira-zespek.png').read_bytes()
    largura, altura = 1144, 664
    dados = base64.b64encode(png).decode()
    corpo = f'''<defs>
  <image id="arte" width="{largura}" height="{altura}" href="data:image/png;base64,{dados}"/>
  <mask id="forma" style="mask-type: alpha"><use href="#arte"/></mask>
  <linearGradient id="feixe" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{CLARO}" stop-opacity="0"/><stop offset=".5" stop-color="{CLARO}" stop-opacity=".95"/>
    <stop offset="1" stop-color="{CLARO}" stop-opacity="0"/>
  </linearGradient>
</defs>
<g class="glitch">
  <use class="fantasma" href="#arte" x="-10" opacity="0"/>
  <use href="#arte"/>
</g>
<g mask="url(#forma)"><rect class="feixe" x="0" y="-60" width="{largura}" height="60" fill="url(#feixe)"/></g>'''
    estilo = f'''.feixe {{ animation: feixe 7s ease-in-out 1s infinite; }}
.glitch {{ animation: glitch 9s 4s infinite; }}
.fantasma {{ animation: fantasma 9s 4s steps(1) infinite; filter: hue-rotate(-25deg) brightness(.6); }}
@keyframes feixe {{ 0% {{ transform: translateY(0); }} 30%, 100% {{ transform: translateY({altura + 60}px); }} }}
@keyframes glitch {{ 0%, 90%, 94%, 100% {{ transform: none; }} 91% {{ transform: translate(-8px, 3px); }} 92.5% {{ transform: translate(10px, -2px); }} }}
@keyframes fantasma {{ 0%, 90%, 94%, 100% {{ opacity: 0; }} 91%, 92.5% {{ opacity: .9; }} }}
@media (prefers-reduced-motion: reduce) {{ .feixe, .glitch, .fantasma {{ animation: none; }} .feixe {{ display: none; }} }}'''
    return svg(largura, altura, corpo, estilo, 'Zespek')


def main():
    SAIDA.mkdir(exist_ok=True)
    fonte_titulos = fira_code(''.join(TITULOS.values()), 600)
    for nome, texto in TITULOS.items():
        (SAIDA / f'titulo-{nome}.svg').write_text(titulo(texto, fonte_titulos), encoding='utf-8')
    texto_terminal = ''.join(p for partes, c, _ in TERMINAL for p, _ in partes) + ''.join(c or '' for _, c, _ in TERMINAL)
    fonte_terminal = fira_code(texto_terminal + 'zespek@server: ~', 500)
    (SAIDA / 'terminal.svg').write_text(terminal(fonte_terminal), encoding='utf-8')
    secoes = secoes_do_readme()
    if secoes:
        fonte_secoes = fira_code(''.join(''.join(b) for b in secoes.values()) + 'zespek@server: ~$', 500)
        for nome, linhas_ini in secoes.items():
            (SAIDA / f'secao-{nome}.svg').write_text(secao(linhas_ini, fonte_secoes), encoding='utf-8')
    (SAIDA / 'caveira.svg').write_text(caveira(), encoding='utf-8')
    for arquivo in sorted(SAIDA.glob('*.svg')):
        print(f'{arquivo.relative_to(RAIZ)}  {arquivo.stat().st_size / 1024:.1f} KB')


if __name__ == '__main__':
    main()
