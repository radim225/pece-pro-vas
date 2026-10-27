// _redirects neumí podmínku na host. Jen přesný produkční host
// peceprovas.pages.dev (náhledy *.peceprovas.pages.dev ne).
export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  if (url.hostname === 'peceprovas.pages.dev') {
    return Response.redirect('https://www.peceprovas.cz' + url.pathname + url.search, 301);
  }
  return context.next();
}
