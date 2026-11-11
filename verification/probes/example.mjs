// Run actual compiled Bend continuations; replace only external effects.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const compiled = fs.readFileSync(process.argv[2], 'utf8');
const suffix = 'cli(process.argv.slice(1));\nio_exit($main);';
assert.ok(compiled.includes(suffix), 'Bend output changed: review the probe adapter');
const source = compiled.replace(suffix, '');
for (const scenario of ['success', 'open-error', 'export-error']) {
  const context = vm.createContext({ scenario, events: [], process, performance, TextEncoder, TextDecoder, console });
  vm.runInContext(source, context);
  const actual = vm.runInContext(`(() => {
    const owner = { fixture: true };
    $0eff['Window.open'] = () => { events.push('open'); return scenario === 'open-error' ? { $: 'Fail', error: io_tup(5,'open') } : io_done(owner); };
    const exportKey = Object.keys($0eff).find(k => k.endsWith('WinRef.export'));
    $0eff[exportKey] = w => { if (w !== owner) throw Error('wrong owner'); events.push('export'); return io_tup(w, scenario === 'export-error' ? { $: 'Fail', error: io_tup(5,'export') } : io_done({ $: exportKey.replace('WinRef.export','X11WindowRef'), display: ':fixture', id: 7 })); };
    $0eff['Window.set_title'] = w => { if (w !== owner) throw Error('wrong owner'); events.push('rename'); return w; };
    $0eff['Window.close'] = w => { if (w !== owner) throw Error('wrong owner'); events.push('close'); return { $: 'Unit' }; };
    $0eff['IO.print'] = text => { events.push('print:' + text); return { $: 'Unit' }; };
    $0eff['IO.sleep'] = ms => { events.push('sleep:' + ms); return { $: 'Unit' }; };
    io_errs = message => events.push('halt:' + message);
    const status = io_run($main);
    return JSON.stringify({ scenario, status, events });
  })()`, context);
  const trace = JSON.parse(actual);
  const expected = {
    success: ['open','export','rename','print::fixture','print:7','sleep:3000','close'],
    'open-error': ['open','halt:open'],
    'export-error': ['open','export','rename','halt:export'],
  };
  assert.deepEqual(trace.events, expected[scenario], 'source/model trace mismatch');
  assert.equal(trace.status, scenario === 'success' ? 0 : 5);
  console.log(actual);
}
