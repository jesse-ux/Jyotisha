import source from "./china-locations.json";

export type LocationNode = {
  code: string;
  name: string;
  center: [longitude: number, latitude: number];
};

export type CityNode = LocationNode & {
  districts: LocationNode[];
};

export type ProvinceNode = LocationNode & {
  cities: CityNode[];
};

export type ChinaLocationData = {
  source: {
    name: string;
    url: string;
    license: string;
    generatedAt: string;
  };
  country: {
    code: "CN";
    name: string;
    timezone: number;
    provinces: ProvinceNode[];
  };
};

export const chinaLocations = source as ChinaLocationData;
