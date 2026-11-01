import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import path from 'node:path';

export async function extractExtras(root,output){
  const compressed=await readFile(path.join(root,'assets/fan-extras.tar.gz'));
  const manifest=JSON.parse(await readFile(path.join(root,'assets/fan-extras.manifest.json'),'utf8'));
  const expected=(await readFile(path.join(root,'assets/fan-extras.sha256'),'utf8')).trim();
  const sha=data=>createHash('sha256').update(data).digest('hex');
  if(sha(compressed)!==expected||expected!==manifest.archiveSha256)throw new Error('Pacote de cries e pedras corrompido.');
  const wanted=new Map(manifest.files.map(e=>[e.path,e]));
  const archive=gunzipSync(compressed,{maxOutputLength:32*1024*1024});
  const seen=new Set();let offset=0;
  while(offset+512<=archive.length){
    const header=archive.subarray(offset,offset+512);if(header.every(x=>x===0))break;
    const str=(start,end)=>header.subarray(start,end).toString('utf8').split('\0')[0];
    const name=str(0,100),size=parseInt(str(124,136).trim(),8),type=str(156,157);
    if(!/^(?:cries\/[A-Z0-9_]+\.wav|items\/DP[A-Z0-9_]+\.png)$/.test(name)||!wanted.has(name)||seen.has(name)||!['','0'].includes(type)||!Number.isSafeInteger(size)||size<0||size>2000000)throw new Error('Asset autoral inválido.');
    let sum=0;for(let i=0;i<512;i++)sum+=(i>=148&&i<156)?32:header[i];
    if(sum!==parseInt(str(148,156).trim(),8)||offset+512+size>archive.length)throw new Error('Arquivo autoral truncado.');
    const data=archive.subarray(offset+512,offset+512+size);
    if(sha(data)!==wanted.get(name).sha256)throw new Error('Hash incorreto: '+name);
    const target=path.join(output,'assets/fan-extras',name);
    await mkdir(path.dirname(target),{recursive:true});await writeFile(target,data);
    seen.add(name);offset+=512+Math.ceil(size/512)*512;
  }
  if(seen.size!==wanted.size)throw new Error('Pacote autoral incompleto.');
  return seen.size;
}
