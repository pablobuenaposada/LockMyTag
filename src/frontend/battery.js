import { batteryLevels } from './constants.js'

// full/medium are the normal state and just add noise, so only flag the ones worth acting on
const alertLevels = new Set(['low', 'very_low'])

export function batteryIconSvg(level) {
  const battery = batteryLevels[level]
  if (!battery || !alertLevels.has(level))
    return ''
  return `<svg class="battery-icon" viewBox="0 0 26 12">
    <title>Battery: ${battery.label}</title>
    <rect x="0.5" y="0.5" width="21" height="11" rx="2.5" fill="none" stroke="${battery.color}" />
    <rect x="23" y="4" width="3" height="4" rx="1" fill="${battery.color}" />
    <rect x="2" y="2" width="${(18 * battery.fill).toFixed(1)}" height="8" rx="1" fill="${battery.color}" />
  </svg>`
}
