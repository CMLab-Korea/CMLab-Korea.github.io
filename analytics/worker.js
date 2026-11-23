const SITE = 'https://cmlab-korea.github.io';
const PATHS = new Set(['/index.html', '/publications.html', '/people.html', '/join.html',
  '/life.html', '/research.html', '/teaching.html', '/collaborate.html', '/404.html']);

function koreanDay() {
  return new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin');
    const headers = {
      'Access-Control-Allow-Origin': SITE,
      'Cache-Control': 'no-store',
      'Vary': 'Origin'
    };
    const reply = (data, status = 200) => Response.json(data, {status, headers});

    if (url.pathname !== '/visitors' || origin !== SITE) return reply({}, 404);
    if (request.method === 'OPTIONS') {
      return new Response(null, {status: 204, headers: {
        ...headers,
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      }});
    }

    const day = koreanDay();
    if (request.method === 'POST') {
      if (!request.headers.get('Content-Type')?.startsWith('application/json')) {
        return reply({}, 415);
      }
      const body = await request.json().catch(() => null);
      if (!body || typeof body.id !== 'string' || !/^[\da-f-]{36}$/i.test(body.id) || !PATHS.has(body.path)) {
        return reply({}, 400);
      }
      const country = /^[A-Z]{2}$/.test(request.cf?.country || '') ? request.cf.country : 'Unknown';
      await env.DB.batch([
        env.DB.prepare('INSERT OR IGNORE INTO visitors (browser_id, first_seen) VALUES (?, ?)').bind(body.id, day),
        env.DB.prepare('INSERT OR IGNORE INTO visits (day, browser_id, country, path) VALUES (?, ?, ?, ?)')
          .bind(day, body.id, country, body.path)
      ]);
    } else if (request.method !== 'GET') {
      return reply({}, 405);
    }

    const totals = env.DB.prepare(
      'SELECT (SELECT COUNT(*) FROM visitors) AS total, (SELECT COUNT(DISTINCT browser_id) FROM visits WHERE day = ?) AS today'
    ).bind(day);
    if (request.method === 'POST') return reply(await totals.first());

    const [counts, countries, pages] = await env.DB.batch([
      totals,
      env.DB.prepare('SELECT country AS label, COUNT(DISTINCT browser_id) AS count FROM visits GROUP BY country ORDER BY count DESC LIMIT 20'),
      env.DB.prepare('SELECT path AS label, COUNT(DISTINCT browser_id) AS count FROM visits GROUP BY path ORDER BY count DESC')
    ]);
    return reply({...counts.results[0], countries: countries.results, pages: pages.results});
  }
};
