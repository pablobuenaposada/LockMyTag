import { lockIconSvg } from "./lock.js";
import { fetchLatestLocationsForAllTags } from "./api.js";
import * as L from "https://unpkg.com/leaflet@1.9.4/dist/leaflet-src.esm.js";

function timeSince(dateString) {
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function createLockIcon(color) {
  // Add or replace fill attribute in the <svg> tag
  const coloredSvg = lockIconSvg.replace(
    /<svg([^>]*)>/,
    `<svg$1 fill="${color}">`,
  );
  return L.divIcon({
    className: "",
    html: coloredSvg,
    iconSize: [30, 30],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
}

function stringToColor(str) {
  // Simple hash to get a number from the string
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  // Map hash to hue (0-359)
  const hue = Math.abs(hash) % 360;
  const sat = 80;   // Fixed high saturation for vivid color
  const light = 50; // Fixed lightness for base color
  const hsl = `hsl(${hue}, ${sat}%, ${light}%)`;

  // Convert HSL to RGB for hex output
  function hslToRgb(h, s, l) {
    s /= 100;
    l /= 100;
    const k = n => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = n =>
      l - a * Math.max(-1, Math.min(Math.min(k(n) - 3, 9 - k(n)), 1));
    return [
      Math.round(255 * f(0)),
      Math.round(255 * f(8)),
      Math.round(255 * f(4)),
    ];
  }
  function rgbToHex([r, g, b]) {
    return (
      "#" +
      [r, g, b]
        .map(x => x.toString(16).padStart(2, "0"))
        .join("")
    );
  }
  const hex = rgbToHex(hslToRgb(hue, sat, light));
  return { hsl, hex };
}

const map = L.map("map");

L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
  maxZoom: 19,
  attribution: "",
}).addTo(map);

fetchLatestLocationsForAllTags()
  .then((locations) => {
    const seen = new Set();
    const markersByTag = {};
    locations.forEach((loc) => {
      let lat = Number(loc.latitude);
      let lng = Number(loc.longitude);
      const key = `${lat},${lng}`;
      if (seen.has(key)) {
        lat += (Math.random() - 0.5) * 0.0002;
        lng += (Math.random() - 0.5) * 0.0002;
      }
      seen.add(key);
      const icon = createLockIcon(stringToColor(loc.name).hsl);
      const marker = L.marker([lat, lng], { icon })
        .addTo(map)
        .bindPopup(
          `<b>${loc.name}</b><br>${loc.timestamp}<br>
           <a href="https://www.google.com/maps?q=${lat},${lng}" target="_blank">
             View on Google Maps
           </a>`
        );
      markersByTag[loc.name] = marker;
    });
    const bounds = locations.map((loc) => [Number(loc.latitude), Number(loc.longitude)]);
    if (bounds.length) {
      map.fitBounds(bounds);
    }

    // Populate sidebar with tag rows
    const sidebar = document.getElementById('sidebar');
    sidebar.innerHTML = '<h2>Tags</h2>' +
  locations.map(loc =>
    `<div class="tag-row" data-tag="${loc.name}" style="background:${stringToColor(loc.name).hex}33;">
  ${loc.name} <span class="tag-time">(${timeSince(loc.timestamp)})</span>
</div>`
  ).join('');

    // Add click event to each tag row
    sidebar.querySelectorAll('.tag-row').forEach(row => {
      row.addEventListener('click', () => {
        const tag = row.getAttribute('data-tag');
        const marker = markersByTag[tag];
        if (marker) {
          marker.openPopup();
          map.setView(marker.getLatLng(), 17, { animate: true });
        }
      });
    });
  })
  .catch((error) => {
    console.error("Fetch error:", error);
  });