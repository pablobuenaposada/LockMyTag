import { maplibreGL } from '@maplibre/maplibre-gl-leaflet'
import * as L from 'leaflet'
import {
  fetchLatestLocationsForAllTags,
  fetchLocks,
  fetchRoute,
  logout,
  setCredentials,
  UnauthorizedError,
} from './api.js'
import { batteryIconSvg } from './battery.js'
import { tagColor, tagHue } from './colors.js'
import { daysOfWeek } from './constants.js'
import { logoIconSvg } from './logo.js'

// Rows and popups are built as HTML strings, and a tag's name and emoji come
// from the database, so anything going into one has to be escaped first
const ESCAPES = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  '\'': '&#39;',
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ESCAPES[character])
}

// 21:00:00 -> 21:00
function withoutSeconds(time) {
  return time.slice(0, 5)
}

// The API sends ISO timestamps with an offset; show them in the browser's own
// time zone and locale, e.g. 29 Oct 2026, 14:05:09
const localTimeFormat = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'medium',
})

function localTime(dateString) {
  return localTimeFormat.format(new Date(dateString))
}

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

// A tag shows its own emoji if it has one, otherwise the padlock in its colour
function createTagIcon(color, hue, emoji) {
  const html = emoji
    ? `<span class="tag-emoji" style="--hue:${hue}">${escapeHtml(emoji)}</span>`
    : logoIconSvg.replace(/<svg([^>]*)>/, `<svg$1 fill="${color}">`)
  return L.divIcon({
    className: '',
    html,
    // Each gets a box its own shape — the logo is portrait, the emoji square —
    // and both are anchored at the foot so the marker points at the same spot
    iconSize: emoji ? [38, 38] : [24, 38],
    iconAnchor: emoji ? [19, 38] : [12, 38],
    popupAnchor: [0, -32],
  })
}

function isoDate(date) {
  // Local calendar date, not UTC — the picker and the backend both mean local days
  const offsetMs = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 10)
}

const map = L.map('map', { maxZoom: 19, attributionControl: false })

maplibreGL({
  style: 'https://tiles.openfreemap.org/styles/positron',
  attribution:
    '<a href="https://openfreemap.org">OpenFreeMap</a> '
    + '<a href="https://www.openstreetmap.org/copyright">&copy; OpenStreetMap contributors</a>',
}).addTo(map)

// Show entire world map
map.fitBounds([
  [-85, -180],
  [85, 180],
])

map.createPane('lockArea')
map.getPane('lockArea').style.zIndex = 380

map.createPane('routeBase')
map.getPane('routeBase').style.zIndex = 390
const routeBaseRenderer = L.canvas({ pane: 'routeBase', padding: 0.5 })

// A line that will not fit shrinks its text rather than being cut short. CSS
// cannot size text to its container, so it has to be measured.
const ROW_MIN_FONT = 9

function shrinkToFit(line) {
  line.style.fontSize = ''
  let size = Number.parseFloat(getComputedStyle(line).fontSize)
  while (line.scrollWidth > line.clientWidth && size > ROW_MIN_FONT) {
    size -= 0.5
    line.style.fontSize = `${size}px`
  }
}

function fitTagRows() {
  document.querySelectorAll('.tag-head, .tag-schedule').forEach(shrinkToFit)
}

const sidebar = document.getElementById('tags-list')
sidebar.parentElement.classList.add('hidden')
let loginTemplatePromise

function loadLoginTemplate() {
  if (!loginTemplatePromise) {
    loginTemplatePromise = fetch(`${window.location.origin}/login.html`).then(
      (response) => {
        if (!response.ok)
          throw new Error('Could not load login template')
        return response.text()
      },
    )
  }
  return loginTemplatePromise
}

