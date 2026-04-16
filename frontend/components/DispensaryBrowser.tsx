'use client'

import { useEffect, useRef, useState } from 'react'
import { Loader } from '@googlemaps/js-api-loader'
import axios from 'axios'

type Dispensary = {
  id: number
  name: string
  address: string
  latitude: number
  longitude: number
}

type Product = {
  id: number
  name: string
  category: string | null
  price: number
  unit: string | null
  in_stock: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const DEFAULT_LOCATION = { lat: 37.7749, lng: -122.4194 }
const DEFAULT_RANGE_MILES = 5

const milesToMeters = (miles: number) => Math.round(miles * 1609.34)

const formatApiError = (err: unknown, fallback: string) => {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status
    const detail = (err.response?.data as { detail?: string } | undefined)?.detail
    if (status && detail) return `${fallback} (HTTP ${status}): ${detail}`
    if (status) return `${fallback} (HTTP ${status})`
    if (err.message) return `${fallback}: ${err.message}`
  }
  return fallback
}

export default function DispensaryBrowser() {
  const mapRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<any>(null)
  const markersRef = useRef<any[]>([])
  const [dispensaries, setDispensaries] = useState<Dispensary[]>([])
  const [selectedDispensary, setSelectedDispensary] = useState<Dispensary | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [zipCode, setZipCode] = useState('94103')
  const [rangeMiles, setRangeMiles] = useState(DEFAULT_RANGE_MILES)
  const [searchSummary, setSearchSummary] = useState('Showing dispensaries within 5 miles of ZIP 94103')

  useEffect(() => {
    const loader = new Loader({
      apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '',
      version: 'weekly',
    })

    loader.load().then(() => {
      if (mapRef.current) {
        const google = (window as any).google
        const map = new google.maps.Map(mapRef.current, {
          center: DEFAULT_LOCATION,
          zoom: 12,
        })
        mapInstanceRef.current = map
        fetchDispensaries(DEFAULT_LOCATION.lat, DEFAULT_LOCATION.lng, milesToMeters(DEFAULT_RANGE_MILES))
      }
    }).catch((err) => {
      setError('Unable to load Google Maps: ' + err)
    })
  }, [])

  const setMarkers = (places: Dispensary[]) => {
    markersRef.current.forEach((marker) => marker.setMap(null))
    markersRef.current = []

    const google = (window as any).google
    places.forEach((place) => {
      if (!mapInstanceRef.current) return
      const marker = new google.maps.Marker({
        position: { lat: place.latitude, lng: place.longitude },
        map: mapInstanceRef.current,
        title: place.name,
      })
      marker.addListener('click', () => selectDispensary(place))
      markersRef.current.push(marker)
    })
  }

  const fetchDispensaries = async (lat: number, lng: number, radiusMeters: number, summaryLabel?: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`${API_URL}/dispensaries`, {
        params: { lat, lng, radius: radiusMeters },
      })

      const results: Dispensary[] = response.data.dispensaries || []
      setDispensaries(results)
      setMarkers(results)
      const radiusMiles = Math.max(1, Math.round(radiusMeters / 1609.34))
      const summaryPrefix = `Showing ${results.length} dispensary${results.length === 1 ? '' : 'ies'} within ${radiusMiles} miles`
      setSearchSummary(summaryLabel ? `${summaryPrefix} of ${summaryLabel}` : summaryPrefix)
      if (results.length > 0) {
        selectDispensary(results[0])
      }
    } catch (err) {
      setError(formatApiError(err, 'Unable to load dispensaries'))
    } finally {
      setLoading(false)
    }
  }

  const searchByZipCode = () => {
    const zip = zipCode.trim()
    if (!/^\d{5}$/.test(zip)) {
      setError('Please enter a valid 5-digit ZIP code.')
      return
    }

    const google = (window as any).google
    if (!google?.maps?.Geocoder) {
      setError('Google Maps is not ready yet. Please try again.')
      return
    }

    const geocoder = new google.maps.Geocoder()
    geocoder.geocode({ address: zip, componentRestrictions: { country: 'US' } }, (results: any, status: any) => {
      if (status !== 'OK' || !results || results.length === 0) {
        setError('Unable to find that ZIP code. Please try another one.')
        return
      }

      const location = results[0].geometry.location
      const coords = { lat: location.lat(), lng: location.lng() }
      if (mapInstanceRef.current) {
        mapInstanceRef.current.panTo(coords)
        mapInstanceRef.current.setZoom(11)
      }

      fetchDispensaries(coords.lat, coords.lng, milesToMeters(rangeMiles), `ZIP ${zip}`)
    })
  }

  const fetchProducts = async (dispensaryId: number) => {
    try {
      const response = await axios.get(`${API_URL}/products/${dispensaryId}`)
      setProducts(response.data.products || [])
    } catch (err) {
      setError(formatApiError(err, 'Unable to load products'))
    }
  }

  const selectDispensary = (dispensary: Dispensary) => {
    setSelectedDispensary(dispensary)
    if (mapInstanceRef.current) {
      mapInstanceRef.current.panTo({ lat: dispensary.latitude, lng: dispensary.longitude })
      mapInstanceRef.current.setZoom(14)
    }
    fetchProducts(dispensary.id)
  }

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported in this browser.')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        }
        if (mapInstanceRef.current) {
          mapInstanceRef.current.panTo(coords)
          mapInstanceRef.current.setZoom(13)
        }
        fetchDispensaries(coords.lat, coords.lng, milesToMeters(rangeMiles), 'your current location')
      },
      () => setError('Unable to retrieve your location.')
    )
  }

  return (
    <div className="grid lg:grid-cols-[1fr_420px] gap-4">
      <div className="space-y-4">
        <div className="rounded border bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Search Dispensaries</h2>
          <div className="grid sm:grid-cols-[minmax(0,1fr)_150px_auto] gap-2">
            <input
              type="text"
              inputMode="numeric"
              maxLength={5}
              placeholder="ZIP code"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value.replace(/\D/g, ''))}
              onKeyDown={(e) => {
                if (e.key === 'Enter') searchByZipCode()
              }}
              className="rounded border border-gray-300 px-3 py-2"
              aria-label="ZIP code"
            />
            <select
              value={rangeMiles}
              onChange={(e) => setRangeMiles(Number(e.target.value))}
              className="rounded border border-gray-300 px-3 py-2"
              aria-label="Search range"
            >
              <option value={3}>3 miles</option>
              <option value={5}>5 miles</option>
              <option value={10}>10 miles</option>
              <option value={15}>15 miles</option>
              <option value={25}>25 miles</option>
            </select>
            <button
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              onClick={searchByZipCode}
            >
              Search
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              onClick={useCurrentLocation}
            >
              Use my location
            </button>
            <button
              className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-800"
              onClick={() => fetchDispensaries(DEFAULT_LOCATION.lat, DEFAULT_LOCATION.lng, milesToMeters(rangeMiles))}
            >
              Reset to SF
            </button>
          </div>
        </div>

        {error && <div className="rounded border border-red-400 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        <div className="rounded border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
          {searchSummary}
        </div>

        <div ref={mapRef} className="w-full h-[520px] rounded border" />

        <div className="rounded border bg-white p-4 shadow-sm">
          <h2 className="text-xl font-semibold mb-3">Dispensaries</h2>
          {loading && <p>Loading dispensaries…</p>}
          {!loading && dispensaries.length === 0 && <p>No dispensaries found.</p>}
          <div className="space-y-3">
            {dispensaries.map((dispensary) => (
              <button
                key={dispensary.id}
                onClick={() => selectDispensary(dispensary)}
                className={`w-full text-left rounded border p-3 transition ${selectedDispensary?.id === dispensary.id ? 'border-green-600 bg-green-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}
              >
                <div className="font-semibold">{dispensary.name}</div>
                <div className="text-sm text-gray-600">{dispensary.address}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <aside className="space-y-4">
        <div className="rounded border bg-white p-4 shadow-sm">
          <h2 className="text-xl font-semibold mb-3">{selectedDispensary ? selectedDispensary.name : 'Select a dispensary'}</h2>
          {selectedDispensary ? (
            <>
              <p className="text-sm text-gray-600 mb-4">{selectedDispensary.address}</p>
              <h3 className="text-lg font-medium mb-2">Products</h3>
              {products.length === 0 ? (
                <p className="text-sm text-gray-500">No products available yet.</p>
              ) : (
                <div className="space-y-3">
                  {products.map((product) => (
                    <div key={product.id} className="rounded border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <div className="font-semibold">{product.name}</div>
                          <div className="text-sm text-gray-500">{product.category || 'Unknown category'}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">${product.price.toFixed(2)}</div>
                          <div className="text-sm text-gray-500">{product.unit || 'unit'}</div>
                        </div>
                      </div>
                      <div className="mt-2 text-sm text-gray-600">{product.in_stock ? 'In stock' : 'Out of stock'}</div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-500">Select a dispensary from the map or list to view its products.</p>
          )}
        </div>
      </aside>
    </div>
  )
}
