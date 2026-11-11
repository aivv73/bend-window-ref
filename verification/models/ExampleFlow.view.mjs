export const title = 'Export a window reference';
export const state = v => ({
  start: 'Start', open: 'Window open',
  exported: v.result === 'Done' ? 'Reference exported' : 'Export failed; owner returned',
  renamed: v.result === 'Done' ? 'Window renamed' : 'Renamed after export failure',
  displayPrinted: 'Display printed', reported: 'Reference printed', slept: 'Three seconds elapsed',
  closed: 'Window explicitly closed', openFailed: 'Could not open window', exportFailed: 'Exited without explicit close',
})[v.phase];
export const step = (action, from, to) => ({
  Open: 'open window', OpenFails: 'opening fails', Export: to.result === 'Done' ? 'export succeeds' : 'export fails',
  Rename: 'rename returned window', PrintDisplay: 'print display', PrintId: 'print ID', ReportFailure: 'report error and exit',
  Sleep: 'wait three seconds', Close: 'close window', Finished: 'finished',
})[action];
export const group = v => v.phase === 'exportFailed' ? 'error' : v.phase === 'closed' ? 'success' : 'active';
export const colors = { error: 'pink', success: 'teal', active: 'blue' };
