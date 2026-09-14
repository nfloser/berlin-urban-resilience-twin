import type { FeatureCollection } from 'geojson'
import type { Facility, NetworkStatus, RouteResponse } from './types'

export type StatusCard = { label: string; value: string; detail: string }

export function networkStatusToCards(status: NetworkStatus, reachableFacilities: number): StatusCard[] {
  return [
    {
      label: 'Network',
      value: `${status.active_segments}/${status.baseline_segments}`,
      detail: 'active road segments'
    },
    {
      label: 'Disconnection',
      value: `${status.disconnected_percentage.toFixed(1)}%`,
      detail: 'segments removed by scenario'
    },
    {
      label: 'Facilities',
      value: String(reachableFacilities),
      detail: 'loaded critical facilities'
    },
    {
      label: 'Data mode',
      value: status.data_mode,
      detail: status.active_scenario_id ? `scenario: ${status.active_scenario_id}` : 'baseline'
    }
  ]
}

export function facilitiesToGeoJson(facilities: Facility[]): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: facilities.map((facility) => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [facility.coordinate.longitude, facility.coordinate.latitude]
      },
      properties: {
        id: facility.id,
        name: facility.name,
        facilityType: facility.facility_type,
        districtId: facility.district_id
      }
    }))
  }
}

export function routeToGeoJson(route: RouteResponse | null): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: route
      ? [
          {
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: route.geometry },
            properties: { affectedSegments: route.affected_segment_ids.length }
          }
        ]
      : []
  }
}
