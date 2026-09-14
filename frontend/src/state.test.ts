import { describe, expect, it } from 'vitest'
import { facilitiesToGeoJson, networkStatusToCards, routeToGeoJson } from './state'


describe('frontend state transformations', () => {
  it('turns backend facilities into map features', () => {
    const collection = facilitiesToGeoJson([
      {
        id: 'h1',
        name: 'Hospital',
        facility_type: 'hospital',
        coordinate: { latitude: 52.52, longitude: 13.4 },
        district_id: 'mitte',
        connected_node_id: 'n1'
      }
    ])
    expect(collection.features[0].geometry).toEqual({ type: 'Point', coordinates: [13.4, 52.52] })
  })

  it('represents route geometry without inventing coordinates', () => {
    const collection = routeToGeoJson({
      path_node_ids: ['a', 'b'],
      segment_ids: ['ab'],
      geometry: [[13.4, 52.52], [13.41, 52.53]],
      distance_m: 100,
      travel_time_s: 20,
      generalized_cost: 20,
      affected_segment_ids: [],
      pollution_exposure: 0,
      mean_reliability: 1,
      explanation: 'fastest'
    })
    expect(collection.features[0].geometry).toEqual({
      type: 'LineString',
      coordinates: [[13.4, 52.52], [13.41, 52.53]]
    })
  })

  it('keeps data provenance visible in status cards', () => {
    const cards = networkStatusToCards({
      data_mode: 'osm-snapshot',
      nodes: 100,
      baseline_segments: 120,
      active_segments: 118,
      disconnected_percentage: 1.666,
      active_scenario_id: 'rain',
      generated_at: '2026-09-14T10:00:00Z'
    }, 4)
    expect(cards.find((card) => card.label === 'Data mode')?.value).toBe('osm-snapshot')
  })
})
