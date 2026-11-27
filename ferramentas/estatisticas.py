#!/usr/bin/env python3
"""
Cartão de estatísticas do perfil, na identidade Zespek, gerado pela Action todo dia.

    GITHUB_TOKEN=... python ferramentas/estatisticas.py dist/estatisticas.svg

Lê o calendário de contribuições pela API GraphQL do GitHub (todos os anos desde a criação da
conta) e desenha o SVG: total, último ano, sequência atual e maior, melhor dia e o gráfico de
área das semanas do último ano, no estilo do gráfico de disponibilidade do painel Zespek. Substitui o cartão de serviço de fora, que saía do ar e não tinha as cores da
marca. Requisitos: Python 3.10+ e internet.
"""
import json
import math
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fonte import FAMILIA, fira_code  # noqa: E402
from gerar_svgs import (ALERTA, AZUL, BORDA, CLARO, ERRO, FUNDO, LILAS, OK, ROXO,  # noqa: E402
                        ROXO_ESCURO, ROXO_VIVO, SUAVE, TEXTO)

USUARIO = os.environ.get('USUARIO', 'Zespek')


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
    # Semanas do último ano, na mesma divisão do calendário do GitHub (começa num domingo)
    inicio = date.fromisoformat(info['dias_ano'][0]['date'])
    semanas = []
    for d in info['dias_ano']:
        i = (date.fromisoformat(d['date']) - inicio).days // 7
        while len(semanas) <= i:
            semanas.append(0)
        semanas[i] += d['contributionCount']
    ativos = sum(1 for d in info['dias_ano'] if d['contributionCount'] > 0)
    agora = datetime.now(timezone(timedelta(hours=-3)))

    largura, altura = 860, 352
    linhas = [
        ('total', mil(info['total'])),
        ('ultimo_ano', mil(info['ano'])),
        ('sequencia_atual', f"{atual} {'dia' if atual == 1 else 'dias'}"),
        ('maior_sequencia', f'{maior} dias'),
        ('melhor_dia', f"{melhor} em {date.fromisoformat(melhor_data).strftime('%d/%m/%Y')}"),
        ('no_github_desde', info['desde']),
    ]
    x0, y0, passo = 28, 104, 30
    texto = [f'<text class="secao" x="{x0}" y="{y0 - 38}">[contribuicoes]</text>']
    for i, (chave, valor) in enumerate(linhas):
        texto.append(f'<text class="liga" style="animation-delay: {0.35 + i * 0.12:.2f}s" x="{x0}" y="{y0 + i * passo}">'
                     f'<tspan fill="{LILAS}">{chave.ljust(16)}</tspan><tspan fill="{SUAVE}">= </tspan>'
                     f'<tspan fill="{CLARO}">"{escape(valor)}"</tspan></text>')

    # Quadro do gráfico no estilo do painel (Disponibilidade da frota): título com o quadrado da
    # marca, selo de agora à direita, área roxa com a linha acesa, grade tracejada, varredura de
    # monitor cruzando a área, um pulso de luz correndo pela linha e o ponto de agora com ping
    qx, qy, ql, qa = 392, 50, 444, 264
    esq, dir_, topo, base = qx + 52, qx + ql - 16, qy + 52, qy + 188
    teto = max(semanas) or 1
    grade = 10 ** max(1, len(str(teto)) - 1)
    teto = math.ceil(teto / grade) * grade
    passo_x = (dir_ - esq) / max(1, len(semanas) - 1)
    pts = [(esq + i * passo_x, base - v / teto * (base - topo)) for i, v in enumerate(semanas)]
    traco = ' '.join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
    area = f'{traco} L{pts[-1][0]:.1f},{base} L{pts[0][0]:.1f},{base} Z'
    px, py = pts[-1]

    def selo(x, y, texto_selo, cor, ancora='start'):
        w = len(texto_selo) * 7.2 + 16
        xr = x - w if ancora == 'end' else x
        return (f'<g class="liga" style="animation-delay: 1.5s"><rect x="{xr:.1f}" y="{y}" width="{w:.1f}" height="22" fill="none" stroke="{cor}"/>'
                f'<text class="selo" x="{xr + 8:.1f}" y="{y + 15}" fill="{cor}">{escape(texto_selo)}</text></g>')

    grafico = [
        f'<rect x="{qx}" y="{qy}" width="{ql}" height="{qa}" fill="#111317" stroke="{BORDA}"/>',
        f'<rect x="{qx + 18}" y="{qy + 18}" width="9" height="9" fill="{ROXO_ESCURO}"/><rect x="{qx + 16}" y="{qy + 16}" width="9" height="9" fill="{ROXO}"/>',
        f'<text class="quadro-titulo" x="{qx + 34}" y="{qy + 25}">CONTRIBUIÇÕES · 12 MESES</text>',
        selo(qx + ql - 16, qy + 10, f'esta semana {mil(semanas[-1])}', OK, 'end'),
    ]
    for v in (0, teto // 2, teto):
        y = base - v / teto * (base - topo)
        grafico.append(f'<line class="grade" x1="{esq}" x2="{dir_}" y1="{y:.1f}" y2="{y:.1f}"/>')
        grafico.append(f'<text class="eixo" x="{esq - 8}" y="{y + 4:.1f}" text-anchor="end">{mil(v)}</text>')
    grafico += [
        f'<g class="revela"><path d="{area}" fill="url(#area)"/><path class="linha" d="{traco}"/></g>',
        f'<path class="pulso" d="{traco}" pathLength="1000"/>',
        f'<g clip-path="url(#area-grafico)"><rect class="varredura" x="{esq - 48}" y="{topo}" width="48" height="{base - topo}" fill="url(#varredura)"/></g>',
        f'<circle class="ping" cx="{px:.1f}" cy="{py:.1f}" r="3.5"/><circle class="ponto liga" style="animation-delay: 1.3s" cx="{px:.1f}" cy="{py:.1f}" r="3.5"/>',
        f'<text class="eixo" x="{esq}" y="{base + 20}">-12 meses</text>',
        f'<text class="eixo" x="{(esq + dir_) / 2:.1f}" y="{base + 20}" text-anchor="middle">-6 meses</text>',
        f'<text class="eixo" x="{dir_}" y="{base + 20}" text-anchor="end">agora</text>',
    ]
    x_selo = qx + 16
    for texto_selo, cor in [(f'média {mil(round(info["ano"] / len(semanas)))}/semana', SUAVE),
                            (f'melhor semana {mil(max(semanas))}', ROXO_VIVO),
                            (f'{ativos} dias ativos', OK)]:
        grafico.append(selo(x_selo, qy + qa - 38, texto_selo, cor))
        x_selo += len(texto_selo) * 7.2 + 16 + 8

    rodape = f'atualizado em {agora:%d/%m/%Y} às {agora:%H:%M} (Brasília), todo dia pela Action'
    corpo = f'''<defs>
  <pattern id="tubo" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".028"/></pattern>
  <linearGradient id="area" x1="0" y1="{topo}" x2="0" y2="{base}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{ROXO}" stop-opacity=".6"/><stop offset="1" stop-color="{ROXO}" stop-opacity=".06"/></linearGradient>
  <linearGradient id="varredura" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{ROXO}" stop-opacity="0"/><stop offset=".96" stop-color="{ROXO}" stop-opacity=".3"/><stop offset=".96" stop-color="{ROXO_VIVO}" stop-opacity=".7"/><stop offset="1" stop-color="{ROXO_VIVO}" stop-opacity=".7"/></linearGradient>
  <linearGradient id="topo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ROXO}" stop-opacity=".16"/><stop offset="1" stop-color="{ROXO}" stop-opacity="0"/></linearGradient>
  <linearGradient id="faixa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ROXO}" stop-opacity="0"/><stop offset=".9" stop-color="{ROXO}" stop-opacity=".10"/><stop offset="1" stop-color="{ROXO}" stop-opacity="0"/></linearGradient>
  <clipPath id="moldura"><rect x="1" y="1" width="{largura - 2}" height="{altura - 2}" rx="10"/></clipPath>
  <clipPath id="area-grafico"><rect x="{esq}" y="{topo}" width="{dir_ - esq}" height="{base - topo}"/></clipPath>
</defs>
<g clip-path="url(#moldura)">
  <rect width="{largura}" height="{altura}" fill="{FUNDO}"/>
  <rect width="{largura}" height="120" fill="url(#topo)"/>
  <rect width="{largura}" height="36" fill="#15121b"/>
  <rect y="36" width="{largura}" height="1" fill="{BORDA}"/>
  <circle cx="22" cy="18" r="6" fill="{ERRO}"/><circle cx="42" cy="18" r="6" fill="{ALERTA}"/><circle cx="62" cy="18" r="6" fill="{OK}"/>
  <text class="barra-titulo" x="{largura / 2}" y="22">zespek@github: ~/stats.log</text>
  {''.join(texto)}
  {''.join(grafico)}
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
.quadro-titulo {{ fill: {TEXTO}; font-size: 12px; letter-spacing: .5px; }}
.selo {{ font-size: 12px; }}
.eixo {{ fill: {SUAVE}; font-size: 12px; }}
.grade {{ stroke: {BORDA}; stroke-width: 1; stroke-dasharray: 2 4; }}
.linha {{ fill: none; stroke: {ROXO}; stroke-width: 2; stroke-linejoin: round; filter: drop-shadow(0 0 3px rgba(189, 0, 255, .8)); }}
.pulso {{ fill: none; stroke: #f4d6ff; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 60 1000; stroke-dashoffset: 60; filter: drop-shadow(0 0 3px {ROXO}); animation: pulso 3.6s linear 1.6s infinite; }}
.ponto {{ fill: {ROXO}; filter: drop-shadow(0 0 4px {ROXO}); }}
.ping {{ fill: none; stroke: {ROXO}; transform-box: fill-box; transform-origin: center; animation: ping 2s cubic-bezier(.2, .6, .4, 1) 1.3s infinite; opacity: 0; }}
.rodape {{ fill: {SUAVE}; font-size: 12px; }}
.liga {{ animation: liga .45s steps(1, end) backwards; }}
.revela {{ animation: revela 1s cubic-bezier(.2, .7, .3, 1) .5s backwards; }}
.varredura {{ animation: varredura 4s linear 1.5s infinite; transform: translateX(-10px); }}
.varre {{ transform: translateY(-120px); animation: varre 9s cubic-bezier(.4, 0, .6, 1) 1s infinite; }}
@keyframes liga {{ 0% {{ opacity: 0; }} 25% {{ opacity: 1; }} 45% {{ opacity: .15; }} 65% {{ opacity: 1; }} 80% {{ opacity: .5; }} 100% {{ opacity: 1; }} }}
@keyframes revela {{ from {{ clip-path: inset(0 100% 0 0); }} }}
@keyframes pulso {{ to {{ stroke-dashoffset: -1000; }} }}
@keyframes ping {{ from {{ transform: scale(1); opacity: .9; }} to {{ transform: scale(4.5); opacity: 0; }} }}
@keyframes varredura {{ from {{ transform: translateX(0); }} to {{ transform: translateX({dir_ - esq + 48}px); }} }}
@keyframes varre {{ 0% {{ transform: translateY(-120px); }} 40%, 100% {{ transform: translateY({altura}px); }} }}
@media (prefers-reduced-motion: reduce) {{ .liga, .revela, .pulso, .ping, .varredura, .varre {{ animation: none; }} .pulso, .ping, .varredura, .varre {{ display: none; }} }}'''
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