async function showLoginPage() {
  let loginPage = document.getElementById('login-page')
  if (!loginPage) {
    loginPage = document.createElement('div')
    loginPage.id = 'login-page'
    loginPage.innerHTML = await loadLoginTemplate()
    document.body.appendChild(loginPage)
  }

  const loginError = document.getElementById('login-error')
  if (!loginError)
    return

  loginError.textContent = ''

  const form = document.getElementById('login-form')
  form.onsubmit = async (event) => {
    event.preventDefault()
    const username = document.getElementById('username').value
    const password = document.getElementById('password').value

    try {
      await setCredentials(username, password)
      await loadMap()
      loginPage.remove()
    }
    catch (error) {
      // Logged in but the map would not load: do not leave a session behind
      logout().catch(() => {})
      loginError.textContent
        = error instanceof UnauthorizedError
          ? 'Invalid username or password. Please try again.'
          : 'Could not login right now. Please try again.'
    }
  }
}

let routeLayer = null
let routeFrame = null
let lockAreaCircle = null
// Which pin opened the area. Every pin for that lock lights up, but only the
// one actually clicked puts it away again — otherwise clicking a sibling pin
// reads as "already shown" and hides the circle you were trying to keep.
let lockAreaPin = null

function clearLockArea() {
  if (lockAreaCircle) {
    map.removeLayer(lockAreaCircle)
    lockAreaCircle = null
  }
  lockAreaPin = null
}

// The circle a scheduled lock watches: centre plus its radius in metres, drawn
// so you can see whether the tag is meant to be inside it right now
function showLockArea(lock, name, color) {
  clearLockArea()

  const when = lock.schedules
    .slice()
    .sort((a, b) => a.day - b.day || a.start_time.localeCompare(b.start_time))
    .map(s =>
      escapeHtml(
        `${daysOfWeek[s.day]} ${withoutSeconds(s.start_time)} - ${withoutSeconds(s.end_time)}`,
      ),
    )
    .join('<br>')

  lockAreaCircle = L.circle([lock.latitude, lock.longitude], {
    pane: 'lockArea',
    radius: lock.radius,
    color,
    weight: 2,
    opacity: 0.85,
    dashArray: '6 4',
    fillColor: color,
    fillOpacity: 0.1,
  })
    .bindPopup(
      `<b>${escapeHtml(name)}</b><br>Lock area · ${escapeHtml(lock.radius)} m<br>${when}<br>`
      + `<a href="https://www.google.com/maps?q=${lock.latitude},${lock.longitude}" target="_blank">View on Google Maps</a>`,
    )
    .addTo(map)

  // A 1 km radius overflows the view at the zoom a tag click leaves you at,
  // so frame the circle rather than drawing it off screen
  map.fitBounds(lockAreaCircle.getBounds(), {
    paddingBottomRight: [250, 0],
    maxZoom: 17,
    animate: true,
  })
}

function clearRoute() {
  if (routeFrame) {
    cancelAnimationFrame(routeFrame)
    routeFrame = null
  }
  if (routeLayer) {
    map.removeLayer(routeLayer)
    routeLayer = null
  }
}

const ROUTE_FADE_SEGMENTS = 30
// One dot runs the whole route on a loop, so direction is read from the motion
// rather than from clutter laid over the route
const ROUTE_LOOP_MS = 8000
const ROUTE_TAIL_FRACTION = 0.07
const ROUTE_POINT_RADIUS = 3
const stillPlease = window.matchMedia('(prefers-reduced-motion: reduce)')

function zoomToTag(latLng) {
  map.setView(latLng, map.getMaxZoom(), { animate: true })
}

function endpointMarker(latLng, fillColor, name, label, timestamp) {
  return L.circleMarker(latLng, {
    radius: 7,
    color: '#fff',
    weight: 2,
    fillColor,
    fillOpacity: 1,
  }).bindPopup(
    `<b>${escapeHtml(name)}</b><br>${escapeHtml(label)}<br>${escapeHtml(localTime(timestamp))}`,
  )
}

function distancesAlong(points) {
  const travelled = [0]
  for (let i = 1; i < points.length; i++) {
    travelled.push(
      travelled[i - 1] + L.latLng(points[i - 1]).distanceTo(points[i]),
    )
  }
  return travelled
}

