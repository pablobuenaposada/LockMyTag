import * as L from 'https://unpkg.com/leaflet@1.9.4/dist/leaflet-src.esm.js'
import { fetchLatestLocationsForAllTags, fetchLocks } from './api.js'
import { daysOfWeek } from './constants.js'
import { lockIconSvg } from './lock.js'

function timeSince(dateString) {
  const now = new Date()
  const date = new Date(dateString)
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60)
    return `${seconds} sec. ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60)
    return `${minutes} min. ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24)
    return `${hours} hours ago`
  const days = Math.floor(hours / 24)
  return `${days} days ago`
}

function createLockIcon(color) {
  const coloredSvg = lockIconSvg.replace(
    /<svg([^>]*)>/,
    `<svg$1 fill="${color}">`,
  )
  return L.divIcon({
    className: '',
    html: coloredSvg,
    iconSize: [30, 30],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  })
}

function murmurhash3(str) {
  let h = 0x811C9DC5
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 0x01000193)
    h ^= h >>> 16
  }
  return h >>> 0
}

function hslToHex(h, s, l) {
  s /= 100
  l /= 100
  const k = n => (n + h / 30) % 12
  const a = s * Math.min(l, 1 - l)
  const f = n =>
    l - a * Math.max(-1, Math.min(Math.min(k(n) - 3, 9 - k(n)), 1))
  const rgb = [
    Math.round(255 * f(0)),
    Math.round(255 * f(8)),
    Math.round(255 * f(4)),
  ]
  return `#${rgb.map(x => x.toString(16).padStart(2, '0')).join('')}`
}

function stringToColor(str) {
  const hash = murmurhash3(str)
  const hue = hash % 360
  const sat = 60 + ((hash >> 8) % 30) // 60-89%
  const light = 40 + ((hash >> 16) % 20) // 40-59%
  const hsl = `hsl(${hue}, ${sat}%, ${light}%)`
  const hex = hslToHex(hue, sat, light)
  return { hsl, hex }
}

const map = L.map('map')

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  maxZoom: 19,
  attribution: '',
}).addTo(map)

fetchLatestLocationsForAllTags()
  .then(async (locations) => {
    const seen = new Set()
    const markersByTag = {}
    const schedulesByTag = {}

    await Promise.all(
      locations.map(async (loc) => {
        const locks = await fetchLocks(loc.tag)
        schedulesByTag[loc.tag] = locks.flatMap(lock =>
          lock.schedules.map(s => ({
            ...s,
            latitude: lock.latitude,
            longitude: lock.longitude,
          })),
        )
      }),
    )

    locations.forEach((loc) => {
      let lat = Number(loc.latitude)
      let lng = Number(loc.longitude)
      const key = `${lat},${lng}`
      if (seen.has(key)) {
        lat += (Math.random() - 0.5) * 0.0002
        lng += (Math.random() - 0.5) * 0.0002
      }
      seen.add(key)
      const icon = createLockIcon(stringToColor(loc.name).hsl)
      const marker = L.marker([lat, lng], { icon })
        .addTo(map)
        .bindPopup(
          `<b>${loc.name}</b><br>${loc.timestamp}<br>
           <a href="https://www.google.com/maps?q=${lat},${lng}" target="_blank">
             View on Google Maps
           </a>`,
        )
      markersByTag[loc.name] = marker
    })

    const bounds = locations.map(loc => [
      Number(loc.latitude),
      Number(loc.longitude),
    ])
    if (bounds.length) {
      map.fitBounds(bounds, { paddingBottomRight: [250, 0] })
    }

    const sidebar = document.getElementById('tags-list')
    sidebar.innerHTML = locations
      .map((loc) => {
        const schedules = (schedulesByTag[loc.tag] || []).slice().sort(
          (a, b) => a.day - b.day || a.start_time.localeCompare(b.start_time),
        )
        const schedulesHtml = schedules.length
          ? schedules.map((s) => {
              return `<div>
        ${daysOfWeek[s.day]} ${s.start_time} - ${s.end_time}
        <a href="https://www.google.com/maps?q=${s.latitude},${s.longitude}" target="_blank">📍</a>
      </div>`
            }).join('')
          : ''
        return `<div class="tag-row" data-tag="${loc.name}" data-tag-id="${loc.tag}" style="background:${stringToColor(loc.name).hex}33;">
          ${loc.name} <span class="tag-time">(${timeSince(loc.timestamp)})</span>
          <div class="tag-schedules">${schedulesHtml}</div>
        </div>`
      })
      .join('')

    sidebar.querySelectorAll('.tag-row').forEach((row) => {
      row.addEventListener('click', () => {
        sidebar.querySelectorAll('.tag-schedules').forEach(s => s.classList.remove('visible'))
        row.querySelector('.tag-schedules').classList.add('visible')

        const tag = row.getAttribute('data-tag')
        const marker = markersByTag[tag]
        if (marker) {
          marker.openPopup()
          map.setView(marker.getLatLng(), 17, { animate: true })
        }
      })
    })
  })
