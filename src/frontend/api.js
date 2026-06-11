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
