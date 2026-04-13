import type { CityWithoutLocation } from "./city.types"

export interface PredictData {
  status: string
  predicted_delay_minutes_raw: number
  predicted_delay_minutes: number
  model_name: string
  decision_threshold_minutes: number
  prediction_rule: string
  origin: CityWithoutLocation
  destination: CityWithoutLocation
  scheduled_departure: string
  estimated_arrival_for_weather: string
  estimated_duration_minutes: number
  estimated_duration_source: string
  route_history_observations: number
  origin_weather_timestamp: string
  destination_weather_timestamp: string
  assumption: string
}

export interface PredictProps {
  dataPredict: PredictData;
  onclick: () => void;
}

