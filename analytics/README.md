# Visitor counts

GitHub Pages hosts the visitor interface. A Cloudflare Worker and D1 database store unique browser counts across the site and per Korean calendar day. The public breakdown groups visitors by country and page path. It uses a random browser ID and Cloudflare country codes. The application does not read, store, or publish IP addresses.

1. Create a D1 database in a Cloudflare account controlled by CMLab and apply `schema.sql`.
2. Deploy `worker.js` as a Cloudflare Worker and bind the database under the variable name `DB`.
3. Set `endpoint` in `data/visitor-settings.json` to the deployed HTTPS Worker URL with the path `/visitors`. Merge the change through the site's usual review process.
4. Load the GitHub Pages homepage in a browser and check the footer. Browse a second page to verify that the same browser counts once in site totals and once in each visited page's breakdown.

Counts represent browsers with persistent local storage, so a new browser or cleared storage starts a new count. Today's count resets on the Asia/Seoul calendar. Counts start after deployment.
