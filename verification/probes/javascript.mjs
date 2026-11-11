import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
// CID is a Bend compiler macro; replace its two names exactly as the compiler does.
const source = fs.readFileSync(process.argv[2], 'utf8').replaceAll('CID(Fail)', '"Fail"').replaceAll('CID(WinRef.export)', '"WinRef.export"');
for (const platform of ['linux','darwin','browser']) {
  const handlers = {};
  const context = { io_tup: (...xs) => xs, io_eff: (name, fn) => handlers[name] = fn };
  if (platform !== 'browser') context.process = { platform };
  vm.runInNewContext(source, context);
  const owner = {};
  const [returned, result] = handlers['WinRef.export'](owner);
  assert.equal(returned, owner);
  assert.equal(result.$, 'Fail');
  assert.equal(result.error[0], platform === 'darwin' ? 45 : 95);
}
console.log('javascript: same owner and ENOTSUP on Linux, macOS, and browser');