// Where along the route a given distance falls. Binary search rather than a
// walking cursor, so the dot can wrap back to the start without bookkeeping.
function positionAt(points, travelled, distance) {
  let low = 1
  let high = points.length - 1
  while (low < high) {
    const mid = (low + high) >> 1
    if (travelled[mid] < distance)
      low = mid + 1
    else high = mid
  }
  const length = travelled[low] - travelled[low - 1]
  const ratio = length ? (distance - travelled[low - 1]) / length : 0
  const from = points[low - 1]
  const to = points[low]
  return {
    index: low,
    latLng: [
      from[0] + (to[0] - from[0]) * ratio,
      from[1] + (to[1] - from[1]) * ratio,
    ],
  }
}

// The stretch of route just behind the dot, so it reads as a comet rather than
// a bead sliding along a wire
function tailPoints(points, travelled, head, length) {
  const from = positionAt(points, travelled, Math.max(0, head - length))
  const to = positionAt(points, travelled, head)
  return [from.latLng, ...points.slice(from.index, to.index), to.latLng]
}

function runningDot(points, color) {
  const travelled = distancesAlong(points)
  const total = travelled[points.length - 1]
  if (!total)
    return [] // Tag never moved, so there is no direction to show

  const tailLength = total * ROUTE_TAIL_FRACTION
  const tail = L.polyline([], {
    color,
    weight: 5,
    opacity: 0.95,
    interactive: false,
  })
  const dot = L.circleMarker(points[0], {
    radius: 5,
    color: '#fff',
    weight: 2,
    fillColor: color,
    fillOpacity: 1,
    interactive: false,
  })

  function moveTo(head) {
    tail.setLatLngs(tailPoints(points, travelled, head, tailLength))
    dot.setLatLng(positionAt(points, travelled, head).latLng)
  }

  if (stillPlease.matches) {
    moveTo(total * 0.25) // Parked partway round, but still pointing somewhere
    return [tail, dot]
  }

  let origin = null
  function frame(now) {
    origin ??= now
    moveTo((((now - origin) % ROUTE_LOOP_MS) / ROUTE_LOOP_MS) * total)
    routeFrame = requestAnimationFrame(frame)
  }
  routeFrame = requestAnimationFrame(frame)

  return [tail, dot]
}

function fadedLine(points, color) {
  // Oldest stretch faint, newest solid, so time still reads in a screenshot,
  // where the running dot shows as nothing at all
  const size = Math.max(
    1,
    Math.ceil((points.length - 1) / ROUTE_FADE_SEGMENTS),
  )
  const lines = []
  for (let start = 0; start < points.length - 1; start += size) {
    const progress = start / (points.length - 1)
    lines.push(
      // One point of overlap, otherwise the chunks render with gaps between them
      L.polyline(points.slice(start, start + size + 1), {
        renderer: routeBaseRenderer,
        color,
        weight: 3,
        opacity: 0.35 + 0.55 * progress,
      }),
    )
  }
  return lines
}

// A dot on every reported position, so the route reads as the readings it
// actually is rather than as a smooth path. Carries the same fade as the line
// so the two agree about which end is older.
function locationDots(points, color) {
  const span = points.length - 1 || 1
  return points.map((point, index) =>
    L.circleMarker(point, {
      renderer: routeBaseRenderer,
      radius: ROUTE_POINT_RADIUS,
      color: '#fff',
      weight: 1,
      opacity: 0.5 + 0.35 * (index / span),
      fillColor: color,
      fillOpacity: 0.45 + 0.5 * (index / span),
      interactive: false, // Never swallow a click meant for the map
    }),
  )
}

async function showRoute(tag, name, color, start, end, statusElement) {
  statusElement.textContent = 'Loading…'
  let route
  try {
    route = await fetchRoute(tag, start, end)
  }
  catch (error) {
    statusElement.textContent
      = error instanceof UnauthorizedError
        ? 'Session expired — reload to log in again.'
        : 'Could not load the route.'
    return
  }

  clearRoute()

  if (!route.count) {
    statusElement.textContent = 'No locations in that range.'
    return
  }

  const points = route.points.map(point => [
    Number(point.latitude),
    Number(point.longitude),
  ])
  const last = points.length - 1
  routeLayer = L.layerGroup([
    ...fadedLine(points, color),
    ...locationDots(points, color),
    ...runningDot(points, color),
    endpointMarker(
      points[0],
      '#16a34a',
      name,
      'Start',
      route.points[0].timestamp,
    ),
    endpointMarker(
      points[last],
      '#dc2626',
      name,
      'End',
      route.points[last].timestamp,
    ),
  ]).addTo(map)
  map.fitBounds(points, { paddingBottomRight: [250, 0] })

  statusElement.textContent = route.truncated
    ? `${route.count} points (capped — narrow the range to see the rest)`
    : `${route.count} points`
}

