import { spawn } from 'child_process';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "file:///c:/Users/Bruno/Downloads/eco-nexao-v3/landing-page/index.html";

async function run() {
  const port = 9444;
  const chrome = spawn(CHROME_PATH, [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    '--disable-gpu',
    '--no-sandbox',
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
    await send('Runtime.enable');
    await send('Page.navigate', { url: TARGET_URL });
    await new Promise(r => setTimeout(r, 1500));

    const diag = await send('Runtime.evaluate', {
      expression: `
        (() => {
          const sections = ['#header', '#hero', '#proposta', '#showcase', '#rota-piloto', '#publicos', '#tecnologia', '#contato', 'footer'];
          return sections.map(sel => {
            const el = document.querySelector(sel);
            if (!el) return { sel, found: false };
            const r = el.getBoundingClientRect();
            const cs = window.getComputedStyle(el);
            return {
              sel,
              found: true,
              rect: { x: r.x, y: r.y, width: r.width, height: r.height },
              display: cs.display,
              visibility: cs.visibility,
              opacity: cs.opacity,
              classes: el.className,
              childCount: el.children.length,
              firstChildClass: el.firstElementChild ? el.firstElementChild.className : null,
              firstChildOpacity: el.firstElementChild ? window.getComputedStyle(el.firstElementChild).opacity : null
            };
          });
        })()
      `,
      returnByValue: true
    });

    console.log('DIAGNOSTICS:', JSON.stringify(diag.result.value, null, 2));

    ws.close();
  } catch (e) {
    console.error(e);
  } finally {
    chrome.kill();
  }
}

run();
