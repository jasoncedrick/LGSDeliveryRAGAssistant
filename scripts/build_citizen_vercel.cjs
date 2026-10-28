// Vercel Build Output API v3: publish only citizen assets and verified source PDFs.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const origin=(process.env.PUBLIC_RAG_API_ORIGIN||'').trim();
const parsed=new URL(origin); // Fail the build if no backend was explicitly selected.
if(parsed.protocol!=='https:'||parsed.username||parsed.password||parsed.origin!==origin)
  throw Error('PUBLIC_RAG_API_ORIGIN must be an HTTPS origin without credentials, path or trailing slash');
const qaOutput=process.env.WEBSITE_BUILD_QA_OUTPUT;
const output=qaOutput?path.resolve(qaOutput):path.join(root,'.vercel','output');
// QA writes only beneath ignored tmp; production builds retain their fixed path.
// Check the resolved absolute target before removing any generated directory.
if(qaOutput){
  const relative=path.relative(path.join(root,'tmp'),output);
  if(!relative||relative==='..'||relative.startsWith('..'+path.sep)||path.isAbsolute(relative))throw Error('QA build output must be beneath project tmp');
}else if(path.dirname(output)!==path.join(root,'.vercel'))throw Error('Invalid build path');
fs.rmSync(output,{recursive:true,force:true});
const site=path.join(output,'static'),assets=path.join(site,'assets');
fs.mkdirSync(assets,{recursive:true});
const files=['styles.css','motion.css','app.js','motion.js','mark.svg','THIRD_PARTY.md'];
for(const name of files)fs.copyFileSync(path.join(root,'website',name),path.join(assets,name));
fs.cpSync(path.join(root,'website/vendor'),path.join(assets,'vendor'),{recursive:true});
fs.copyFileSync(path.join(root,'website/index.html'),path.join(site,'index.html'));
fs.writeFileSync(path.join(assets,'runtime-config.js'),
  'window.EBOSS_CONFIG = Object.freeze('+JSON.stringify({apiOrigin:origin,sourceCatalog:'/sources/catalog.json'})+');\n');
fs.mkdirSync(path.join(site,'sources'));
const sources=JSON.parse(fs.readFileSync(path.join(root,'config/website_sources.json'),'utf8'));
const catalog=[];
for(const source of sources){
  if(!/^[a-z]+$/.test(source.id)||path.basename(source.filename)!==source.filename)throw Error('Invalid source identity');
  const bytes=fs.readFileSync(path.join(root,'data/raw_charters',source.filename));
  if(crypto.createHash('sha256').update(bytes).digest('hex')!==source.sha256)throw Error('Source PDF hash changed: '+source.id);
  fs.writeFileSync(path.join(site,'sources',source.id+'.pdf'),bytes);
  catalog.push({id:source.id,office:source.office,filename:source.filename,url:'/sources/'+source.id+'.pdf'});
}
fs.writeFileSync(path.join(site,'sources/catalog.json'),JSON.stringify(catalog));
const csp=`default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' ${origin}; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'`;
fs.writeFileSync(path.join(output,'config.json'),JSON.stringify({version:3,routes:[
  {src:'/(.*)',headers:{'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':csp},continue:true},
  {src:'/assets/runtime-config.js',headers:{'Cache-Control':'no-store'},continue:true},
  {handle:'filesystem'}
]},null,2));
console.log(`Built static citizen site with ${sources.length} verified PDFs. Backend: ${origin}`);