async function loadMap() {
  const locations = await fetchLatestLocationsForAllTags()
  const seen = new Set()
  const markersByTag = {}
  const schedulesByTag = {}
  const locksByTag = {}
  const colorByTag = Object.fromEntries(
    locations.map(loc => [loc.tag, tagColor(loc.colorIndex)]),
  )
  const hueByTag = Object.fromEntries(
    locations.map(loc => [loc.tag, tagHue(loc.colorIndex)]),
  )

  await Promise.all(
    locations.map(async (loc) => {
      const locks = await fetchLocks(loc.tag)
      locksByTag[loc.tag] = locks
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
    const icon = createTagIcon(
      colorByTag[loc.tag],
      hueByTag[loc.tag],
      loc.emoji,
    )
    const marker = L.marker([lat, lng], { icon })
      .addTo(map)
      .bindPopup(
        `<b>${escapeHtml(loc.name)}</b><br>${escapeHtml(localTime(loc.timestamp))}<br>
         <a href="https://www.google.com/maps?q=${lat},${lng}" target="_blank">
           View on Google Maps
         </a>`,
      )
      .on('click', () => zoomToTag(marker.getLatLng()))
    markersByTag[loc.name] = marker
  })

  const bounds = locations.map(loc => [
    Number(loc.latitude),
    Number(loc.longitude),
  ])
  // The opening view and the reset button must agree, so there is one of it
  function showAllTags() {
    if (!bounds.length)
      return
    map.fitBounds(bounds, {
      paddingTopLeft: [60, 60],
      paddingBottomRight: [310, 60],
    })
  }

  // Back to how the map opened: every tag in view, nothing selected
  function resetView() {
    clearRoute()
    clearLockArea()
    map.closePopup()
    sidebar
      .querySelectorAll('.tag-schedules.visible')
      .forEach(panel => panel.classList.remove('visible'))
    sidebar
      .querySelectorAll('.schedule-pin.active')
      .forEach(pin => pin.classList.remove('active'))
    sidebar.querySelectorAll('.route-status').forEach((status) => {
      status.textContent = ''
    })
    showAllTags()
  }

  document.getElementById('show-all').addEventListener('click', resetView)
  document.getElementById('logout').addEventListener('click', async () => {
    try {
      await logout()
    }
    catch {
      return // still logged in, so stay on the map
    }
    // Starting over is the simplest way to drop every tag, marker and timer
    // the session loaded; with no session the page lands on the login form
    window.location.reload()
  })
  showAllTags()

  const today = new Date()
  const defaultEnd = isoDate(today)
  const defaultStart = isoDate(
    new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000),
  )

  sidebar.innerHTML = locations
    .map((loc) => {
      const schedules = (schedulesByTag[loc.tag] || [])
        .slice()
        .sort(
          (a, b) => a.day - b.day || a.start_time.localeCompare(b.start_time),
        )
      const schedulesHtml = schedules.length
        ? schedules
            .map((s) => {
              return `<div class="tag-schedule">
      <span>${escapeHtml(`${daysOfWeek[s.day]} ${withoutSeconds(s.start_time)} - ${withoutSeconds(s.end_time)}`)}</span>
      <button type="button" class="schedule-pin" data-lock="${s.lock}" title="Show this lock's area">📍</button>
    </div>`
            })
            .join('')
        : ''
      return `<div class="tag-row" data-tag="${escapeHtml(loc.name)}" data-tag-id="${escapeHtml(loc.tag)}" style="background:${colorByTag[loc.tag]}33;">
        <div class="tag-head">${
          loc.emoji
            ? `<span class="tag-emoji tag-emoji-row" style="--hue:${hueByTag[loc.tag]}">${escapeHtml(loc.emoji)}</span>`
            : `<span class="tag-dot" style="background:${colorByTag[loc.tag]}"></span>`
        }<span class="tag-name">${escapeHtml(loc.name)}</span>${batteryIconSvg(loc.battery)}<span class="tag-time">(${timeSince(loc.timestamp)})</span></div>
        <div class="tag-schedules">${schedulesHtml}
          <div class="tag-schedules-edit"><a href="${window.location.origin}/admin/locks/lock/?tag__name=${encodeURIComponent(loc.name)}">edit lock schedules</a></div>
          <div class="tag-route">
            <div class="tag-route-title">Past route</div>
            <label>from <input type="date" class="route-start" value="${defaultStart}" max="${defaultEnd}"></label>
            <label>to <input type="date" class="route-end" value="${defaultEnd}" max="${defaultEnd}"></label>
            <div class="tag-route-buttons">
              <button type="button" class="route-show">Show</button>
              <button type="button" class="route-clear">Clear</button>
            </div>
            <div class="route-status"></div>
          </div>
        </div>
      </div>`
    })
    .join('')

  sidebar.querySelectorAll('.tag-row').forEach((row) => {
    const name = row.getAttribute('data-tag')
    const tagId = row.getAttribute('data-tag-id')
    const routePanel = row.querySelector('.tag-route')
    const status = routePanel.querySelector('.route-status')

    row.addEventListener('click', () => {
      const alreadyOpen = row
        .querySelector('.tag-schedules')
        .classList
        .contains('visible')
      sidebar
        .querySelectorAll('.tag-schedules')
        .forEach(s => s.classList.remove('visible'))
      row.querySelector('.tag-schedules').classList.add('visible')

      // Opening a different tag drops the route still on screen, so the line
      // on the map always belongs to the tag whose panel is open
      if (!alreadyOpen) {
        clearRoute()
        clearLockArea()
        sidebar
          .querySelectorAll('.schedule-pin.active')
          .forEach(pin => pin.classList.remove('active'))
        status.textContent = ''
      }

      const marker = markersByTag[name]
      if (marker) {
        marker.openPopup()
        zoomToTag(marker.getLatLng())
      }
    })

    row.querySelectorAll('.schedule-pin').forEach((pin) => {
      pin.addEventListener('click', (event) => {
        // Otherwise the row handler fires too and snaps the view back
        event.stopPropagation()
        const lock = (locksByTag[tagId] || []).find(
          candidate => String(candidate.id) === pin.dataset.lock,
        )
        if (!lock)
          return
        const wasOpenedByThisPin = pin === lockAreaPin
        clearLockArea()
        sidebar
          .querySelectorAll('.schedule-pin.active')
          .forEach(other => other.classList.remove('active'))

        // Clicking the pin that opened the area puts it away; any other pin
        // shows its lock and lights every pin sharing that lock
        if (!wasOpenedByThisPin) {
          showLockArea(lock, name, colorByTag[tagId])
          lockAreaPin = pin
          row
            .querySelectorAll(`.schedule-pin[data-lock="${pin.dataset.lock}"]`)
            .forEach(sibling => sibling.classList.add('active'))
        }
      })
    })

    // The row click zooms to the latest position, which would fight with
    // picking dates, so the controls keep their clicks to themselves
    routePanel.addEventListener('click', event => event.stopPropagation())

    routePanel.querySelector('.route-show').addEventListener('click', () => {
      showRoute(
        tagId,
        name,
        colorByTag[tagId],
        routePanel.querySelector('.route-start').value,
        routePanel.querySelector('.route-end').value,
        status,
      )
    })

    routePanel.querySelector('.route-clear').addEventListener('click', () => {
      clearRoute()
      status.textContent = ''
    })
  })

  sidebar.parentElement.classList.remove('hidden')
  // Only measurable once the sidebar is on screen and has a width
  fitTagRows()
}

// The sidebar is a share of the window, so a resize changes what fits
window.addEventListener('resize', fitTagRows)

loadMap().catch((error) => {
  if (error instanceof UnauthorizedError) {
    showLoginPage()
  }
})
