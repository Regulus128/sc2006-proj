import React, { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { fetchOpportunityGeoJSON } from '../../services/api'
import ChoroplethLayer from './ChoroplethLayer'

export default function MapView(){
  const [data, setData] = useState<any>(null)
  useEffect(()=>{
    fetchOpportunityGeoJSON().then(setData).catch(console.error)
  },[])
  const center = useMemo(()=>({ lat: 1.3521, lng: 103.8198 }),[])
  return (
    <MapContainer center={center} zoom={11} style={{ height: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="© OpenStreetMap" />
      {data && <ChoroplethLayer data={data} />}
    </MapContainer>
  )
}
