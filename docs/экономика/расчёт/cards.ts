import { readFileSync, writeFileSync } from 'node:fs';
import { buildModel } from '/home/claude/arvello-site/src/core/builders/index.ts';
import { techcard } from '/home/claude/arvello-site/src/core/techcard.ts';
const raw = JSON.parse(readFileSync('/home/claude/arvello-site/data/catalog/models.json', 'utf8'));
const models = Array.isArray(raw) ? raw : raw.models;
const out: unknown[] = [];
for (const m of models) {
  const opts: Record<string, string> = {};
  for (const o of m.options ?? []) if (o.values?.length) opts[o.key] = o.values[0].key;
  try {
    const g = buildModel(m.sku, opts);
    const xs = g.parts.flatMap((p: any) => [p.x0, p.x1]), ys = g.parts.flatMap((p: any) => [p.y0, p.y1]), zs = g.parts.flatMap((p: any) => [p.z0, p.z1]);
    const size = [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys), Math.max(...zs) - Math.min(...zs)].map(Math.round);
    out.push({ sku: m.sku, name: m.name?.ru ?? m.name, category: m.category, opts, size, card: techcard(g, { category: m.category }), nparts: g.parts.length });
  } catch (e) { out.push({ sku: m.sku, error: String(e) }); }
}
writeFileSync('/home/claude/work/cards.json', JSON.stringify(out));
console.log(out.length, out.filter((x: any) => x.error).map((x: any) => x.sku + ' ' + x.error));
