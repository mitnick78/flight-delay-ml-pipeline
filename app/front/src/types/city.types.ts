interface City {
  id_city: string
  name_city: string
  longitude: number
  latitude: number
}

export type CityWithoutLocation = Omit<City, 'longitude' | 'latitude'>