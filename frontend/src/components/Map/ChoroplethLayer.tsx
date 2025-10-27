import React from 'react'
import { GeoJSON } from 'react-leaflet'
import { colorForScore } from '../../utils/colorScale'

export default function ChoroplethLayer({ data }: { data: any }){
  function style(feature: any){
    const s = feature?.properties?.H_score ?? feature?.properties?.h_score ?? 0
    return { weight: 0.6, color: '#666', fillOpacity: 0.7, fillColor: colorForScore(s) }
  }
  return <GeoJSON data={data} style={style as any} />
}
