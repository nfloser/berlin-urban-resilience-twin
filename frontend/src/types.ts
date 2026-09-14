export type Coordinate = { latitude: number; longitude: number }

export type Facility = {
  id: string
  name: string
  facility_type: 'hospital' | 'fire_station' | 'emergency_service' | 'shelter'
  coordinate: Coordinate
  district_id: string
  connected_node_id: string
  source_uri?: string | null
}

export type NetworkStatus = {
  data_mode: string
  nodes: number
  baseline_segments: number
  active_segments: number
  disconnected_percentage: number
  active_scenario_id: string | null
  generated_at: string
}

export type RouteMode = 'fastest' | 'most_reliable' | 'lowest_exposure' | 'disruption_avoiding'

export type RouteResponse = {
  path_node_ids: string[]
  segment_ids: string[]
  geometry: number[][]
  distance_m: number
  travel_time_s: number
  generalized_cost: number
  affected_segment_ids: string[]
  pollution_exposure: number
  mean_reliability: number
  explanation: string
}
