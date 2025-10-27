import React from 'react'
import MapView from '../../components/Map/MapView'
import { AppStateProvider } from '../../contexts/AppStateContext'

export default function MainPage(){
  return (
    <AppStateProvider>
      <div style={{ height: '100%' }}>
        <MapView />
      </div>
    </AppStateProvider>
  )
}


