/**
 * One-shot poster save — used by Vite dev API and `npm run save-poster`.
 * Usage: node tools/node/snapshot_app_poster_once.mjs [baseUrl]
 */
import { capturePageUrl, snapshotAppPoster } from './lib/appPosterSnapshot.mjs';

const base =
  process.argv[2] ??
  process.env.CAPTURE_BASE ??
  `http://127.0.0.1:${process.env.CAPTURE_PORT || 5173}`;

const fullScroll = process.env.CAPTURE_FULL === '1';
const pageUrl = base.includes('app.html') ? base : capturePageUrl(base, { fullScroll });

try {
  const result = await snapshotAppPoster({ pageUrl, fullScroll });
  process.stdout.write(
    JSON.stringify({
      ok: true,
      pageUrl,
      resized: result.resized,
      copies: result.copies,
    }),
  );
} catch (err) {
  process.stderr.write(String(err instanceof Error ? err.stack ?? err.message : err));
  process.exit(1);
}
