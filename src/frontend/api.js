export class UnauthorizedError extends Error {
  constructor() {
    super('Unauthorized')
    this.name = 'UnauthorizedError'
  }
}

async function requestJson(path) {
  const response = await fetch(`${window.location.origin}${path}`, {
    credentials: 'same-origin', // send session cookie automatically
  })

  if (response.status === 401 || response.status === 403)
    throw new UnauthorizedError()

  if (!response.ok)
    throw new Error('Network response was not ok')

  return response.json()
}

export async function setCredentials(username, password) {
  // Exchange username/password for a session cookie — password hashing happens once only
  const csrfToken = await getCsrfToken()
  const response = await fetch(`${window.location.origin}/api/account/login/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ username, password }),
  })
  if (response.status === 401 || response.status === 403)
    throw new UnauthorizedError()
  if (!response.ok)
    throw new Error('Login failed')
}

export function clearCredentials() {
  // Simply navigate away — the session cookie will expire on its own,
  // or we could call a logout endpoint if added later.
  document.cookie = 'sessionid=; Max-Age=0; path=/'
}

async function getCsrfToken() {
  // Django sets csrftoken cookie on any GET request to a Django view
  await fetch(`${window.location.origin}/api/account/login/`, {
    method: 'GET',
    credentials: 'same-origin',
  })
  // Read from cookie
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
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
      // Colour follows this order, so index by age: a new tag appends rather
      // than shifting the colour of every tag already on the map. The index is
      // taken before any fetch can fail, or a 404 would renumber the rest.
      const oldestFirst = [...tags].sort((a, b) =>
        a.created.localeCompare(b.created),
      )
      const locationPromises = oldestFirst.map(
        (tag, index) =>
          fetchLatestLocation(tag.id)
            .then(location => ({
              tag: location.tag,
              name: tag.name,
              colorIndex: index,
              longitude: location.longitude,
              latitude: location.latitude,
              timestamp: location.timestamp,
              battery: location.battery,
            }))
            .catch(() => null), // Skip if fetch fails (e.g., 404)
      )
      return Promise.all(locationPromises)
    })
    .then(locations => locations.filter(loc => loc !== null))
}

export function fetchRoute(uuid, start, end) {
  const params = new URLSearchParams()
  if (start)
    params.set('start', start)
  if (end)
    params.set('end', end)
  const query = params.toString()
  return requestJson(`/api/locations/route/${uuid}${query ? `?${query}` : ''}`)
}

export function fetchLocks(uuid) {
  return requestJson(`/api/locks/${uuid}?status=active`)
}
