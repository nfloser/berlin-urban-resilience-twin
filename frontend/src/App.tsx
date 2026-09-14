import { useEffect, useRef, useState } from 'react'
import maplibregl, { GeoJSONSource, Map } from 'maplibre-gl'
import type { MapLayerMouseEvent, MapMouseEvent } from 'maplibre-gl'
import type { FeatureCollection, LineString } from 'geojson'
import 'maplibre-gl/dist/maplibre-gl.css'
import { api } from './api'
import { facilitiesToGeoJson, networkStatusToCards, routeToGeoJson } from './state'
import type { Coordinate, Facility, NetworkStatus, RouteMode, RouteResponse } from './types'
import './styles.css'

const berlinCenter: [number, number] = [13.405, 52.52]

function App() {
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<Map | null>(null)
  const facilitiesRef = useRef<Facility[]>([])
  const originRef = useRef<Coordinate | null>(null)
  const destinationRef = useRef<Coordinate | null>(null)
  const [status, setStatus] = useState<NetworkStatus | null>(null)
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [networkSegments, setNetworkSegments] = useState<
    FeatureCollection<LineString, { segment_id: string; affected: boolean }>
  >({ type: 'FeatureCollection', features: [] })
  const [origin, setOrigin] = useState<Coordinate | null>(null)
  const [destination, setDestination] = useState<Coordinate | null>(null)
  const [route, setRoute] = useState<RouteResponse | null>(null)
  const [mode, setMode] = useState<RouteMode>('fastest')
  const [segmentId, setSegmentId] = useState('BC')
  const [disruptionWeight, setDisruptionWeight] = useState(1)
  const [pollutionWeight, setPollutionWeight] = useState(0)
  const [reliabilityWeight, setReliabilityWeight] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Facility | null>(null)

  async function refresh() {
    const [nextStatus, nextFacilities, nextNetwork] = await Promise.all([
      api.status(),
      api.facilities(),
      api.networkSegments()
    ])
    setStatus(nextStatus)
    setFacilities(nextFacilities)
    setNetworkSegments(nextNetwork)
  }

  useEffect(() => {
    refresh().catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: mapContainer.current,
      center: berlinCenter,
      zoom: 12,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors'
          }
        },
        layers: [{ id: 'osm', type: 'raster', source: 'osm' }]
      }
    })
    map.addControl(new maplibregl.NavigationControl(), 'bottom-right')
    map.on('load', () => {
      map.addSource('network', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      })
      map.addLayer({
        id: 'network',
        type: 'line',
        source: 'network',
        paint: {
          'line-color': ['case', ['boolean', ['get', 'affected'], false], '#ff5f6d', '#64748b'],
          'line-width': ['case', ['boolean', ['get', 'affected'], false], 5, 2],
          'line-opacity': 0.78
        }
      })
      map.addSource('facilities', { type: 'geojson', data: facilitiesToGeoJson([]) })
      map.addLayer({
        id: 'facilities',
        type: 'circle',
        source: 'facilities',
        paint: {
          'circle-radius': 8,
          'circle-color': ['match', ['get', 'facilityType'], 'hospital', '#ff5f6d', 'fire_station', '#ffb347', '#6ee7b7'],
          'circle-stroke-color': '#0b1220',
          'circle-stroke-width': 2
        }
      })
      map.addSource('route', { type: 'geojson', data: routeToGeoJson(null) })
      map.addLayer({
        id: 'route',
        type: 'line',
        source: 'route',
        paint: { 'line-color': '#38bdf8', 'line-width': 6, 'line-opacity': 0.9 }
      })
      map.on('click', 'facilities', (event: MapLayerMouseEvent) => {
        const id = String(event.features?.[0]?.properties?.id ?? '')
        setSelected(facilitiesRef.current.find((item) => item.id === id) ?? null)
      })
    })
    map.on('click', (event: MapMouseEvent) => {
      if (map.queryRenderedFeatures(event.point, { layers: ['facilities'] }).length > 0) return
      const coordinate = { latitude: event.lngLat.lat, longitude: event.lngLat.lng }
      if (!originRef.current || (originRef.current && destinationRef.current)) {
        originRef.current = coordinate
        destinationRef.current = null
        setOrigin(coordinate)
        setDestination(null)
        setRoute(null)
      } else {
        destinationRef.current = coordinate
        setDestination(coordinate)
      }
    })
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const source = mapRef.current?.getSource('network') as GeoJSONSource | undefined
    source?.setData(networkSegments)
  }, [networkSegments])

  useEffect(() => {
    facilitiesRef.current = facilities
    const source = mapRef.current?.getSource('facilities') as GeoJSONSource | undefined
    source?.setData(facilitiesToGeoJson(facilities))
  }, [facilities])

  useEffect(() => {
    const source = mapRef.current?.getSource('route') as GeoJSONSource | undefined
    source?.setData(routeToGeoJson(route))
  }, [route])

  async function calculateRoute() {
    if (!origin || !destination) {
      setError('Click the map once for origin and once for destination.')
      return
    }
    setError(null)
    try {
      setRoute(await api.route(origin, destination, mode, {
        disruption_weight: disruptionWeight,
        pollution_weight: pollutionWeight,
        reliability_weight: reliabilityWeight
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  async function closeSegment() {
    if (!segmentId.trim()) return
    setError(null)
    try {
      await api.scenario(segmentId.trim())
      await refresh()
      if (origin && destination) await calculateRoute()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const cards = status ? networkStatusToCards(status, facilities.length) : []

  return (
    <main className="app-shell">
      <div ref={mapContainer} className="map" aria-label="Berlin resilience map" />
      <header className="brand glass">
        <div className="eyebrow">Decision support · Berlin</div>
        <h1>Urban Resilience Twin</h1>
        <p>Semantic relationships, network disruption and explainable accessibility analysis.</p>
      </header>
      <section className="status-row">
        {cards.map((card) => (
          <article className="status-card glass" key={card.label}>
            <span>{card.label}</span><strong>{card.value}</strong><small>{card.detail}</small>
          </article>
        ))}
      </section>
      <aside className="control-panel glass">
        <div className="panel-heading"><span className="eyebrow">Routing</span><strong>Scenario controls</strong></div>
        <label>Objective
          <select value={mode} onChange={(e) => setMode(e.target.value as RouteMode)}>
            <option value="fastest">Fastest</option><option value="most_reliable">Most reliable</option>
            <option value="lowest_exposure">Lowest exposure</option><option value="disruption_avoiding">Disruption avoiding</option>
          </select>
        </label>
        <label>Disruption weight<input type="number" min="0" step="0.1" value={disruptionWeight} onChange={(e) => setDisruptionWeight(Number(e.target.value))} /></label>
        <label>Pollution weight<input type="number" min="0" step="0.1" value={pollutionWeight} onChange={(e) => setPollutionWeight(Number(e.target.value))} /></label>
        <label>Reliability weight<input type="number" min="0" step="0.1" value={reliabilityWeight} onChange={(e) => setReliabilityWeight(Number(e.target.value))} /></label>
        <button className="primary" onClick={calculateRoute}>Calculate route</button>
        <div className="divider" />
        <label>Close road segment<input value={segmentId} onChange={(e) => setSegmentId(e.target.value)} placeholder="segment id" /></label>
        <button onClick={closeSegment}>Apply scenario overlay</button>
        <p className="hint">The overlay never mutates the base network. In the deterministic fixture, try segment <code>BC</code>.</p>
      </aside>
      <aside className="detail-panel glass">
        <div className="panel-heading"><span className="eyebrow">Explainability</span><strong>{selected ? selected.name : route ? 'Route rationale' : 'Select or calculate'}</strong></div>
        {selected ? (
          <dl><dt>Type</dt><dd>{selected.facility_type}</dd><dt>District</dt><dd>{selected.district_id}</dd><dt>Network node</dt><dd>{selected.connected_node_id}</dd><dt>Provenance</dt><dd>{selected.source_uri ?? 'fixture entity'}</dd></dl>
        ) : route ? (
          <><p>{route.explanation}</p><dl><dt>Travel time</dt><dd>{(route.travel_time_s / 60).toFixed(1)} min</dd><dt>Distance</dt><dd>{(route.distance_m / 1000).toFixed(2)} km</dd><dt>Reliability</dt><dd>{route.mean_reliability.toFixed(2)}</dd><dt>Affected segments</dt><dd>{route.affected_segment_ids.length}</dd></dl></>
        ) : (
          <p>Click the map twice to define a route. Click a facility marker to inspect its semantic/network relationship.</p>
        )}
        {error && <p className="error">{error}</p>}
      </aside>
      <footer className="timeline glass"><span className="dot" /><strong>{status?.active_scenario_id ? 'Scenario overlay active' : 'Baseline network'}</strong><span>{status?.generated_at ? new Date(status.generated_at).toLocaleString() : 'loading…'}</span><span className="spacer" /><span>Historical mode is intentionally unavailable until a real historical dataset is added.</span></footer>
    </main>
  )
}

export default App
