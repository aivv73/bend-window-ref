export const title = 'Observe an exported reference';
export const state = v => ({
 readDisplay:'Wait for display line',readId:'Wait for ID line',connect:'Read reference',blocked:'Waiting without a deadline',
 fetchName:'Inspect window',checkName:'Inspect window',freeName:'Inspect window',freeNameOnError:'Release resources after lookup failure',
 geometry:'Inspect window',closeDisplay:'Geometry checked',closeDisplayOnError:'Release resources after lookup failure',
 wait:'Observer disconnected',stopChild:'Stop and reap producer',reap:'Stop and reap producer',finished:'Resources released',
})[v.phase];
export const step = (action,from,to) => ({
 ReadDisplay:'display arrives',ReadId:'ID arrives',Silence:'producer stops sending output',ParseFails:'reading or parsing fails',
 Connect:'connect to display',ConnectFails:'connection fails',FetchName:'fetch title',FetchFails:'lookup fails',
 CheckName:to.phase === 'freeName' ? 'title matches' : 'lookup fails',FreeName:'free title memory',
 Geometry:to.phase === 'closeDisplay' ? 'geometry matches' : 'lookup fails',CloseDisplay:'close observer connection',
 Wait:'producer exits',WaitTimeout:'exit deadline expires',Kill:'kill producer',Reap:'reap producer',Finished:'finished',Blocked:'still waiting',
})[action];
export const group = v => v.phase === 'blocked' ? 'error' : v.phase === 'finished' ? 'success' : 'active';
export const colors = { error:'pink',success:'teal',active:'blue' };
