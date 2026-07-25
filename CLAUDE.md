# Web kosmetického salonu Péče PRO VÁS — pravidla

Jednostránkový statický web reálné firmy. Live: <https://www.peceprovas.cz>.
Jediný `index.html`, žádný build step, žádné závislosti. Push do `main` = **okamžitý deploy na živý web**.
Klientkou je Radimova mamka, která salon provozuje — její formulace mají přednost před našimi.

## Slovník — závazné

**Slovo „ošetření" se na webu nesmí objevit.** *(mamka, 2026-07-25)* Používá se **„kosmetická péče"**, ve zkrácené podobě **„péče"**.

Platí to na **celý web**, ne jen na viditelný text: nadpisy, menu, popisky karet, `alt`, `aria-label`, meta description i kotvy v URL (sekce má proto `id="kosmeticka-pece"`, ne `#osetreni`).

Nejde o hledání a nahrazení jedním výrazem — čeština to nedovolí. Řiď se smyslem věty:

| Nefunguje | Použij |
|---|---|
| „Každé ošetření volím…" → „Každá péče volím…" | „Péči volím vždy…" |
| „Každé ošetření je prožitek" | „Kosmetická péče je u nás prožitek" |
| „před ošetřením a po něm" | „před návštěvou salonu a po ní" |
| „Vyberte ošetření" + „zahrnuje kompletní **péči**" | přeformuluj druhou půlku, ať se „péče" neopakuje dvakrát v sousedních větách |

Kontrola před commitem: `grep -i "ošetř" index.html` musí být prázdné.

## Popisky produktů a ošetřujících úkonů

**Piš jen to, co je doložitelné** — text na obalu produktu nebo už existující text webu. Nic nedomýšlej, nedopočítávej texturu ani účinky z fotky. Dřívější návrh obsahoval smyšlený claim („posilují přirozenou obranu pleti"), faktickou chybu („tělové mléko", ačkoli na tubě stojí jen `BODY`) a claim přiřčený produktům, na kterých natištěný není. U kosmetiky na webu reálné firmy je to kategorie chyb, která se nesmí dostat ven.

**Cizí reklamní banner potřebuje rámec.** `product.JPG` a `tonikum_bruno.JPEG` jsou hotové reklamy Bruno Vassari s vysázenou grafikou a neklikatelnými tlačítky. Salon **nic neprodává online** — každé CTA vede na `tel:` nebo `wa.me`. Banner musí sedět v sekci, která ho vysvětlí a nabídne funkční akci (telefon), jinak slibuje něco, co web neumí.

## Technické pasti

- **Přípony `.JPG`/`.JPEG` velkými písmeny** (`main.JPG`, `product.JPG`, `bruno_katalog.JPEG`, `tonikum_bruno.JPEG`). Vercel běží na case-sensitive filesystemu — `main.jpg` vrátí 404. Nepřejmenovávej bez úpravy `index.html`.
- **Push velkých binárek přes HTTP padá** na `send-pack: unexpected disconnect`. Prochází s `git -c http.postBuffer=524288000 push origin main`. **Vždy ověř, že push dosedl:** `git rev-list --left-right --count origin/main...HEAD` musí dát `0 0` (git umí zavádějícně hlásit „Everything up-to-date").
- **Rám fotky se přizpůsobuje fotce, ne naopak.** Poměry stran v CSS odpovídají nativním rozměrům, aby `object-fit: cover` neuřízl vysázený text na bannerech ani polovinu srovnávacího snímku před/po.
- **Vercel Web Analytics** měří jen díky ručně vloženému `<script defer src="/_vercel/insights/script.js">` před `</body>`. U statického HTML se nevloží sám — nemazat, jinak měření tiše umře.

## Jak ověřovat změny

Lokálně `python3 -m http.server 8899 --bind 127.0.0.1`, pak v prohlížeči přes `<iframe>` s pevnou šířkou (screenshot celého okna je moc široký a ořezává). Standardní sada:

- responzivní sweep na **320 / 360 / 390 / 430 / 600 / 768 / 861 / 1000 / 1024 / 1440 px** — horizontální scroll, kolize v hlavičce, poměry fotek
- žádná rozbitá fotka (`img.complete && img.naturalWidth > 0`) — pozor, `loading="lazy"` fotky mimo viewport hlásí `false` legitimně
- žádná mrtvá kotva (`href="#…"` bez odpovídajícího `id`)
- `html { scroll-behavior: smooth }` znamená, že `scrollTo()` animuje — při měření používej `behavior:'instant'`

Skutečné breakpointy: **1000 px** (desktop nav ↔ hamburger + plovoucí lišta), **430 px** (skrytí tagu „KOSMETIKA"), **360 px** (zmenšení wordmarku vedle tlačítka Zavolat).

## Wiki

Po každém smysluplném kusu práce aktualizuj `Radim OS/Wiki/pages/projects/Kosmetika Péče PRO VÁS.md`, `Wiki/index.md` a připiš do `Wiki/log.md` — postup ve `Radim OS/Wiki/CLAUDE.md`.
