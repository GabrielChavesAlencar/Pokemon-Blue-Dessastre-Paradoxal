import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import path from 'node:path';
export async function extractSprites(root,output){
  const compressed=await readFile(path.join(root,'assets/fan-pokemon.tar.gz'));
  const expected=(await readFile(path.join(root,'assets/fan-pokemon.sha256'),'utf8')).trim();
  if(createHash('sha256').update(compressed).digest('hex')!==expected)throw new Error('O pacote de sprites não corresponde ao checksum.');
  const archive=gunzipSync(compressed,{maxOutputLength:64*1024*1024});
  let offset=0,count=0;const seen=new Set();
  while(offset+512<=archive.length){
    const header=archive.subarray(offset,offset+512);if(header.every(x=>x===0))break;
    const str=(start,end)=>header.subarray(start,end).toString('utf8').split('\0')[0];
    const name=str(0,100),size=parseInt(str(124,136).trim(),8),type=str(156,157);
    if(!/^[A-Z][A-Z0-9_]*\/(?:front|front-shiny|back|back-shiny|icon|icon-shiny|footprint)\.png$/.test(name)||!['0',''].includes(type)||!Number.isSafeInteger(size)||size<0||size>2000000||seen.has(name))throw new Error('Entrada inválida no pacote de sprites.');
    const checksum=parseInt(str(148,156).trim(),8);let sum=0;for(let i=0;i<512;i++)sum+=(i>=148&&i<156)?32:header[i];
    if(sum!==checksum||offset+512+size>archive.length)throw new Error('Pacote de sprites corrompido.');
    const target=path.join(output,'assets/fan-pokemon',name);await mkdir(path.dirname(target),{recursive:true});await writeFile(target,archive.subarray(offset+512,offset+512+size));
    seen.add(name);count++;offset+=512+Math.ceil(size/512)*512;
  }
  return count;
}
