// _redirects neumí podmínku na host. Jen přesný produkční host
// peceprovas.pages.dev (náhledy *.peceprovas.pages.dev ne).
//
// Opt-out z měření pro naše zařízení: ?nesledovat nastaví cookie ze serveru.
// Safari maže localStorage (i cookie z JS) po 7 dnech bez návštěvy, cookie
// ze serveru ne. Každá návštěva s cookie ji prodlouží o dalších 400 dní
// (víc Chrome nedovolí). ?sledovat ji smaže. Inline skript v index.html
// cookie čte, proto nesmí být HttpOnly.
const COOKIE = 'peceprovas-nesledovat';
const MAX_AGE = 400 * 24 * 60 * 60;

export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  if (url.hostname === 'peceprovas.pages.dev') {
    return Response.redirect('https://www.peceprovas.cz' + url.pathname + url.search, 301);
  }

  const hasCookie = (request.headers.get('Cookie') || '')
    .split(';').some((c) => c.trim() === COOKIE + '=1');
  let setCookie = null;
  if (url.searchParams.has('nesledovat') || (hasCookie && !url.searchParams.has('sledovat'))) {
    setCookie = `${COOKIE}=1; Max-Age=${MAX_AGE}; Path=/; Secure; SameSite=Lax`;
  } else if (url.searchParams.has('sledovat')) {
    setCookie = `${COOKIE}=; Max-Age=0; Path=/; Secure; SameSite=Lax`;
  }

  const response = await context.next();
  if (!setCookie) return response;
  const out = new Response(response.body, response);
  out.headers.append('Set-Cookie', setCookie);
  return out;
}
