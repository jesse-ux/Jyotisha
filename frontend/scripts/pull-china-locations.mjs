import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SOURCE_URL = "https://raw.githubusercontent.com/zhChuXiao/ChinaGeoJson/master/info.json";
const outputPath = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../src/data/china-locations.json",
);

const response = await fetch(SOURCE_URL, {
  headers: { "user-agent": "Jyotisha location-data refresh" },
});

if (!response.ok) {
  throw new Error(`Unable to download China location data: ${response.status} ${response.statusText}`);
}

const source = await response.json();

function childrenOf(code) {
  const record = source[String(code)];
  return Array.isArray(record?.children) ? record.children : [];
}

function toLocation(node) {
  const [longitude, latitude] = Array.isArray(node.center) ? node.center : [];
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    throw new Error(`Missing valid coordinates for ${node.name} (${node.adcode})`);
  }

  return {
    code: String(node.adcode),
    name: node.name,
    center: [longitude, latitude],
  };
}

function toCity(node) {
  const location = toLocation(node);
  return {
    ...location,
    districts: childrenOf(node.adcode).map(toLocation),
  };
}

function toProvince(node) {
  const location = toLocation(node);
  const directChildren = childrenOf(node.adcode);
  const directDistricts = directChildren.filter((child) => child.level === "district");

  // Direct-administered municipalities, Hong Kong and Macao have districts
  // directly below the province-level node. A virtual city keeps the UI's
  // country → province → city → district sequence consistent.
  if (directChildren.length === directDistricts.length) {
    return {
      ...location,
      cities: [{
        code: `${node.adcode}-city`,
        name: node.name,
        center: location.center,
        districts: directDistricts.map(toLocation),
      }],
    };
  }

  return {
    ...location,
    cities: directChildren.map(toCity),
  };
}

const countryChildren = childrenOf(100000).filter((node) => node.level === "province");
const output = {
  source: {
    name: "ChinaGeoJson / DataV.GeoAtlas",
    url: SOURCE_URL,
    license: "MIT",
    generatedAt: new Date().toISOString(),
  },
  country: {
    code: "CN",
    name: "中国",
    timezone: 8,
    provinces: countryChildren.map(toProvince),
  },
};

await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, `${JSON.stringify(output)}\n`, "utf8");

const cityCount = output.country.provinces.reduce((total, province) => total + province.cities.length, 0);
const districtCount = output.country.provinces.reduce(
  (total, province) => total + province.cities.reduce((sum, city) => sum + city.districts.length, 0),
  0,
);
console.log(`Wrote ${outputPath}: ${output.country.provinces.length} provinces, ${cityCount} cities, ${districtCount} districts.`);
