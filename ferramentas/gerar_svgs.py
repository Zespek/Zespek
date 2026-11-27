#!/usr/bin/env python3
"""
Gera os SVGs animados do README (pasta svg/): os títulos das seções, o terminal de abertura e
a caveira do rodapé.

    python ferramentas/gerar_svgs.py

Tudo fica no próprio repositório, sem depender de serviço de fora: o título não aparece mais
pela metade quando o serviço demora. A animação é SMIL e CSS dentro do SVG, que o GitHub
mostra no <img>. Para mudar um texto, edite TITULOS ou TERMINAL abaixo e rode de novo.
Requisitos: Python 3.10+ e internet (a Fira Code vem do Google Fonts, ver fonte.py).
"""
import base64
import math
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
# Cada linha: (partes já na tela, comando digitado ou None, instante em segundos)
TERMINAL = [
    (PROMPT, 'whoami', 0.5),
    ([('José Felipe · CTO | Tech Governance | KMP® | Agile Coach | Teacher', CLARO)], None, 1.5),
    (PROMPT, 'cat ./foco_atual.txt', 2.2),
    ([('> ', OK), ('segurança de aplicações e servidores em produção', TEXTO)], None, 3.7),
    ([('> ', OK), ('acho a falha antes de outra pessoa e fecho com o time', TEXTO)], None, 4.0),
    ([('> ', OK), ('governança técnica e times ágeis com Kanban', TEXTO)], None, 4.3),
    (PROMPT, None, 4.8),
]
CICLO, SOME = 16.0, 15.2  # o terminal limpa em SOME e recomeça a cada CICLO segundos


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


# ---------- Terminal de abertura: digita, responde, limpa e recomeça ----------

