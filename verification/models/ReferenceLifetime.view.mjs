export const title = 'A reference outlives its window';
export const state = v => ({ owned:'Window open', exported:'Reference points to original window', copied:'Both copies point to original window', expired:'Unchanged reference points to no window', reused:'Unchanged reference points to another window' })[v.phase];
export const step = action => ({ Export:'export reference', Copy:'copy reference', Close:'owner closes window', Reuse:'X11 reuses the ID', Finished:'finished' })[action];
export const group = v => ['expired','reused'].includes(v.phase) ? 'expired' : 'live';
export const colors = { expired:'orange', live:'teal' };
