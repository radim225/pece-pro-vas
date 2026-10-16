#!/usr/bin/env python3
"""Synchronizace Google recenzí do pole RECENZE v index.html (POC, znovupoužitelné pro další weby).

Deterministické jádro: stáhne recenze, převede je na řádky pole RECENZE a přepíše jen blok
`var RECENZE = [ ... ];`. Nic nenasazuje. Změnu vždy schvaluje člověk přes PR (viz workflow).

Zdroje (`source` v konfiguraci):
  maps-public  neoficiální veřejná data Google Map. Jen pro test, může kdykoli přestat fungovat.
  gbp-api      oficiální Google Business Profile API (zdarma, vyžaduje schválený přístup a OAuth).
               Env: GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN.

Pojistky: 0 stažených recenzí → konec bez zápisu. Méně recenzí než na webu → konec bez zápisu
(smazání recenze je rozhodnutí člověka, ne skriptu), pokud není --allow-shrink.

Použití:
  python3 scripts/recenze_sync.py               # zapíše změny do cílového souboru
  python3 scripts/recenze_sync.py --check       # jen porovná; exit 1 = web je zastaralý
  python3 scripts/recenze_sync.py --config jina.json
Exit: 0 beze změny / zapsáno, 1 změna (--check), 2 chyba nebo zásah pojistky.
"""
import argparse, datetime, html, json, os, re, sys, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

