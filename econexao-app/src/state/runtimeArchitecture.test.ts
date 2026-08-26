import fs from 'node:fs';
import path from 'node:path';

function runtimeFiles(directory: string): string[] {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) return runtimeFiles(full);
    if (!/\.(ts|tsx)$/.test(entry.name) || /\.(test|spec|stories)\./.test(entry.name)) return [];
    return [full];
  });
}

describe('runtime architecture', () => {
  it('não importa mockData em código de produção', () => {
    const roots = [path.resolve('app'), path.resolve('src')];
    const violations = roots.flatMap(runtimeFiles).filter((file) => {
      if (file.endsWith(path.join('data', 'mockData.ts'))) return false;
      return /(?:from\s+|require\(|import\s*(?:\(|["']))["']?[^"']*mockData/.test(
        fs.readFileSync(file, 'utf8')
      );
    });
    expect(violations).toEqual([]);
  });

  it('mantém uma allowlist explícita das propriedades de AppState', () => {
    const source = fs.readFileSync(path.resolve('src/state/appReducer.ts'), 'utf8');
    const body = source.match(/export interface AppState\s*{([\s\S]*?)}/)?.[1] ?? '';
    const properties = [...body.matchAll(/^\s*(\w+)\??:/gm)].map((match) => match[1]).sort();
    expect(properties).toEqual(['accessibility', 'activeRegionId', 'featureFlags']);
  });

  it('não possui fallbacks silenciosos para MOCK em requisições de produção', () => {
    const apiAndHooksFiles = [
      path.resolve('src/api/client.ts'),
      path.resolve('src/hooks/queries.ts'),
    ];
    apiAndHooksFiles.forEach((file) => {
      const content = fs.readFileSync(file, 'utf8');
      expect(content).not.toMatch(/MOCK_/);
      expect(content).not.toMatch(/mockData/);
    });
  });
});
