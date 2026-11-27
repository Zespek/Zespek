#!/usr/bin/env python3
"""
Cartão de estatísticas do perfil, na identidade Zespek, gerado pela Action todo dia.

    GITHUB_TOKEN=... python ferramentas/estatisticas.py dist/estatisticas.svg

Lê o calendário de contribuições pela API GraphQL do GitHub (todos os anos desde a criação da
conta) e desenha o SVG: total, último ano, sequência atual e maior, melhor dia e as barras dos
últimos 12 meses. Substitui o cartão de serviço de fora, que saía do ar e não tinha as cores da
marca. Requisitos: Python 3.10+ e internet.
"""
import json
import os
import sys
import urllib.request
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fonte import FAMILIA, fira_code  # noqa: E402
from gerar_svgs import (ALERTA, AZUL, BORDA, CLARO, ERRO, FUNDO, LILAS, OK, ROXO,  # noqa: E402
                        ROXO_ESCURO, ROXO_VIVO, SUAVE, TEXTO)

USUARIO = os.environ.get('USUARIO', 'Zespek')
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def graphql(consulta, variaveis):
    corpo = json.dumps({'query': consulta, 'variables': variaveis}).encode()
    pedido = urllib.request.Request('https://api.github.com/graphql', data=corpo, headers={
        'Authorization': f"bearer {os.environ['GITHUB_TOKEN']}", 'Content-Type': 'application/json',
        'User-Agent': 'zespek-perfil'})
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        dados = json.load(resposta)
    if dados.get('errors'):
        raise SystemExit(f"GraphQL: {dados['errors'][0].get('message')}")
    return dados['data']


DIAS = 'contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }'


def coletar():
    base = graphql(f'''query($login: String!) {{ user(login: $login) {{ createdAt
      contributionsCollection {{ contributionYears {DIAS} }} }} }}''', {'login': USUARIO})['user']
    anos = base['contributionsCollection']['contributionYears']
    partes = ' '.join(f'a{a}: contributionsCollection(from: "{a}-01-01T00:00:00Z", to: "{a}-12-31T23:59:59Z") {{ {DIAS} }}' for a in anos)
    por_ano = graphql(f'query($login: String!) {{ user(login: $login) {{ {partes} }} }}', {'login': USUARIO})['user']
    dias = {}
    for colecao in [*por_ano.values(), base['contributionsCollection']]:
        for semana in colecao['contributionCalendar']['weeks']:
            for d in semana['contributionDays']:
                dias[d['date']] = d['contributionCount']
    ultimo_ano = base['contributionsCollection']['contributionCalendar']
    return {
        'desde': base['createdAt'][:4],
        'total': sum(c['contributionCalendar']['totalContributions'] for c in por_ano.values()),
        'ano': ultimo_ano['totalContributions'],
        'dias': dict(sorted(dias.items())),
        'dias_ano': [d for s in ultimo_ano['weeks'] for d in s['contributionDays']],
    }


def sequencias(dias, hoje):
    # O calendário de cada ano vem até 31/12, com os dias que ainda não chegaram zerados
    datas = [d for d in map(date.fromisoformat, dias) if d <= hoje]
    # Hoje ainda sem contribuição não quebra a sequência: conta a partir de ontem
    dia = hoje if dias[hoje.isoformat()] else hoje - timedelta(days=1)
    atual = 0
    while dias.get(dia.isoformat(), 0) > 0:
        atual += 1
        dia -= timedelta(days=1)
    maior = corrida = 0
    anterior = None
    for d in datas:
        if dias[d.isoformat()] > 0:
            corrida = corrida + 1 if anterior and d - anterior == timedelta(days=1) else 1
            maior = max(maior, corrida)
            anterior = d
        else:
            corrida, anterior = 0, None
    return atual, maior


def mil(n):
    return f'{n:,}'.replace(',', '.')