def terminal(fonte):
    tam, cw, linha = 15, 9.0, 27
    largura, altura = 860, 262
    x0, y0 = 26, 76
    corpo, cursor = [], []  # cursor: (instante, x, y)
    for i, (partes, comando, t) in enumerate(TERMINAL):
        y = y0 + i * linha
        fixo = ''.join(p for p, _ in partes)
        tspans = ''.join(f'<tspan fill="{cor}">{escape(p)}</tspan>' for p, cor in partes)
        n_fixo = len(fixo)
        # A primeira linha já começa na tela; as outras aparecem no instante t
        if i == 0:
            vals, tempos = [round(n_fixo * cw, 1), 0], [0, SOME]
            cursor.append((0, x0 + n_fixo * cw, y))
        else:
            vals, tempos = [0, round(n_fixo * cw, 1), 0], [0, t, SOME]
        if comando:
            tspans += f'<tspan fill="{TEXTO}">{escape(comando)}</tspan>'
            inicio = t + (0 if i == 0 else 0.35)
            if i != 0:
                cursor.append((t, x0 + n_fixo * cw, y))
            vals, tempos = vals[:-1], tempos[:-1]
            for k in range(1, len(comando) + 1):
                vals.append(round((n_fixo + k) * cw, 1))
                tempos.append(inicio + k * 0.06)
                cursor.append((inicio + k * 0.06, x0 + (n_fixo + k) * cw, y))
            vals.append(0)
            tempos.append(SOME)
        elif i == len(TERMINAL) - 1:
            cursor.append((t, x0 + n_fixo * cw, y))
        # 4 px a mais para não cortar a última letra (o rect começa 2 px antes do texto)
        vals = [round(v + 4, 1) if v else 0 for v in vals]
        tempos_n = ';'.join(f'{min(tp / CICLO, 1):.4f}' for tp in tempos)
        comprimento = len(fixo) + len(comando or '')
        # Sem SMIL fica a linha inteira na tela (o width do rect), com o terminal já respondido
        corpo.append(f'''<clipPath id="l{i}"><rect x="{x0 - 2}" y="{y - linha / 2}" height="{linha}" width="{comprimento * cw + 4:g}">
  <animate attributeName="width" values="{lista(vals)}" keyTimes="{tempos_n}" calcMode="discrete" dur="{CICLO}s" repeatCount="indefinite"/>
</rect></clipPath>
<g clip-path="url(#l{i})"><text x="{x0}" y="{y}" textLength="{comprimento * cw:g}" lengthAdjust="spacingAndGlyphs" dominant-baseline="central">{tspans}</text></g>''')
    cursor.sort()
    _, fim_x, fim_y = cursor[-1]
    cursor.append((SOME, -40, y0))
    tempos_c = ';'.join(f'{tp / CICLO:.4f}' for tp, _, _ in cursor)
    corpo.append(f'''<rect class="cursor" x="{fim_x + 1:g}" y="{fim_y - 9:g}" width="{cw:g}" height="18" fill="{ROXO}">
  <animate attributeName="x" values="{lista([x + 1 for _, x, _ in cursor])}" keyTimes="{tempos_c}" calcMode="discrete" dur="{CICLO}s" repeatCount="indefinite"/>
  <animate attributeName="y" values="{lista([y - 9 for _, _, y in cursor])}" keyTimes="{tempos_c}" calcMode="discrete" dur="{CICLO}s" repeatCount="indefinite"/>
</rect>''')
    janela = f'''<defs>
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
  <clipPath id="moldura"><rect x="1" y="1" width="{largura - 2}" height="{altura - 2}" rx="10"/></clipPath>
</defs>
<g clip-path="url(#moldura)">
  <rect width="{largura}" height="{altura}" fill="{FUNDO}"/>
  <rect width="{largura}" height="120" fill="url(#topo)"/>
  <rect width="{largura}" height="36" fill="#15121b"/>
  <rect y="36" width="{largura}" height="1" fill="{BORDA}"/>
  <circle cx="22" cy="18" r="6" fill="{ERRO}"/><circle cx="42" cy="18" r="6" fill="{ALERTA}"/><circle cx="62" cy="18" r="6" fill="{OK}"/>
  <text class="barra" x="{largura / 2}" y="18" text-anchor="middle" dominant-baseline="central">zespek@server: ~</text>
  {chr(10).join(corpo)}
  <rect width="{largura}" height="{altura}" fill="url(#tubo)"/>
  <rect class="varre" width="{largura}" height="110" fill="url(#faixa)"/>
  <rect class="luz" y="{altura - 2}" width="220" height="2" fill="url(#luz)"/>
</g>
<rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="10.5" fill="none" stroke="{BORDA}"/>'''
    estilo = f'''{fonte}
text {{ font: 500 {tam}px {FAMILIA}; white-space: pre; }}
.barra {{ fill: {SUAVE}; font-size: 13px; }}
.cursor {{ animation: pisca 1s steps(1) infinite; }}
.varre {{ animation: varre 8s cubic-bezier(.4, 0, .6, 1) 1s infinite; transform: translateY(-110px); }}
.luz {{ animation: corre 6s linear infinite; transform: translateX(-220px); }}
@keyframes pisca {{ 50% {{ opacity: 0; }} }}
@keyframes varre {{ 0% {{ transform: translateY(-110px); }} 45%, 100% {{ transform: translateY({altura}px); }} }}
@keyframes corre {{ to {{ transform: translateX({largura}px); }} }}
@media (prefers-reduced-motion: reduce) {{ .cursor, .varre, .luz {{ animation: none; }} .varre, .luz {{ display: none; }} }}'''
    return svg(largura, altura, janela, estilo, 'zespek@server: whoami. José Felipe, CTO | Tech Governance | KMP® | Agile Coach | Teacher')


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
    (SAIDA / 'caveira.svg').write_text(caveira(), encoding='utf-8')
    for arquivo in sorted(SAIDA.glob('*.svg')):
        print(f'{arquivo.relative_to(RAIZ)}  {arquivo.stat().st_size / 1024:.1f} KB')


if __name__ == '__main__':
    main()
