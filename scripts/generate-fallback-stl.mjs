import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.join(rootDir, "exports", "stl");

await fs.mkdir(outputDir, { recursive: true });
await writeOrganic();
await writeVoronoi();

async function writeOrganic() {
  const mesh = buildLatheMesh({
    radialSegments: 128,
    heightSegments: 72,
    height: 160,
    yScale: 0.84,
    radiusAt(u, v) {
      const profile = Math.sin(v * Math.PI);
      const waist = 31 + profile * 34;
      const lip = 16 * v ** 4;
      const foot = 13 * (1 - v) ** 5;
      const growth =
        Math.sin(u * Math.PI * 2 * 5 + v * 8.5) * 3.4 +
        Math.sin(u * Math.PI * 2 * 9 - v * 15) * 1.7 +
        Math.cos(u * Math.PI * 2 * 2 + v * 5) * 2.2;
      const rib = (0.5 + 0.5 * Math.sin(u * Math.PI * 2 * 14 + v * 4)) ** 5 * 4.6;
      return waist + lip + foot + (growth + rib) * profile;
    },
    solidName: "organic_growth_vessel_fallback",
  });
  const target = path.join(outputDir, "organic-growth-vessel-fallback.stl");
  await fs.writeFile(target, mesh);
  console.log(`Wrote ${target}`);
}

async function writeVoronoi() {
  const mesh = buildLatheMesh({
    radialSegments: 132,
    heightSegments: 76,
    height: 150,
    yScale: 0.84,
    radiusAt(u, v) {
      const profile = Math.sin(v * Math.PI);
      const dome = 25 + profile * 48 + v ** 2.1 * 12;
      const macro = Math.sin(u * Math.PI * 2 * 4 + v * 9) * 2.8;
      const micro = Math.cos(u * Math.PI * 2 * 7 - v * 13) * 2.2;
      const rib = (0.5 + 0.5 * Math.sin(u * Math.PI * 2 * 16 + v * 6)) ** 4 * 4.0;
      return dome + (macro + micro + rib) * profile;
    },
    solidName: "voronoi_light_shell_fallback",
  });
  const target = path.join(outputDir, "voronoi-light-shell-fallback.stl");
  await fs.writeFile(target, mesh);
  console.log(`Wrote ${target}`);
}

function buildLatheMesh({ radialSegments, heightSegments, height, yScale, radiusAt, solidName }) {
  const vertices = [];
  const facets = [];

  for (let yIndex = 0; yIndex <= heightSegments; yIndex += 1) {
    const v = yIndex / heightSegments;
    const z = (v - 0.5) * height;
    for (let xIndex = 0; xIndex < radialSegments; xIndex += 1) {
      const u = xIndex / radialSegments;
      const angle = u * Math.PI * 2;
      const radius = radiusAt(u, v);
      vertices.push([Math.cos(angle) * radius, Math.sin(angle) * radius * yScale, z]);
    }
  }

  for (let yIndex = 0; yIndex < heightSegments; yIndex += 1) {
    for (let xIndex = 0; xIndex < radialSegments; xIndex += 1) {
      const a = yIndex * radialSegments + xIndex;
      const b = yIndex * radialSegments + ((xIndex + 1) % radialSegments);
      const c = (yIndex + 1) * radialSegments + ((xIndex + 1) % radialSegments);
      const d = (yIndex + 1) * radialSegments + xIndex;
      facets.push([vertices[a], vertices[b], vertices[c]]);
      facets.push([vertices[a], vertices[c], vertices[d]]);
    }
  }

  const bottom = [0, 0, -height / 2];
  const top = [0, 0, height / 2];
  for (let xIndex = 0; xIndex < radialSegments; xIndex += 1) {
    const next = (xIndex + 1) % radialSegments;
    facets.push([bottom, vertices[next], vertices[xIndex]]);
    const topA = heightSegments * radialSegments + xIndex;
    const topB = heightSegments * radialSegments + next;
    facets.push([top, vertices[topA], vertices[topB]]);
  }

  return [
    `solid ${solidName}`,
    ...facets.map(formatFacet),
    `endsolid ${solidName}`,
    "",
  ].join("\n");
}

function formatFacet(points) {
  const normal = computeNormal(points);
  return [
    `  facet normal ${format(normal[0])} ${format(normal[1])} ${format(normal[2])}`,
    "    outer loop",
    ...points.map((point) => `      vertex ${format(point[0])} ${format(point[1])} ${format(point[2])}`),
    "    endloop",
    "  endfacet",
  ].join("\n");
}

function computeNormal([a, b, c]) {
  const ux = b[0] - a[0];
  const uy = b[1] - a[1];
  const uz = b[2] - a[2];
  const vx = c[0] - a[0];
  const vy = c[1] - a[1];
  const vz = c[2] - a[2];
  const nx = uy * vz - uz * vy;
  const ny = uz * vx - ux * vz;
  const nz = ux * vy - uy * vx;
  const length = Math.hypot(nx, ny, nz) || 1;
  return [nx / length, ny / length, nz / length];
}

function format(value) {
  return Number.isFinite(value) ? value.toFixed(6) : "0.000000";
}
