export async function fetchOpportunityGeoJSON(){
  const resp = await fetch('http://127.0.0.1:8000/data/opportunity.geojson')
  if(!resp.ok) throw new Error('Failed to load geojson')
  return await resp.json()
}
