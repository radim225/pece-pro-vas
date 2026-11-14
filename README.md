# Péče PRO VÁS

Statický web [www.peceprovas.cz](https://www.peceprovas.cz). Žádný build, výstupní adresář je kořen repozitáře (`index.html`, `soukromi.html`, `404.html`).

**Hosting:** Cloudflare Pages (projekt napojený na GitHub). Vercel běží dočasně souběžně, dokud se nepřepne DNS. Doména se nemění. `vercel.json` v repu zůstává, aby Vercel dál fungoval.

Push do `main` pořád hned nasadí živý web na Vercelu a po napojení i Cloudflare Pages.

Pravidla textu a kontrolní příkazy jsou v `CLAUDE.md`.
