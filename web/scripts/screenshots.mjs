/**
 * Documentation screenshot capture.
 *
 * Serves the production build and photographs each surface at a fixed device profile, so
 * the images in the README are reproducible rather than hand-cropped. Run: `pnpm shots`.
 *
 * The shots wait on network idle AND the fonts, then hold for the videos to paint a real
 * frame — a documentation screenshot of a black <video> would misrepresent the product.
 */
import { chromium } from "playwright";
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { join, extname } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = join(fileURLToPath(new URL("..", import.meta.url)), "dist");
const OUT = join(fileURLToPath(new URL("../..", import.meta.url)), "docs/assets/screenshots");

const MIME = {
  ".html": "text/html", ".css": "text/css", ".js": "text/javascript",
  ".json": "application/json", ".svg": "image/svg+xml", ".jpg": "image/jpeg",
  ".png": "image/png", ".mp4": "video/mp4", ".woff2": "font/woff2",
};

// A tiny static server that mirrors directory-style routing (/path -> /path/index.html).
async function serve(port) {
  const server = createServer(async (req, res) => {
    try {
      let p = decodeURIComponent(req.url.split("?")[0]);
      let file = join(DIST, p);
      const s = await stat(file).catch(() => null);
      if (s?.isDirectory() || !extname(p)) file = join(DIST, p, "index.html");
      const body = await readFile(file);
      res.setHeader("Content-Type", MIME[extname(file)] ?? "application/octet-stream");
      res.end(body);
    } catch {
      res.statusCode = 404;
      res.end("not found");
    }
  });
  await new Promise((r) => server.listen(port, r));
  return server;
}

const SHOTS = [
  { name: "01-landing-hero", path: "/overview/", w: 1440, h: 900 },
  { name: "02-findings", path: "/findings/", w: 1440, h: 900 },
  { name: "03-findings-comparison", path: "/findings/", w: 1440, h: 900, y: 900 },
  { name: "04-data", path: "/data/", w: 1440, h: 900 },
  { name: "05-build", path: "/build/", w: 1440, h: 1200, y: 260 },
  { name: "06-validation", path: "/validation/", w: 1440, h: 1000 },
  { name: "07-pipeline", path: "/pipeline/", w: 1440, h: 900 },
  { name: "08-findings-method", path: "/findings/method/", w: 1440, h: 1000, y: 500 },
  { name: "mobile-overview", path: "/overview/", w: 390, h: 844, dsf: 2 },
  { name: "mobile-findings", path: "/findings/", w: 390, h: 844, dsf: 2 },
  { name: "mobile-data", path: "/data/", w: 390, h: 844, dsf: 2 },
];

const PORT = 4477;
const server = await serve(PORT);
const browser = await chromium.launch();

for (const shot of SHOTS) {
  const ctx = await browser.newContext({
    viewport: { width: shot.w, height: shot.h },
    deviceScaleFactor: shot.dsf ?? 1.5, // 1.5x desktop is crisp at GitHub's display width
    colorScheme: "dark",
  });
  const page = await ctx.newPage();
  // Neutralize scroll-reveal utilities so below-fold content is captured, without touching
  // the video/scrim opacity the composition depends on. Motion stays ON so footage renders.
  await page.addInitScript(() => {
    const s = document.createElement("style");
    s.textContent = ".reveal,.reveal-fade,.reveal-stagger>*,.flow,.flow-parallax{animation:none!important;opacity:1!important;transform:none!important;filter:none!important}";
    document.documentElement.appendChild(s);
    new MutationObserver(() => document.head && document.head.appendChild(s.cloneNode(true))).observe(document.documentElement, { childList: true });
  });
  await page.goto(`http://localhost:${PORT}${shot.path}`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1400); // let video posters/frames paint
  if (shot.y) await page.evaluate((y) => window.scrollTo(0, y), shot.y);
  await page.waitForTimeout(400);
  await page.screenshot({ path: join(OUT, `${shot.name}.png`) });
  console.log(`  ${shot.name}.png  ${shot.w}x${shot.h}`);
  await ctx.close();
}

await browser.close();
server.close();
console.log("done");
