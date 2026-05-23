const AUTH_STORAGE_KEY = 'lockmytag.basicAuth'

export class UnauthorizedError extends Error {
  constructor() {
    super('Unauthorized')
    this.name = 'UnauthorizedError'
  }
}

function getAuthHeaders() {
  const auth = window.sessionStorage.getItem(AUTH_STORAGE_KEY)
  return auth ? { Authorization: auth } : {}
}

async function requestJson(path) {
  const response = await fetch(`${window.location.origin}${path}`, {
    headers: getAuthHeaders(),
  })

  if (response.status === 401 || response.status === 403)
    throw new UnauthorizedError()

  if (!response.ok)
    throw new Error('Network response was not ok')

  return response.json()
}

export function setCredentials(username, password) {
  const encoded = window.btoa(`${username}:${password}`)
  window.sessionStorage.setItem(AUTH_STORAGE_KEY, `Basic ${encoded}`)
}

export function clearCredentials() {
  window.sessionStorage.removeItem(AUTH_STORAGE_KEY)
}

export function fetchTags() {
  return requestJson('/api/locations/tags/')
}

export function fetchLatestLocation(uuid) {
  return requestJson(`/api/locations/latest/${uuid}`)
}

export function fetchLatestLocationsForAllTags() {
  return fetchTags()
    .then((tags) => {
      const locationPromises = tags.map(
        tag =>
          fetchLatestLocation(tag.id)
            .then(location => ({
              tag: location.tag,
              name: tag.name,
              longitude: location.longitude,
              latitude: location.latitude,
              timestamp: location.timestamp,
            }))
            .catch(() => null), // Skip if fetch fails (e.g., 404)
      )
      return Promise.all(locationPromises)
    })
    .then(locations => locations.filter(loc => loc !== null))
}

export function fetchLocks(uuid) {
  return requestJson(`/api/locks/${uuid}?status=active`)
}
