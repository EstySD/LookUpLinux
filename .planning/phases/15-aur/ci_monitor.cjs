// Local adapter because the installed github-workflows skill omits its helper.
const {spawnSync}=require('node:child_process');
const [command,...args]=process.argv.slice(2);
if(!command||command==='--help'){
  console.log('runs [gh run list args] | watch <id> [args] | log-failed <id> | view <id> [args]');process.exit(0);
}
const commands={runs:['run','list'],watch:['run','watch'],view:['run','view'],'log-failed':['run','view',...args,'--log-failed']};
if(!commands[command])throw Error('Unknown monitor command');
const argv=command==='log-failed'?commands[command]:[...commands[command],...args];
const result=spawnSync('gh',argv,{stdio:'inherit',windowsHide:true});
process.exit(result.status??1);
