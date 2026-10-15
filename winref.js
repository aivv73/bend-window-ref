// SPDX-License-Identifier: Apache-2.0
function winref_export(window) {
  const code = typeof process !== "undefined" && process.platform === "darwin" ? 45 : 95;
  const text = "WinRef.export: external reference is unavailable on this backend";
  return io_tup(window, { $: CID(Fail), error: io_tup(code, text) });
}

io_eff(CID(WinRef.export), winref_export);
