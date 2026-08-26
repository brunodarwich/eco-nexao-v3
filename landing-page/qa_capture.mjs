import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "file:///c:/Users/Bruno/Downloads/eco-nexao-v3/landing-page/index.html";
const OUT_DIR = "c:\\Users\\Bruno\\Downloads\\eco-nexao-v3\\landing-page\\qa_screenshots";

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function run() {
  const port = 9555;
  const chrome = spawn(CHROME_PATH, [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    '--disable-gpu',
    '--no-sandbox',
    '--hide-scrollbars',
    '--mute-audio',
    'about:blank'
  ]);

  await new Promise(r => setTimeout(r, 1500));

  try {
    const versionRes = await fetch(`http://127.0.0.1:${port}/json/version`);
    const versionData = await versionRes.json();
    const listRes = await fetch(`http://127.0.0.1:${port}/json/list`);
    const listData = await listRes.json();
    let pageTarget = listData.find(t => t.type === 'page');

    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise(res => ws.onopen = res);

    let id = 1;
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const curId = id++;
        const handler = (e) => {
          const m = JSON.parse(e.data);
          if (m.id === curId) {
            ws.removeEventListener('message', handler);
            if (m.error) reject(m.error);
            else resolve(m.result);
          }
        };
        ws.addEventListener('message', handler);
        ws.send(JSON.stringify({ id: curId, method, params }));
      });
    }

    await send('Page.enable');
    await send('DOM.enable');
    await send('Runtime.enable');

    console.log('Navigating to target URL...');
    await send('Page.navigate', { url: TARGET_URL });
    await new Promise(r => setTimeout(r, 1500));

    // Force all reveal elements visible & disable transitions for clean capture
    await send('Runtime.evaluate', {
      expression: `
        (() => {
          const style = document.createElement('style');
          style.innerHTML = \`
            .reveal, .reveal.active, .js-ready .reveal, .js-ready .reveal.active {
              opacity: 1 !important;
              transform: none !important;
              transition: none !important;
              visibility: visible !important;
            }
          \`;
          document.head.appendChild(style);
          document.querySelectorAll('.reveal').forEach(e => e.classList.add('active'));
        })()
      `
    });

    async function captureViewport(filename) {
      const res = await send('Page.captureScreenshot', {
        format: 'png',
        captureBeyondViewport: true
      });
      const buffer = Buffer.from(res.data, 'base64');
      const filePath = path.join(OUT_DIR, filename);
      fs.writeFileSync(filePath, buffer);
      console.log(`Saved screenshot: ${filePath} (${(buffer.length / 1024).toFixed(1)} KB)`);
    }

    async function scrollToElement(selector) {
      await send('Runtime.evaluate', {
        expression: `
          (() => {
            const el = document.querySelector('${selector}');
            if (el) {
              el.scrollIntoView({ behavior: 'instant', block: 'start' });
            }
          })()
        `
      });
      await new Promise(r => setTimeout(r, 200));
    }

    async function captureElement(selector, filename) {
      await scrollToElement(selector);
      const res = await send('Runtime.evaluate', {
        expression: `
          (() => {
            const el = document.querySelector('${selector}');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: Math.max(0, r.x), y: Math.max(0, r.y), width: r.width, height: r.height, scale: 1 };
          })()
        `,
        returnByValue: true
      });
      const clip = res.result.value;
      if (!clip || clip.width <= 0 || clip.height <= 0) {
        console.warn(`Could not get bounds for ${selector}`);
        return;
      }
      const captureRes = await send('Page.captureScreenshot', {
        format: 'png',
        clip: {
          x: 0,
          y: Math.round(clip.y),
          width: Math.round(clip.width),
          height: Math.min(Math.round(clip.height), 3000),
          scale: 1
        },
        captureBeyondViewport: true
      });
      const buffer = Buffer.from(captureRes.data, 'base64');
      const filePath = path.join(OUT_DIR, filename);
      fs.writeFileSync(filePath, buffer);
      console.log(`Saved element screenshot: ${filePath} (${(buffer.length / 1024).toFixed(1)} KB)`);
    }

    // 1. DESKTOP VIEWPORT (1440x900)
    console.log('=== DESKTOP AUDIT (1440x900) ===');
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false
    });
    await new Promise(r => setTimeout(r, 500));

    // Full Desktop Capture
    const docLayout = await send('Page.getLayoutMetrics');
    const fullHeightDesktop = Math.ceil(docLayout.contentSize.height);
    console.log(`Desktop page total height: ${fullHeightDesktop}px`);

    const fullDeskRes = await send('Page.captureScreenshot', {
      format: 'png',
      clip: { x: 0, y: 0, width: 1440, height: fullHeightDesktop, scale: 1 },
      captureBeyondViewport: true
    });
    fs.writeFileSync(path.join(OUT_DIR, '01_desktop_full.png'), Buffer.from(fullDeskRes.data, 'base64'));
    console.log('Saved 01_desktop_full.png');

    // Desktop Sections
    await captureElement('#header', '02_desktop_header.png');
    await captureElement('#hero', '03_desktop_hero.png');
    await captureElement('#proposta', '04_desktop_proposta.png');
    await captureElement('#showcase', '05_desktop_showcase.png');
    await captureElement('#rota-piloto', '06_desktop_rota_piloto.png');
    await captureElement('#publicos', '07_desktop_impacto.png');
    await captureElement('#tecnologia', '08_desktop_tecnologia.png');
    await captureElement('#contato', '09_desktop_contato_footer.png');

    // Showcase 6 Tabs
    for (let tabIndex = 0; tabIndex < 6; tabIndex++) {
      await send('Runtime.evaluate', {
        expression: `
          const tabs = document.querySelectorAll('.tab-btn');
          if (tabs[${tabIndex}]) tabs[${tabIndex}].click();
        `
      });
      await new Promise(r => setTimeout(r, 300));
      await captureElement('#showcase-screen-panel', `05_desktop_showcase_tab_${tabIndex + 1}.png`);
    }

    // 2. MOBILE VIEWPORT (375x812)
    console.log('=== MOBILE AUDIT (375x812) ===');
    await send('Emulation.setDeviceMetricsOverride', {
      width: 375,
      height: 812,
      deviceScaleFactor: 2,
      mobile: true
    });
    await new Promise(r => setTimeout(r, 600));

    const mobileDocLayout = await send('Page.getLayoutMetrics');
    const fullHeightMobile = Math.ceil(mobileDocLayout.contentSize.height);
    console.log(`Mobile page total height: ${fullHeightMobile}px`);

    const fullMobileRes = await send('Page.captureScreenshot', {
      format: 'png',
      clip: { x: 0, y: 0, width: 375, height: fullHeightMobile, scale: 1 },
      captureBeyondViewport: true
    });
    fs.writeFileSync(path.join(OUT_DIR, '10_mobile_full_375.png'), Buffer.from(fullMobileRes.data, 'base64'));
    console.log('Saved 10_mobile_full_375.png');

    await captureElement('#hero', '12_mobile_hero.png');
    await captureElement('#proposta', '13_mobile_proposta.png');
    await captureElement('#showcase', '14_mobile_showcase.png');
    await captureElement('#rota-piloto', '15_mobile_rota_piloto.png');
    await captureElement('#publicos', '16_mobile_impacto.png');
    await captureElement('#tecnologia', '17_mobile_tecnologia.png');
    await captureElement('#contato', '18_mobile_contato_footer.png');

    // Mobile Drawer Open
    console.log('=== Mobile Menu Open ===');
    await scrollToElement('#header');
    await send('Runtime.evaluate', {
      expression: `
        const btn = document.getElementById('mobile-toggle');
        if (btn && btn.getAttribute('aria-expanded') !== 'true') {
          btn.click();
        }
      `
    });
    await new Promise(r => setTimeout(r, 400));
    const menuRes = await send('Page.captureScreenshot', {
      format: 'png',
      clip: { x: 0, y: 0, width: 375, height: 812, scale: 1 },
      captureBeyondViewport: true
    });
    fs.writeFileSync(path.join(OUT_DIR, '19_mobile_menu_open.png'), Buffer.from(menuRes.data, 'base64'));
    console.log('Saved 19_mobile_menu_open.png');

    // Close menu
    await send('Runtime.evaluate', {
      expression: `
        const btn = document.getElementById('mobile-toggle');
        if (btn && btn.getAttribute('aria-expanded') === 'true') {
          btn.click();
        }
      `
    });

    // 3. MOBILE VIEWPORT (412x915)
    console.log('=== MOBILE AUDIT (412x915) ===');
    await send('Emulation.setDeviceMetricsOverride', {
      width: 412,
      height: 915,
      deviceScaleFactor: 2,
      mobile: true
    });
    await new Promise(r => setTimeout(r, 500));
    const layout412 = await send('Page.getLayoutMetrics');
    const full412Res = await send('Page.captureScreenshot', {
      format: 'png',
      clip: { x: 0, y: 0, width: 412, height: Math.ceil(layout412.contentSize.height), scale: 1 },
      captureBeyondViewport: true
    });
    fs.writeFileSync(path.join(OUT_DIR, '20_mobile_full_412.png'), Buffer.from(full412Res.data, 'base64'));
    console.log('Saved 20_mobile_full_412.png');

    console.log('--- ALL SCREENSHOTS CAPTURED SUCCESSFULLY ---');
    ws.close();
  } catch (err) {
    console.error('Error during capture:', err);
  } finally {
    chrome.kill();
  }
}

run();
