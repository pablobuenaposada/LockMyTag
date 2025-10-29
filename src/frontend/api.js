export function fetchTags() {
  return fetch(`${window.location.origin}/api/locations/tags/`).then(
    (response) => {
      if (!response.ok)
        throw new Error('Network response was not ok')
      return response.json()
    },
  )
}

export function fetchLatestLocation(uuid) {
  return fetch(`${window.location.origin}/api/locations/latest/${uuid}`).then(
    (response) => {
      if (!response.ok)
        throw new Error('Network response was not ok')
      return response.json()
    },
  )
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
  return fetch(`${window.location.origin}/api/locks/${uuid}`).then(
    (response) => {
      if (!response.ok)
        throw new Error('Network response was not ok')
      return response.json()
    },
  )
}
