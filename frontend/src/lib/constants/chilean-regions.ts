export const CHILEAN_REGIONS = [
  "Región Metropolitana",
  "Valparaíso",
  "Biobío",
  "Maule",
  "La Araucanía",
  "Los Lagos",
  "O'Higgins",
  "Antofagasta",
  "Los Ríos",
  "Atacama",
  "Coquimbo",
  "Arica y Parinacota",
  "Tarapacá",
  "Aysén",
  "Magallanes",
  "Ñuble",
] as const;

export type ChileanRegion = (typeof CHILEAN_REGIONS)[number];
