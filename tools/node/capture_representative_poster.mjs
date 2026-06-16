/**
 * Representative poster pipeline: PIL 4-act narrative compose (no Playwright by default).
 * Usage: npm run capture-app-poster
 * Optional: CAPTURE_VIDEO_INTRO=1 to also capture video intro for demo assets.
 */
import { mkdir } from 'node:fs/promises';
import { OUT_DIR } from './lib/appPosterSnapshot.mjs';
import {
  buildApp,
  runPython,
  startPreview,
  waitForServer,
} from './lib/previewServer.mjs';
import { captureVideoIntroPoster, videoPosterUrl } from './lib/captureVideoPoster.mjs';

const PORT = Number(process.env.CAPTURE_PORT || 5174);
const BASE = `http://127.0.0.1:${PORT}`;
const CAPTURE_VIDEO_INTRO = process.env.CAPTURE_VIDEO_INTRO === '1';

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  let server = null;
  let exitCode = 0;

  try {
    if (CAPTURE_VIDEO_INTRO) {
      console.log('Building app (CAPTURE_VIDEO_INTRO=1)…');
      await buildApp();
      console.log(`Starting preview on ${BASE}…`);
      server = startPreview(PORT);
      await waitForServer(`${BASE}/video.html`);

      const pageUrl = videoPosterUrl(BASE, 'intro');
      console.log(`Capturing video intro ${pageUrl}…`);
      const videoPath = await captureVideoIntroPoster({ pageUrl });
      console.log(`Video intro → ${videoPath}`);
    }

    console.log('Composing narrative poster (4-act science story → 3840×5200)…');
    await runPython('tools/python/compose_representative_poster.py');
    console.log('Done.');
  } catch (e) {
    console.error(e);
    exitCode = 1;
  } finally {
    if (server) server.kill('SIGTERM');
    process.exit(exitCode);
  }
}

main();
