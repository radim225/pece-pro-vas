// Počítadlo pro záložku „Web“ v mamčině aplikaci tržeb (Supabase, EU).
// Ukládá jen den, typ (návštěva / klik na telefon / klik na WhatsApp),
// doménu, odkud návštěvník přišel, a mobil/počítač. Žádná cookie, IP ani
// celý User-Agent se neukládá. Zařízení s cookie peceprovas-nesledovat
// a roboti se nepočítají. Publishable klíč je veřejný; RPC web_hit umí jen
// přičíst 1 a tabulku přes něj číst nejde.
const SUPABASE = 'https://ffyjubuvdeywlhjzckdv.supabase.co/rest/v1/rpc/web_hit';
const KEY = 'sb_publishable_18nG9qvZpxZ_LRdGrwI4QQ_bqEBOFtZ';
const KINDS = ['navsteva', 'telefon', 'whatsapp'];

function zdroj(ref) {
  try {
    const host = new URL(ref).hostname.replace(/^www\./, '');
    return host.endsWith('peceprovas.cz') ? '' : host;
  } catch (e) {
    return '';
  }
}

export async function onRequestPost({ request }) {
  const done = new Response(null, { status: 204 });
  const cookie = request.headers.get('Cookie') || '';
  if (cookie.split(';').some((c) => c.trim() === 'peceprovas-nesledovat=1')) return done;
  const ua = request.headers.get('User-Agent') || '';
  if (!ua || /bot|crawl|spider|slurp|headless|lighthouse|preview/i.test(ua)) return done;

  let data = {};
  try { data = await request.json(); } catch (e) {}
  if (!KINDS.includes(data.kind)) return done;

  await fetch(SUPABASE, {
    method: 'POST',
    headers: { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      p_kind: data.kind,
      p_source: data.kind === 'navsteva' ? zdroj(data.ref || '') : '',
      p_device: /Mobi|Android|iPhone|iPad/i.test(ua) ? 'mobil' : 'pocitac',
    }),
  }).catch(() => {});
  return done;
}
