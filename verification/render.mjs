// Render reviewed statechart outputs with Pele 1.9.0, installed outside this repo.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const modulePath = path.resolve(process.argv[2]);
const packagePath = path.resolve(path.dirname(modulePath),'../package.json');
if (JSON.parse(fs.readFileSync(packagePath,'utf8')).version !== '1.9.0') throw Error('Use pele@1.9.0');
const { render } = await import(pathToFileURL(modulePath).href);
const root = path.resolve(import.meta.dirname, 'charts');
const entries = [
 ['ExampleFlow','Export a reference','The error branch returns the owner, renames the window, then exits before explicit close. Process exit may still reclaim the X11 resource.'],
 ['ReferenceLifetime','Use a borrowed reference','Expiry and ID reuse break consumer assumptions, not the library contract. “No window” breaks the live-reference assumption; “another window” breaks both assumptions. Both were replayed on Xvfb.'],
 ['Observer','Observe the window','A silent producer can block either line read. The final process-exit timeout does not cover those reads. Internal lookup and cleanup steps are grouped for readability.'],
 ['ExportBridge','Export contract','All modeled outcomes return the same owner. Successful export synchronizes earlier requests and preserves queued events.'],
 ['CheckPipeline','Run the checks','The model covers normal command failures and cleanup. Forced termination and failures in trap installation or cleanup are outside its scope.'],
];
const css = `.pele{--pele-bg:#fff;--pele-fg:#1c1c1c;--pele-muted:#656565;--pele-line:#808080;--pele-surface:#fcfcfc;--pele-surface-alt:#f1f1f1;--pele-border:#c9c9c9}.pele .blue rect{fill:#c3e0ff}.pele .teal rect{fill:#bfe3df}.pele .orange rect{fill:#f0d3bf}.pele .pink rect{fill:#ffcbe6}.pele .breaks rect{fill:#ffecee!important;stroke:#e72e3b!important;stroke-width:2.5px!important}.pele .breaks text{fill:#cd2834!important}.pele .bugPath rect{stroke:#1680f3!important;stroke-width:2.5px!important}@media(prefers-color-scheme:dark){.pele{--pele-bg:#1f1f1f;--pele-fg:#f5f5f5;--pele-muted:#acacac;--pele-line:#939393;--pele-surface:#121212;--pele-surface-alt:#2c2c2c;--pele-border:#4e4e4e}.pele .blue rect{fill:#1b3857}.pele .teal rect{fill:#174641}.pele .orange rect{fill:#573117}.pele .pink rect{fill:#57233e}.pele .breaks rect{fill:#2e2021!important;stroke:#cf2b35!important}.pele .breaks text{fill:#ff6463!important}}`;
const escape = value => value.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const sections=[];
for (const [model,label,note] of entries) {
 const dir=path.join(root,model);
 const mermaid=fs.readFileSync(path.join(dir,'chart.mmd'),'utf8');
 const report=fs.readFileSync(path.join(dir,'report.md'),'utf8');
 const result=render(mermaid,{limit:1_000_000,outputLimit:8_000_000,maxEdges:10_000,idPrefix:model});
 const svg=result.svg.replace(/(<svg\b[^>]*>)/,`$1<style>${css}</style>`);
 fs.writeFileSync(path.join(dir,'chart.svg'),svg);
 const src='data:image/svg+xml;base64,'+Buffer.from(svg).toString('base64');
 sections.push(`<section role="tabpanel" id="${model}" ${model==='ExampleFlow'?'':'hidden'}><p>${escape(note)}</p><div class="canvas"><img src="${src}" alt="${escape(label)} statechart" style="width:100%"></div><details><summary>Mermaid source and checker report</summary><pre><code class="language-mermaid">${escape(mermaid)}</code></pre><pre>${escape(report)}</pre></details></section>`);
 console.log(`${model}: ${result.width} × ${result.height}`);
}
const html=`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Window reference statecharts</title><style>
:root{color-scheme:light dark}body{margin:0;font-family:var(--font-sans,system-ui);color:var(--foreground,inherit)}nav{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 12px}button{font:inherit;font-size:13px;border:1px solid var(--border,#888);border-radius:var(--radius,8px);padding:8px 10px;color:var(--foreground,inherit);background:var(--secondary,transparent);cursor:pointer}button[aria-selected="true"]{border-color:var(--primary,#4b96ff);background:var(--accent,transparent)}p{line-height:1.5;font-size:14px;margin:12px 0}.canvas{height:560px;overflow:auto;border:1px solid var(--border,#888);border-radius:var(--radius,8px);background:var(--card,transparent);padding:16px}.canvas img{display:block;max-width:none}.tools{display:flex;gap:8px;align-items:center;font-size:13px;color:var(--muted-foreground,inherit);margin:10px 0}details{margin:14px 0}summary{cursor:pointer;font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 var(--font-mono,monospace);padding:16px;border-radius:var(--radius,8px);background:var(--code-background,transparent)}
</style></head><body><nav role="tablist" aria-label="State machines">${entries.map(([model,label],i)=>`<button role="tab" aria-controls="${model}" aria-selected="${i===0}" data-tab="${model}">${escape(label)}</button>`).join('')}</nav><div class="tools"><button id="minus" aria-label="Zoom out">−</button><span id="zoom">100%</span><button id="plus" aria-label="Zoom in">+</button><button id="reset">Fit width</button><span>Scroll the chart to follow the flow.</span></div>${sections.join('')}<script>
let zoom=100;const active=()=>document.querySelector('section:not([hidden]) img');function apply(){active().style.width=zoom+'%';document.getElementById('zoom').textContent=zoom+'%'}document.querySelectorAll('[data-tab]').forEach(button=>button.onclick=()=>{document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b===button)));document.querySelectorAll('section').forEach(s=>s.hidden=s.id!==button.dataset.tab);zoom=100;apply()});document.getElementById('plus').onclick=()=>{zoom=Math.min(250,zoom+25);apply()};document.getElementById('minus').onclick=()=>{zoom=Math.max(50,zoom-25);apply()};document.getElementById('reset').onclick=()=>{zoom=100;apply()};
</script></body></html>`;
fs.writeFileSync(path.join(root,'index.html'),html);