def desenhar(info):
    atual, maior = sequencias(info['dias'], date.fromisoformat(info['dias_ano'][-1]['date']))
    melhor_data, melhor = max(info['dias'].items(), key=lambda kv: (kv[1], kv[0]))
    meses = OrderedDict()
    for d in info['dias_ano']:
        chave = d['date'][:7]
        meses[chave] = meses.get(chave, 0) + d['contributionCount']
    meses = list(meses.items())[-12:]
    agora = datetime.now(timezone(timedelta(hours=-3)))

    largura, altura = 860, 300
    linhas = [
        ('total', mil(info['total'])),
        ('ultimo_ano', mil(info['ano'])),
        ('sequencia_atual', f"{atual} {'dia' if atual == 1 else 'dias'}"),
        ('maior_sequencia', f'{maior} dias'),
        ('melhor_dia', f"{melhor} em {date.fromisoformat(melhor_data).strftime('%d/%m/%Y')}"),
        ('no_github_desde', info['desde']),
    ]
    x0, y0, passo = 28, 92, 30
    texto = [f'<text class="secao" x="{x0}" y="{y0 - 34}">[contribuicoes]</text>']
    for i, (chave, valor) in enumerate(linhas):
        y = y0 + i * passo
        texto.append(f'<text class="liga" style="animation-delay: {0.35 + i * 0.12:.2f}s" x="{x0}" y="{y}">'
                     f'<tspan fill="{LILAS}">{chave.ljust(16)}</tspan><tspan fill="{SUAVE}">= </tspan>'
                     f'<tspan fill="{CLARO}">"{escape(valor)}"</tspan></text>')

    # Barras dos últimos 12 meses: crescem uma atrás da outra e um brilho corre por dentro delas
    bx, base_y, alto, larg_b, vao = 470, 236, 150, 24, 7
    pico = max(v for _, v in meses) or 1
    barras, formas = [], []
    for i, (mes, valor) in enumerate(meses):
        h = max(2, round(valor / pico * alto))
        x = bx + i * (larg_b + vao)
        formas.append(f'<rect x="{x}" y="{base_y - h}" width="{larg_b}" height="{h}"/>')
        destaque = valor == pico
        barras.append(f'<rect class="barra" style="animation-delay: {0.5 + i * 0.07:.2f}s" x="{x}" y="{base_y - h}" '
                      f'width="{larg_b}" height="{h}" fill="{"url(#pico)" if destaque else "url(#coluna)"}"/>')
        barras.append(f'<text class="mes" x="{x + larg_b / 2}" y="{base_y + 18}">{MESES[int(mes[5:]) - 1]}</text>')
        if destaque:
            barras.append(f'<text class="pico liga" style="animation-delay: 1.4s" x="{x + larg_b / 2}" y="{base_y - h - 10}">{mil(valor)}</text>')
    largura_barras = 12 * (larg_b + vao) - vao
    barras.append(f'<rect x="{bx}" y="{base_y}" width="{largura_barras}" height="1" fill="{BORDA}"/>')
    barras.append(f'<text class="legenda" x="{bx}" y="{y0 - 34}">contribuições por mês</text>')

    rodape = f'atualizado em {agora:%d/%m/%Y} às {agora:%H:%M} (Brasília), todo dia pela Action'
    corpo = f'''<defs>
  <pattern id="tubo" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".028"/></pattern>
  <linearGradient id="coluna" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ROXO}"/><stop offset="1" stop-color="{ROXO_ESCURO}" stop-opacity=".55"/></linearGradient>
  <linearGradient id="pico" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CLARO}"/><stop offset=".25" stop-color="{ROXO_VIVO}"/><stop offset="1" stop-color="{ROXO}"/></linearGradient>
  <linearGradient id="topo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ROXO}" stop-opacity=".16"/><stop offset="1" stop-color="{ROXO}" stop-opacity="0"/></linearGradient>
  <linearGradient id="brilho" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <linearGradient id="faixa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ROXO}" stop-opacity="0"/><stop offset=".9" stop-color="{ROXO}" stop-opacity=".10"/><stop offset="1" stop-color="{ROXO}" stop-opacity="0"/></linearGradient>
  <clipPath id="moldura"><rect x="1" y="1" width="{largura - 2}" height="{altura - 2}" rx="10"/></clipPath>
  <clipPath id="area-barras">{''.join(formas)}</clipPath>
</defs>
<g clip-path="url(#moldura)">
  <rect width="{largura}" height="{altura}" fill="{FUNDO}"/>
  <rect width="{largura}" height="120" fill="url(#topo)"/>
  <rect width="{largura}" height="36" fill="#15121b"/>
  <rect y="36" width="{largura}" height="1" fill="{BORDA}"/>
  <circle cx="22" cy="18" r="6" fill="{ERRO}"/><circle cx="42" cy="18" r="6" fill="{ALERTA}"/><circle cx="62" cy="18" r="6" fill="{OK}"/>
  <text class="barra-titulo" x="{largura / 2}" y="22">zespek@github: ~/stats.log</text>
  {''.join(texto)}
  {''.join(barras)}
  <g clip-path="url(#area-barras)"><rect class="reflexo" x="{bx - 120}" y="{base_y - alto - 4}" width="120" height="{alto + 4}" fill="url(#brilho)"/></g>
  <text class="rodape" x="{x0}" y="{altura - 18}">{escape(rodape)}</text>
  <rect width="{largura}" height="{altura}" fill="url(#tubo)"/>
  <rect class="varre" width="{largura}" height="120" fill="url(#faixa)"/>
</g>
<rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="10.5" fill="none" stroke="{BORDA}"/>'''
    todos = ''.join(c for c in corpo if not c.isspace()) + ' "=[]_:/.()' + rodape
    estilo = f'''{fira_code(todos, 500)}
text {{ font: 500 15px {FAMILIA}; white-space: pre; }}
.secao {{ fill: {AZUL}; }}
.barra-titulo {{ fill: {SUAVE}; font-size: 13px; text-anchor: middle; }}
.legenda {{ fill: {SUAVE}; font-size: 13px; }}
.mes {{ fill: {SUAVE}; font-size: 12px; text-anchor: middle; }}
.pico {{ fill: {CLARO}; font-size: 13px; text-anchor: middle; }}
.rodape {{ fill: {SUAVE}; font-size: 12px; }}
.liga {{ animation: liga .45s steps(1, end) backwards; }}
.barra {{ transform-box: fill-box; transform-origin: bottom; animation: cresce .9s cubic-bezier(.2, .8, .3, 1) backwards; }}
.reflexo {{ animation: reflexo 6s ease-in-out 2.5s infinite; }}
.varre {{ transform: translateY(-120px); animation: varre 9s cubic-bezier(.4, 0, .6, 1) 1s infinite; }}
@keyframes liga {{ 0% {{ opacity: 0; }} 25% {{ opacity: 1; }} 45% {{ opacity: .15; }} 65% {{ opacity: 1; }} 80% {{ opacity: .5; }} 100% {{ opacity: 1; }} }}
@keyframes cresce {{ from {{ transform: scaleY(0); }} }}
@keyframes reflexo {{ 0% {{ transform: translateX(0); }} 35%, 100% {{ transform: translateX({largura_barras + 120}px); }} }}
@keyframes varre {{ 0% {{ transform: translateY(-120px); }} 40%, 100% {{ transform: translateY({altura}px); }} }}
@media (prefers-reduced-motion: reduce) {{ .liga, .barra, .reflexo, .varre {{ animation: none; }} .reflexo, .varre {{ display: none; }} }}'''
    resumo = f"Contribuições de {USUARIO}: {mil(info['total'])} no total, {mil(info['ano'])} no último ano, sequência atual de {atual} dias"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" '
            f'role="img" aria-label="{escape(resumo)}">\n<title>{escape(resumo)}</title>\n<style>\n{estilo}\n</style>\n{corpo}\n</svg>\n')


def main():
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else 'dist/estatisticas.svg')
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(desenhar(coletar()), encoding='utf-8')
    print(f'{destino}  {destino.stat().st_size / 1024:.1f} KB')


if __name__ == '__main__':
    main()
