import { readFile } from 'node:fs/promises';
import openapiTS, { astToString } from 'openapi-typescript';

const sourceUrl = new URL('../../docs/openapi.yaml', import.meta.url);
const generatedUrl = new URL('../src/api/generated/openapi.ts', import.meta.url);
const expected = astToString(await openapiTS(sourceUrl));
const actual = await readFile(generatedUrl, 'utf8').catch(() => '');
const comparableActual = actual.replace(/^\/\*\*[\s\S]*?\*\/\s*/, '');

if (comparableActual !== expected) {
  process.stderr.write(
    'Tipos OpenAPI desatualizados. Execute `npm run openapi:generate` e versione o resultado.\n'
  );
  process.exitCode = 1;
}