MESICE = ['leden', 'únor', 'březen', 'duben', 'květen', 'červen',
          'červenec', 'srpen', 'září', 'říjen', 'listopad', 'prosinec']
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
BLOK = re.compile(r'(?P<head>^[ \t]*var RECENZE = \[)(?P<body>.*?)(?P<tail>^[ \t]*\];)', re.S | re.M)
HVEZDY = {'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5}


def http(url, data=None, headers=None):
    h = {'User-Agent': UA, 'Accept-Language': 'cs', 'Cookie': 'CONSENT=YES+cb'}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


# ---------- zdroje: každý vrací [{author, stars, time (datetime UTC), text}] ----------

def zdroj_maps_public(cfg):
    page = http(cfg['maps_url'])
    m = re.search(r'<link href="(/maps/preview/place\?[^"]+)"', page)
    if not m:
        raise RuntimeError('Na stránce Map chybí odkaz /maps/preview/place (změnil Google formát?)')
    raw = http('https://www.google.com' + html.unescape(m.group(1)))
    data = json.loads(raw.split('\n', 1)[1] if raw.startswith(")]}'") else raw)
    try:
        polozky = data[6][175][9][0][0]
    except (IndexError, TypeError):
        raise RuntimeError('Ve stažených datech nejsou recenze na očekávaném místě (změnil Google formát?)')
    out = []
    for p in polozky:
        r = p[0]
        try:
            text = r[2][15][0][0]
        except (IndexError, TypeError):
            text = ''  # hodnocení bez textu
        out.append({
            'author': r[1][4][5][0],
            'stars': int(r[2][0][0]),
            'time': datetime.datetime.fromtimestamp(r[1][2] / 1e6, datetime.timezone.utc),
            'text': text,
        })
    return out


def zdroj_gbp_api(cfg):
    """Oficiální API (v4 reviews). Nevyzkoušeno proti živému API, dokud Google neschválí přístup."""
    try:
        token_body = urllib.parse.urlencode({
            'client_id': os.environ['GBP_CLIENT_ID'],
            'client_secret': os.environ['GBP_CLIENT_SECRET'],
            'refresh_token': os.environ['GBP_REFRESH_TOKEN'],
            'grant_type': 'refresh_token',
        }).encode()
    except KeyError as e:
        raise RuntimeError(f'Chybí proměnná prostředí {e} pro gbp-api')
    token = json.loads(http('https://oauth2.googleapis.com/token', token_body,
                            {'Content-Type': 'application/x-www-form-urlencoded'}))['access_token']
    base = 'https://mybusiness.googleapis.com/v4/accounts/%s/locations/%s/reviews' % (
        cfg['gbp_account'], cfg['gbp_location'])
    out, page = [], None
    while True:
        q = {'pageSize': 50, 'orderBy': 'updateTime desc'}
        if page:
            q['pageToken'] = page
        d = json.loads(http(base + '?' + urllib.parse.urlencode(q), headers={'Authorization': 'Bearer ' + token}))
        for r in d.get('reviews', []):
            text = r.get('comment', '')
            if '(Original)' in text:  # Google přidává strojový překlad; bereme originál
                text = text.split('(Original)', 1)[1]
            text = text.replace('(Translated by Google)', '').strip()
            out.append({
                'author': r['reviewer'].get('displayName', ''),
                'stars': HVEZDY.get(r.get('starRating'), 0),
                'time': datetime.datetime.fromisoformat(r['createTime'].replace('Z', '+00:00')),
                'text': text,
            })
        page = d.get('nextPageToken')
        if not page:
            return out


ZDROJE = {'maps-public': zdroj_maps_public, 'gbp-api': zdroj_gbp_api}


# ---------- převod na pole RECENZE ----------

def jmeno(author, fmt):
    author = author.strip()
    if fmt == 'full' or ' ' not in author:
        return author
    first, rest = author.split(' ', 1)
    return f'{first} {rest.strip()[0]}.'  # 'first_initial': „Daniela F.“


def radky(recenze, cfg):
    tz = ZoneInfo(cfg.get('timezone', 'Europe/Prague'))
    vyber = [r for r in recenze if r['text'].strip() and 1 <= r['stars'] <= 5]
    vyber.sort(key=lambda r: r['time'], reverse=True)  # nejnovější první
    if cfg.get('max'):
        vyber = vyber[:cfg['max']]
    out = []
    for r in vyber:
        t = r['time'].astimezone(tz)
        out.append('    { name: %s, stars: %d, date: %s, text: %s }' % (
            json.dumps(jmeno(r['author'], cfg.get('name_format', 'first_initial')), ensure_ascii=False),
            r['stars'],
            json.dumps(f'{MESICE[t.month - 1]} {t.year}', ensure_ascii=False),
            json.dumps(r['text'].strip(), ensure_ascii=False)))
    return out


def pocet(n):
    return f'{n} recenze' if n == 1 else (f'{n} recenze' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else f'{n} recenzí')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default=os.path.join(os.path.dirname(__file__), 'recenze.json'))
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--allow-shrink', action='store_true')
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding='utf-8'))
    cil = os.path.join(os.path.dirname(os.path.abspath(a.config)), cfg['target'])
    src = open(cil, encoding='utf-8').read()
    m = BLOK.search(src)
    if not m:
        print(f'CHYBA: v {cil} chybí blok "var RECENZE = [ ... ];"', file=sys.stderr); return 2

    try:
        recenze = ZDROJE[cfg['source']](cfg)
    except Exception as e:
        print(f'CHYBA zdroje {cfg["source"]}: {e}', file=sys.stderr); return 2
    nove = radky(recenze, cfg)
    stare = [l for l in m.group('body').strip('\n').split('\n') if l.strip().startswith('{')]

    if not nove:
        print('POJISTKA: zdroj nevrátil žádnou recenzi s textem, nic nezapisuju.', file=sys.stderr); return 2
    if len(nove) < len(stare) and not a.allow_shrink:
        print(f'POJISTKA: na webu je {pocet(len(stare))}, zdroj vrátil {len(nove)}. '
              'Nic nezapisuju (případně --allow-shrink).', file=sys.stderr); return 2

    body = '\n' + ',\n'.join(nove) + '\n'
    vysledek = src[:m.start('body')] + body + src[m.end('body'):]
    if vysledek == src:
        print(f'Beze změny ({pocet(len(nove))}, zdroj {cfg["source"]}).'); return 0
    if a.check:
        print(f'ZMĚNA: web má {pocet(len(stare))}, zdroj {len(nove)}.'); return 1
    open(cil, 'w', encoding='utf-8').write(vysledek)
    print(f'Zapsáno: {pocet(len(nove))} do {cfg["target"]} (předtím {len(stare)}).'); return 0


if __name__ == '__main__':
    sys.exit(main())
