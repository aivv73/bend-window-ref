export const title = 'Export preserves the owner';
export const state = v => v.phase === 'ready' ? 'Window owned by caller' : v.result === 'Done' ? 'Owner returned with synchronized reference' : 'Owner returned with ' + v.result;
export const step = (action,from,to) => action === 'Finished' ? 'finished' : to.result === 'Done' ? 'export reference' : 'export fails';
export const group = v => v.phase === 'ready' ? 'active' : v.result === 'Done' ? 'success' : 'failure';
export const colors = { active:'blue',success:'teal',failure:'orange' };
