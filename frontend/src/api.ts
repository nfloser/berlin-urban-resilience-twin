import type { FeatureCollection, LineString } from 'geojson'
import type { Coordinate, Facility, NetworkStatus, RouteMode, RouteResponse } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) }
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${response.status}: ${text}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  status: () => json<NetworkStatus>('/network/status'),
  facilities: () => json<Facility[]>('/facilities'),
  networkSegments: () =>
    json<FeatureCollection<LineString, { segment_id: string; affected: boolean }>>(
      '/network/segments'
    ),
  freshness: () => json<Record<string, unknown>>('/data/freshness'),
  route: (
    origin: Coordinate,
    destination: Coordinate,
    mode: RouteMode,
    preferences: { disruption_weight: number; pollution_weight: number; reliability_weight: number }
  ) =>
    json<RouteResponse>('/route', {
      method: 'POST',
      body: JSON.stringify({ origin, destination, mode, preferences })
    }),
  scenario: (segmentId: string) =>
    json<{ id: string; active: boolean }>('/scenario', {
      method: 'POST',
      body: JSON.stringify({
        id: `closure-${segmentId}`,
        name: `Road closure: ${segmentId}`,
        description: 'User-created scenario overlay; base network remains unchanged.',
        disruptions: [
          {
            id: `closure-${segmentId}-event`,
            kind: 'road_closure',
            affected_segment_ids: [segmentId]
          }
        ]
      })
    })
}
