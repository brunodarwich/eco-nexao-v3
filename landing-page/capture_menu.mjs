import { spawn } from 'child_process';
import fs from 'fs';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "file:///c:/Users/Bruno/Downloads/eco-nexao-v3/landing-page/index.html";

async function run() {
  const chrome = spawn(CHROME_PATH, [
    '--headless=new',
    '--remote-debugging-port=9777',
    '--disable-gpu',
    '--no-sandbox',
    'about:blank'
  ]);
  await new Promise(r => setTimeout(r, 1200));

  const res = await fetch('http://127.0.0.1:9777/json/list');
  const [tab] = await res.json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);

  let id = 1;
  const send = (method, params = {}) => new Promise((resolve) => {
    const curId = id++;
    const h = (e) => {
      const m = JSON.parse(e.data);
      if (m.id === curId) {
        ws.removeEventListener('message', h);
        resolve(m.result);
      }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: curId, method, params }));
  });

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.navigate', { url: TARGET_URL });
  await new Promise(r => setTimeout(r, 1500));

  await send('Emulation.setDeviceMetricsOverride', {
    width: 375,
    height: 812,
    deviceScaleFactor: 2,
    mobile: true
  });

  await send('Runtime.evaluate', {
    expression: `
      window.scrollTo(0, 0);
      const btn = document.getElementById('mobile-toggle');
      if (btn) btn.click();
    `
  });
  await new Promise(r => setTimeout(r, 500));

  const ss = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('qa_screenshots/19_mobile_menu_open_clean.png', Buffer.from(ss.data, 'base64'));
  console.log('Mobile menu open captured successfully!');
  ws.close();
  chrome.kill();
}

run();
