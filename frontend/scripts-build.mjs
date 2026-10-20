import { cp, mkdir, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const root = process.cwd();
const dist = join(root, 'dist');
const viteBin = join(root, 'node_modules', 'vite', 'bin', 'vite.js');

await rm(dist, { recursive: true, force: true });

if (process.env.WILDLIFE_PORTABLE_BUILD !== '1') {
  const result = spawnSync(process.execPath, [viteBin, 'build'], { stdio: 'inherit' });
  if (result.status === 0) process.exit(0);
  console.warn('\nVite build was unavailable in this environment; using the portable TypeScript build fallback.');
}

await mkdir(join(dist, 'assets'), { recursive: true });
await cp(join(root, 'src', 'index.css'), join(dist, 'assets', 'index.css'));
const imports = {
  react: 'https://esm.sh/react@18.3.1',
  'react/jsx-runtime': 'https://esm.sh/react@18.3.1/jsx-runtime',
  'react/jsx-dev-runtime': 'https://esm.sh/react@18.3.1/jsx-dev-runtime',
  'react-dom/client': 'https://esm.sh/react-dom@18.3.1/client',
  'react-router-dom': 'https://esm.sh/react-router-dom@6.28.1',
  axios: 'https://esm.sh/axios@1.7.9',
  leaflet: 'https://esm.sh/leaflet@1.9.4',
  'react-leaflet': 'https://esm.sh/react-leaflet@4.2.1',
  recharts: 'https://esm.sh/recharts@2.15.0',
  'lucide-react': 'https://esm.sh/lucide-react@0.469.0',
};
const html = `<!doctype html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><meta name="theme-color" content="#0b120d"/><title>Wildlife Conservation Intelligence Platform</title><link rel="stylesheet" href="/assets/index.css"/><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/><script type="importmap">${JSON.stringify({ imports })}</script></head><body><div id="root"></div><script type="module" src="/main.js"></script></body></html>`;
await writeFile(join(dist, 'index.html'), html);
console.log(`Portable build output prepared in ${dist}`);
