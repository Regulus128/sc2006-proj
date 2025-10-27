export async function fetchOpportunityGeoJSON() {
  const r = await fetch('/data/opportunity.geojson')
  if (!r.ok) throw new Error('Failed to load geojson')
  return r.json()
}