// Tag colours are chosen so no two are easy to confuse: each entry is the
// colour furthest from every colour already in the list, measured as CIEDE2000
// perceptual distance. The closest pair sits around 19 at 14 tags and 14 at 20,
// where roughly 2 is the point a difference stops being visible at all.
//
// Candidates are limited to what reads as a dot on a light map — not so pale it
// disappears, not so dark it looks black, not so grey it looks muddy — and stay
// clear of the basemap and of the green and red route end markers.
//
// Order matters: the earliest entries are the furthest apart, so a handful of
// tags gets the most distinct colours. Tags are indexed by age, so adding one
// takes the next colour and never repaints the tags already on the map.
const PALETTE = [
  '#046095',
  '#d006ef',
  '#c18d15',
  '#0aacb8',
  '#822b54',
  '#7a501f',
  '#3899fa',
  '#cf6e8e',
  '#2b0df2',
  '#6b7326',
  '#fa7f42',
  '#a2b305',
  '#776ecf',
  '#227755',
  '#82342b',
  '#8c089b',
  '#15c19f',
  '#d10557',
  '#bd5b05',
  '#cc7466',
  '#b83d8f',
  '#fa42c3',
  '#8f6e14',
  '#06b8ef',
]

export function tagColor(index) {
  // Past the end of the list colours repeat, which is better than inventing
  // near-duplicates that look like a bug
  return PALETTE[index % PALETTE.length]
}
