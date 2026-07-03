export const COMUNAS_RM = [
  "Santiago",
  "Providencia",
  "Las Condes",
  "Ñuñoa",
  "La Florida",
  "Maipú",
  "Pudahuel",
  "Quilicura",
  "Recoleta",
  "Independencia",
  "San Miguel",
  "La Cisterna",
  "Peñalolén",
  "Macul",
  "Vitacura",
] as const;

export type ComunaRM = (typeof COMUNAS_RM)[number];
