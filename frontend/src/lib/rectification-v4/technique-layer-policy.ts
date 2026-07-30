import type { EvidenceDomain } from "./contracts.ts";
import { domainScorerRegistry } from "./domain-scorers.ts";

export type MissingTechniqueLayerClassification = Readonly<{
  required: readonly string[];
  optional: readonly string[];
  referenceOnly: readonly string[];
  unclassified: readonly string[];
}>;

const aliases: Readonly<Record<string, string>> = {
  Vimshottari_MD_AD_PD: "vimshottari",
  Narayana_MD_AD: "narayana",
};
const optionalLayers = new Set(["KP_cusps", "A7", "Ashtakavarga", "Shadbala"]);
const referenceOnlyLayers = new Set(["D60"]);
const knownDomainLayers = new Set(
  Object.values(domainScorerRegistry).flatMap((policy) => policy.techniqueLayers),
);

export function classifyMissingTechniqueLayers(
  missingLayers: readonly string[],
  activeScoreableDomains: readonly EvidenceDomain[],
): MissingTechniqueLayerClassification {
  const requiredLayers = new Set(
    activeScoreableDomains.flatMap((domain) => domainScorerRegistry[domain].techniqueLayers),
  );
  const classified = {
    required: [] as string[],
    optional: [] as string[],
    referenceOnly: [] as string[],
    unclassified: [] as string[],
  };

  for (const layer of [...new Set(missingLayers)]) {
    const canonical = aliases[layer] ?? layer;
    if (referenceOnlyLayers.has(canonical)) classified.referenceOnly.push(layer);
    else if (requiredLayers.has(canonical)) classified.required.push(layer);
    else if (optionalLayers.has(canonical) || knownDomainLayers.has(canonical)) classified.optional.push(layer);
    else classified.unclassified.push(layer);
  }
  return classified;
}
