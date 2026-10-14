/* ============================================================
   OBS Studio — Web Replication · Icon Registry
   Inline SVG set mirroring OBS 30.x iconography
   ============================================================ */

const M = (d, extra = '') => `<path d="${d}" ${extra}/>`;

/* Monochrome icon bodies (stroke or fill using currentColor) */
const mono = {
  gear: M('M8 5.2A2.8 2.8 0 1 0 8 10.8 2.8 2.8 0 0 0 8 5.2Zm0 1.2a1.6 1.6 0 1 1 0 3.2 1.6 1.6 0 0 1 0-3.2Z', 'fill="currentColor"') + M('M7.1 1h1.8l.3 1.7c.4.1.8.3 1.1.5l1.6-.8 1.3 1.3-.8 1.6c.2.3.4.7.5 1.1l1.7.3v1.8l-1.7.3c-.1.4-.3.8-.5 1.1l.8 1.6-1.3 1.3-1.6-.8c-.3.2-.7.4-1.1.5L8.9 15H7.1l-.3-1.7c-.4-.1-.8-.3-1.1-.5l-1.6.8-1.3-1.3.8-1.6c-.2-.3-.4-.7-.5-1.1L1.4 8.9V7.1l1.7-.3c.1-.4.3-.8.5-1.1l-.8-1.6L4.1 2.8l1.6.8c.3-.2.7-.4 1.1-.5L7.1 1Z', 'fill="none" stroke="currentColor" stroke-width="1.1"'),
  plus: M('M7.3 2h1.4v5.3H14v1.4H8.7V14H7.3V8.7H2V7.3h5.3V2Z', 'fill="currentColor"'),
  minus: M('M2 7.3h12v1.4H2V7.3Z', 'fill="currentColor"'),
  up: M('M8 3.5 12.7 9.6l-1.1.9L8 6.4l-3.6 4.1-1.1-.9L8 3.5Z', 'fill="currentColor"'),
  down: M('M8 12.5 3.3 6.4l1.1-.9L8 9.6l3.6-4.1 1.1.9L8 12.5Z', 'fill="currentColor"'),
  eye: M('M8 3.5c3.2 0 5.9 2 7 4.5-1.1 2.5-3.8 4.5-7 4.5S2.1 10.5 1 8c1.1-2.5 3.8-4.5 7-4.5Zm0 1.4C5.5 4.9 3.4 6.3 2.5 8c.9 1.7 3 3.1 5.5 3.1s4.6-1.4 5.5-3.1C12.6 6.3 10.5 4.9 8 4.9Zm0 1.1a2 2 0 1 1 0 4 2 2 0 0 1 0-4Z', 'fill="currentColor"'),
  'eye-off': M('M8 3.5c3.2 0 5.9 2 7 4.5-.5 1.1-1.3 2.1-2.2 2.9l1.4 1.4-.9.9L2.8 2.7l.9-.9 1.6 1.6C6.1 3.7 7 3.5 8 3.5Zm-4.9 2 1 1C4.6 6 5.2 5.6 5.9 5.3l.7 1.1A4 4 0 0 0 4.9 8c.4.8 1.1 1.5 1.9 2l.7 1.2c-1.9-.5-3.5-1.8-4.5-3.2.3-.9.6-1.7 1.1-2.5Zm4.9.4c.3 0 .6 0 .9.1l2.6 2.6c-.4 1.5-1.8 2.6-3.5 2.6-.3 0-.6 0-.9-.1L5.5 8.5C5.9 7 7.3 5.9 8 5.9Z', 'fill="currentColor"'),
  lock: M('M8 1.8c1.8 0 3.2 1.4 3.2 3.2v1.5h.6c.5 0 .9.4.9.9v5.6c0 .5-.4.9-.9.9H4.2a.9.9 0 0 1-.9-.9V7.4c0-.5.4-.9.9-.9h.6V5c0-1.8 1.4-3.2 3.2-3.2Zm0 1.3C7 3.1 6.1 4 6.1 5v1.5h3.8V5c0-1-.9-1.9-1.9-1.9Z', 'fill="currentColor"'),
  unlock: M('M8 1.8c1.6 0 2.9 1.1 3.2 2.6l-1.3.4A1.9 1.9 0 0 0 8 3.1C7 3.1 6.1 4 6.1 5v1.5h5.7c.5 0 .9.4.9.9v5.6c0 .5-.4.9-.9.9H4.2a.9.9 0 0 1-.9-.9V7.4c0-.5.4-.9.9-.9h.6V5c0-1.8 1.4-3.2 3.2-3.2Z', 'fill="currentColor"'),
  vol: M('M9.3 2.2v11.6c0 .5-.6.8-1 .5L5 11.5H2.7a.7.7 0 0 1-.7-.7V5.2c0-.4.3-.7.7-.7H5l3.3-2.8c.4-.3 1 0 1 .5Zm2.2 1.9c1 .9 1.7 2.3 1.7 3.9s-.7 3-1.7 3.9l-.9-.9c.8-.7 1.2-1.8 1.2-3s-.4-2.3-1.2-3l.9-.9Zm-1.6 1.8c.6.6 1 1.3 1 2.1s-.4 1.5-1 2.1l-.8-.8c.3-.4.5-.8.5-1.3s-.2-.9-.5-1.3l.8-.8Z', 'fill="currentColor"'),
  'vol-mute': M('M9.3 2.2v11.6c0 .5-.6.8-1 .5L5 11.5H2.7a.7.7 0 0 1-.7-.7V5.2c0-.4.3-.7.7-.7H5l3.3-2.8c.4-.3 1 0 1 .5Zm1.7 3.1 1.1-1.1 1.2 1.2L12.2 6.5l1.1 1.1-1.2 1.2-1.1-1.1-1.1 1.1-1.2-1.2 1.1-1.1-1.1-1.1 1.2-1.2 1.1 1.1Z', 'fill="currentColor"'),
  filter: M('M2.5 3h11l-4.3 5v4.6L6.8 14V8L2.5 3Z', 'fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"'),
  props: M('M9.5 1.5a4 4 0 0 0-3.9 4.9L1.4 10.6a1.4 1.4 0 0 0 0 2l2 2a1.4 1.4 0 0 0 2 0l4.2-4.2A4 4 0 0 0 14.5 5c0-.5-.1-1-.3-1.5l-2.5 2.5-1.7-.5-.5-1.7L12 1.8c-.4-.2-1-.3-2.5-.3Z', 'fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"'),
  trash: M('M6 1.5h4l.4 1H14v1.4H2V2.5h3.6L6 1.5ZM3.5 5h9l-.7 9.1a1 1 0 0 1-1 .9H5.2a1 1 0 0 1-1-.9L3.5 5Zm3 1.8v6h1.1v-6H6.5Zm2 0v6h1.1v-6H8.5Z', 'fill="currentColor"'),
  check: M('M6.2 11.4 2.8 8l-1 1 4.4 4.4L14.2 5.4l-1-1-7 7Z', 'fill="currentColor"'),
  close: M('M3.4 2.3 8 6.9l4.6-4.6 1.1 1.1L9.1 8l4.6 4.6-1.1 1.1L8 9.1l-4.6 4.6-1.1-1.1L6.9 8 2.3 3.4l1.1-1.1Z', 'fill="currentColor"'),
  refresh: M('8 2.5a5.5 5.5 0 0 1 5.3 4l-1.4.4A4.1 4.1 0 0 0 8 3.9 4.1 4.1 0 1 0 11 11l1 1A5.5 5.5 0 1 1 8 2.5Zm5 .1V6h-3.4L13 2.6Z', 'fill="currentColor"'),
  'chev-r': M('M5.8 2.6 11.2 8l-5.4 5.4-1-1L9.2 8 4.8 3.6l1-1Z', 'fill="currentColor"'),
  'chev-d': M('M2.6 5.8 8 11.2l5.4-5.4-1-1L8 9.2 3.6 4.8l-1 1Z', 'fill="currentColor"'),
  'chev-u': M('M2.6 10.2 8 4.8l5.4 5.4-1 1L8 6.8l-4.4 4.4-1-1Z', 'fill="currentColor"'),
  'chev-l': M('M10.2 2.6 4.8 8l5.4 5.4 1-1L6.8 8l4.4-4.4-1-1Z', 'fill="currentColor"'),
  search: M('M6.5 2a4.5 4.5 0 0 1 3.6 7.2l3.8 3.8-1 1-3.8-3.8A4.5 4.5 0 1 1 6.5 2Zm0 1.4a3.1 3.1 0 1 0 0 6.2 3.1 3.1 0 0 0 0-6.2Z', 'fill="currentColor"'),
  info: M('M8 1.5A6.5 6.5 0 1 1 8 14.5 6.5 6.5 0 0 1 8 1.5Zm0 1.3a5.2 5.2 0 1 0 0 10.4 5.2 5.2 0 0 1 0-10.4ZM8 6.8c.4 0 .7.3.7.7v3.2a.7.7 0 1 1-1.4 0V7.5c0-.4.3-.7.7-.7Zm0-2.6a.9.9 0 1 1 0 1.8.9.9 0 0 1 0-1.8Z', 'fill="currentColor"'),
  warn: M('M8 1.8 15 14H1L8 1.8Zm0 2.6L3.4 12.6h9.2L8 4.4Zm-.7 2.4h1.4v3.4H7.3V6.8Zm.7 3.8a.9.9 0 1 1 0 1.8.9.9 0 0 1 0-1.8Z', 'fill="currentColor"'),
  question: M('M8 1.5A6.5 6.5 0 1 1 8 14.5 6.5 6.5 0 0 1 8 1.5Zm0 1.3a5.2 5.2 0 1 0 0 10.4A5.2 5.2 0 0 0 8 2.8Zm0 1.7c1.3 0 2.4 1 2.4 2.3 0 .9-.5 1.4-1.1 1.9-.4.3-.6.5-.6.9v.3H7.3V9.8c0-1 .5-1.5 1.1-2 .4-.3.6-.5.6-.8 0-.6-.5-1-1-1s-1 .4-1 1H5.6C5.6 5.5 6.7 4.5 8 4.5Zm-.7 6.4h1.4v1.4H7.3v-1.4Z', 'fill="currentColor"'),
  power: M('M8 1.8c.4 0 .7.3.7.7v5.4a.7.7 0 1 1-1.4 0V2.5c0-.4.3-.7.7-.7ZM4.6 3.6l.9 1A4.8 4.8 0 1 0 12.7 8c0-1.3-.5-2.5-1.4-3.4l.9-1A6.1 6.1 0 1 1 4.6 3.6Z', 'fill="currentColor"'),
  settings: M('M8 5.2A2.8 2.8 0 1 0 8 10.8 2.8 2.8 0 0 0 8 5.2Z', 'fill="currentColor"') + M('M6.6 1.6h2.8l.3 1.8 1.5.9 1.7-.7 1.4 2.4-1.4 1.2v1.6l1.4 1.2-1.4 2.4-1.7-.7-1.5.9-.3 1.8H6.6l-.3-1.8-1.5-.9-1.7.7-1.4-2.4L3.1 9.6V8L1.7 6.8l1.4-2.4 1.7.7 1.5-.9.3-1.8ZM8 4.6A3.4 3.4 0 1 0 8 11.4 3.4 3.4 0 0 0 8 4.6Z', 'fill="none" stroke="currentColor" stroke-width="1.1"'),
  fullscreen: M('M2 2h5v1.4H3.4V7H2V2Zm7 0h5v5h-1.4V3.4H9V2ZM2 9h1.4v3.6H7V14H2V9Zm12 0v5H9v-1.4h3.6V9H14Z', 'fill="currentColor"'),
  exit: M('M6.5 1.5h6.2c.5 0 .8.4.8.9v11.2c0 .5-.3.9-.8.9H6.5v-1.4h5.6V2.9H6.5V1.5Zm.6 4.1L9.4 8 7.1 10.4l-1-1L7.4 8 6.1 6.6l1-1ZM2 7.3h5v1.4H2V7.3Z', 'fill="currentColor"'),
  copy: M('M5.5 1.5h7a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1Zm.4 1.4v6.2h6.2V2.9H5.9ZM3 5v8.5h6V15H2.5a1 1 0 0 1-1-1V5H3Z', 'fill="currentColor"'),
  save: M('M2.5 2.5h9L14 5v8.5h-11.5V2.5ZM4 4v3h7V4H4Zm0 5v4h8V9H4Z', 'fill="none" stroke="currentColor" stroke-width="1.2"'),
  scissors: M('M4 1.5 12.4 10l1.5-1.4-8.4-8.6L4 1.5Zm-1 9.2a2.4 2.4 0 1 0 2.1 4.1l3.2-3.1-1-1-3.2 3.1a1 1 0 0 1-1.1-1.1Zm9.5 0a2.4 2.4 0 1 0 .1 4.1 2.4 2.4 0 0 0-.1-4.1Zm-1.9-9.2-3.5 3.6 1 1 3.5-3.6-1-1Z', 'fill="currentColor"'),
  camera: M('M2.5 4.5h2.2l1-1.5h4.6l1 1.5h2.2c.4 0 .8.3.8.8v7c0 .4-.4.7-.8.7H2.5a.8.8 0 0 1-.8-.7v-7c0-.5.4-.8.8-.8ZM8 6.2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm0 1.4a1.6 1.6 0 1 1 0 3.2 1.6 1.6 0 0 1 0-3.2Z', 'fill="currentColor"'),
  transition: M('M2.5 3.5h11v9h-11v-9Zm1.4 1.4v6.2h8.2V4.9H3.9Z', 'fill="none" stroke="currentColor" stroke-width="1.2') + M('M6 6.2 9.8 8 6 9.8V6.2Z', 'fill="currentColor"'),
  studio: M('M1.5 3h6v10h-6V3Zm7 0h6v10h-6V3ZM2.9 4.4v7.2h3.2V4.4H2.9Zm7 0v7.2h3.2V4.4H9.9Z', 'fill="currentColor"'),
  wrench: M('M9.5 1.5a4 4 0 0 0-3.9 4.9L1.4 10.6a1.4 1.4 0 0 0 0 2l2 2a1.4 1.4 0 0 0 2 0l4.2-4.2A4 4 0 0 0 14.5 5c0-.5-.1-1-.3-1.5l-2.5 2.5-1.7-.5-.5-1.7L12 1.8c-.4-.2-1-.3-2.5-.3Z', 'fill="none" stroke="currentColor" stroke-width="1.2"'),
  keyboard: M('M1.5 4h13v8h-13V4Zm1.4 1.4v5.2h10.2V5.4H2.9Zm1 1h1.2v1.2H3.9V6.4Zm2.4 0h1.2v1.2H6.3V6.4Zm2.4 0h1.2v1.2H8.7V6.4Zm2.4 0h1.2v1.2h-1.2V6.4Zm-7.2 2.4h1.2v1.2H3.9V8.8Zm2.4 0h4.8v1.2H6.3V8.8Zm6 0h1.2v1.2h-1.2V8.8Z', 'fill="currentColor"'),
  person: M('M8 1.8a3 3 0 1 1 0 6 3 3 0 0 1 0-6Zm0 7.2c3 0 5.5 1.8 5.5 4v1.2h-11v-1.2c0-2.2 2.5-4 5.5-4Z', 'fill="currentColor"'),
  sliders: M('M3 2v4.2a2 2 0 0 0 0 3.6V14h1.4V9.8a2 2 0 0 0 0-3.6V2H3Zm4.3 0v7.2a2 2 0 0 0 0 3.6V14h1.4v-1.2a2 2 0 0 0 0-3.6V2H7.3Zm4.3 0v2.2a2 2 0 0 0 0 3.6V14H13V7.8a2 2 0 0 0 0-3.6V2h-1.4Z', 'fill="currentColor"'),
  video: M('M1.5 4h9.5v8H1.5V4Zm11 2.2 2.5-1.7v7l-2.5-1.7V6.2Z', 'fill="currentColor"'),
  audio: M('M8 1.8a3.2 3.2 0 0 1 3.2 3.2v2.5a3.2 3.2 0 1 1-6.4 0V5A3.2 3.2 0 0 1 8 1.8ZM3.9 7.5h1.4A2.7 2.7 0 0 0 8 10.2 2.7 2.7 0 0 0 10.7 7.5h1.4A4.1 4.1 0 0 1 8.7 11.4v1.7h2v1.4H5.3v-1.4h2v-1.7A4.1 4.1 0 0 1 3.9 7.5Z', 'fill="currentColor"'),
  monitor: M('M1.5 2.5h13v9h-13v-9Zm1.4 1.4v6.2h10.2V3.9H2.9ZM5.5 12.5h5V14h-5v-1.5Z', 'fill="currentColor"'),
  broadcast: M('M8 5.5a1.7 1.7 0 1 1 0 3.4 1.7 1.7 0 0 1 0-3.4Zm-3.2-1.7.9 1a3.9 3.9 0 0 0 0 6.4l-.9 1a5.2 5.2 0 0 1 0-8.4Zm6.4 0a5.2 5.2 0 0 1 0 8.4l-.9-1a3.9 3.9 0 0 0 0-6.4l.9-1ZM3 2l.9 1a6.6 6.6 0 0 0 0 10L3 14a7.9 7.9 0 0 1 0-12Zm10 0a7.9 7.9 0 0 1 0 12l-.9-1a6.6 6.6 0 0 0 0-10L13 2Z', 'fill="currentColor"'),
  record: M('M8 2.5A5.5 5.5 0 1 1 8 13.5 5.5 5.5 0 0 1 8 2.5Zm0 1.4a4.1 4.1 0 1 0 0 8.2 4.1 4.1 0 0 0 0-8.2Z', 'fill="currentColor"'),
  replay: M('M8 2.5a5.5 5.5 0 1 1-5.3 7l1.4-.4A4.1 4.1 0 1 0 8 3.9c-1.2 0-2.3.5-3 1.3L6.6 6.8H2.5V2.7L4 4.2A5.5 5.5 0 0 1 8 2.5Z', 'fill="currentColor"'),
  play: M('M4.5 2.5 13 8l-8.5 5.5v-11Z', 'fill="currentColor"'),
  pause: M('M4 2.5h2.6v11H4v-11Zm5.4 0H12v11H9.4v-11Z', 'fill="currentColor"'),
  stop: M('M3.5 3.5h9v9h-9v-9Z', 'fill="currentColor"'),
  plug: M('M5.5 1.5V5h5V1.5H12V5h1v3a4.2 4.2 0 0 1-3.5 4.1V15H8V12.1A4.2 4.2 0 0 1 4.5 8V5h1V1.5Z', 'fill="currentColor"'),
  folder: M('M1.5 3h5l1.2 1.5h6.8v8.5h-13V3Z', 'fill="none" stroke="currentColor" stroke-width="1.2"'),
  windows: M('M2 2.5h5.2v5.2H2V2.5Zm6.8 0H14v5.2H8.8V2.5ZM2 8.3h5.2v5.2H2V8.3Zm6.8 0H14v5.2H8.8V8.3Z', 'fill="currentColor"'),
  dot: M('M8 4.5A3.5 3.5 0 1 1 8 11.5 3.5 3.5 0 0 1 8 4.5Z', 'fill="currentColor"'),
  browser: M('M1.5 2.5h13v11h-13v-11Zm1.4 1.4v2.2h10.2V3.9H2.9Zm0 3.6v4.6h10.2V7.5H2.9Z', 'fill="none" stroke="currentColor" stroke-width="1.1'),
  globe: M('M8 1.5a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13Zm0 1.3c-.8 0-1.8 1.4-2.2 3.5h4.4C9.8 4.2 8.8 2.8 8 2.8ZM4.4 6.3c-.2.5-.3 1.1-.4 1.7h1.7c0-.6.1-1.2.2-1.7H4.4Zm2.9 0c-.1.5-.2 1.1-.2 1.7h1.8c0-.6-.1-1.2-.2-1.7H7.3Zm3.2 0c.1.5.2 1.1.2 1.7h1.7c-.1-.6-.2-1.2-.4-1.7h-1.5ZM2.8 9.4c.1.6.2 1.2.4 1.7h1.5c-.1-.5-.2-1.1-.2-1.7H2.8Zm3.1 0c0 .6.1 1.2.2 1.7h1.6c.1-.5.2-1.1.2-1.7H5.9Zm3.4 0c0 .6-.1 1.2-.2 1.7h1.5c.2-.5.3-1.1.4-1.7H9.3Zm-4.5 3.1c.4.7 1 1.3 1.7 1.6-.2-.5-.4-1-.5-1.6H4.8Zm2.7 0c.1.6.3 1.2.5 1.6.3-.1.5-.3.7-.5l-.3-1.1h-.9Zm2.4 0c-.1.6-.3 1.1-.5 1.6.7-.3 1.3-.9 1.7-1.6H9.9Zm2.9 0c.2-.5.3-1.1.4-1.7h-1.7c0 .6-.1 1.2-.2 1.7h1.5ZM2.8 6.3h1.7c0-.6.1-1.2.2-1.7H4.8c-.9.4-1.6 1-2 1.7Z', 'fill="currentColor"'),
};

/* Colored source-type icons (16x16, two-tone) */
const src = {
  display: `<rect x="1.5" y="2.5" width="13" height="9" rx="1" fill="#3f8cff"/><rect x="2.5" y="3.5" width="11" height="7" rx=".5" fill="#7db4ff"/><rect x="6" y="12" width="4" height="1.6" rx=".4" fill="#3f8cff"/><rect x="4.5" y="13.6" width="7" height="1.2" rx=".4" fill="#3f8cff"/>`,
  window: `<rect x="1.5" y="3.5" width="13" height="9.5" rx="1" fill="#5a5a5e" stroke="#77787c"/><rect x="1.5" y="3.5" width="13" height="2.2" rx="1" fill="#3f8cff"/><rect x="2.6" y="6.9" width="5" height="4.6" fill="#c8cad0"/><rect x="8.6" y="6.9" width="4.8" height="4.6" fill="#9a9ca2"/>`,
  game: `<path d="M4.2 4.5h7.6c1.7 0 3 1.4 2.9 3.1l-.2 2.8a1.9 1.9 0 0 1-3.3 1.2L9.9 10.5H6.1l-1.3 1.1a1.9 1.9 0 0 1-3.3-1.2l-.2-2.8c-.1-1.7 1.2-3.1 2.9-3.1Z" fill="#7a8cff"/><rect x="4.2" y="6.4" width="2.8" height="1" rx=".5" fill="#fff"/><rect x="5.1" y="5.5" width="1" height="2.8" rx=".5" fill="#fff"/><circle cx="10.8" cy="6.3" r=".8" fill="#fff"/><circle cx="12.2" cy="7.8" r=".8" fill="#fff"/>`,
  image: `<rect x="1.5" y="2.5" width="13" height="11" rx="1" fill="#2ebd4e"/><circle cx="5" cy="5.8" r="1.3" fill="#ffe45c"/><path d="M2.5 12.5 6.5 8l3 3.4 2-2.2 2.5 3.3H2.5Z" fill="#1d8f3a"/>`,
  slideshow: `<rect x="1.5" y="2.5" width="10" height="8" rx="1" fill="#2ebd4e"/><rect x="4.5" y="5.5" width="10" height="8" rx="1" fill="#26a344" stroke="#171718"/><circle cx="7.5" cy="8" r="1" fill="#ffe45c"/><path d="M5.5 12.5 8.5 9.5l2 2.3 1.5-1.7 1.7 2.4h-8.2Z" fill="#1d8f3a"/>`,
  color: `<rect x="1.5" y="2.5" width="13" height="11" rx="1" fill="#f0f0f0" stroke="#8b8d92"/><circle cx="5" cy="6" r="1.4" fill="#e04b4b"/><circle cx="8.5" cy="5" r="1.4" fill="#ffd93b"/><circle cx="11" cy="7.5" r="1.4" fill="#3f8cff"/><circle cx="6.5" cy="10" r="1.4" fill="#2ebd4e"/>`,
  text: `<rect x="1.5" y="2.5" width="13" height="11" rx="1" fill="#f0f0f0" stroke="#8b8d92"/><path d="M4 5h8v1.6H8.8V12H7.2V6.6H4V5Z" fill="#333"/>`,
  media: `<rect x="1.5" y="2.5" width="13" height="11" rx="1" fill="#7a57d1"/><path d="M6.5 5.5 10.8 8 6.5 10.5v-5Z" fill="#fff"/>`,
  vlc: `<path d="M8 2c1.4 0 2.2.8 2.2.8l-.7 2.7c1.6.5 2.9 1.6 3.3 3 .3 1.4-1.1 2-3 .2-.4 1.4-1 2.8-1.8 2.8s-1.4-1.4-1.8-2.8c-1.9 1.8-3.3 1.2-3-.2.4-1.4 1.7-2.5 3.3-3L5.8 2.8S6.6 2 8 2Z" fill="#e08a2e"/>`,
  browser: `<circle cx="8" cy="8" r="6.2" fill="none" stroke="#3f8cff" stroke-width="1.3"/><path d="M8 1.8c-1.6 0-2.8 2.7-2.8 6.2s1.2 6.2 2.8 6.2 2.8-2.7 2.8-6.2S9.6 1.8 8 1.8Zm0 1.2c.7 0 1.6 2.2 1.6 5s-.9 5-1.6 5-1.6-2.2-1.6-5 .9-5 1.6-5Z" fill="#3f8cff"/><path d="M2.2 6.3h11.6M2.2 9.7h11.6" stroke="#3f8cff" stroke-width="1.1"/>`,
  mic: `<rect x="6.2" y="1.5" width="3.6" height="7" rx="1.8" fill="#e0559a"/><path d="M4.2 7.3A3.8 3.8 0 0 0 8 11.1a3.8 3.8 0 0 0 3.8-3.8h1.4A5.2 5.2 0 0 1 8.7 12.3V14H11v1.4H5V14h2.3v-1.7A5.2 5.2 0 0 1 2.8 7.3h1.4Z" fill="#c23f80"/>`,
  speaker: `<path d="M9 2v12c0 .6-.7.9-1.1.5L5.2 12H2.8a.8.8 0 0 1-.8-.8V4.8c0-.4.4-.8.8-.8h2.4l2.7-2.5C8.3 1.1 9 1.4 9 2Z" fill="#3f8cff"/><path d="M11.2 4.6a4.8 4.8 0 0 1 0 6.8l-1-1a3.4 3.4 0 0 0 0-4.8l1-1Z" fill="#77aef7"/>`,
  headphones: `<path d="M8 2a5.2 5.2 0 0 1 5.2 5.2V13a1 1 0 0 1-1 1h-1.6v-5.4h1.2v-1.4A3.8 3.8 0 0 0 8 3.4 3.8 3.8 0 0 0 4.2 6.2v1.4h1.2V14H3.8a1 1 0 0 1-1-1V7.2A5.2 5.2 0 0 1 8 2Z" fill="#2ebd4e"/>`,
  app: `<rect x="1.5" y="2.5" width="13" height="11" rx="1" fill="none" stroke="#3f8cff" stroke-width="1.2"/><rect x="1.5" y="2.5" width="13" height="2.4" rx="1" fill="#3f8cff"/><path d="M4 8h3.5M4 10h5" stroke="#3f8cff" stroke-width="1.1"/>`,
  group: `<rect x="1.5" y="2.5" width="7" height="6" rx="1" fill="#b06fd4"/><rect x="7.5" y="7.5" width="7" height="6" rx="1" fill="#8a4bb0"/>`,
  scene: `<rect x="1.5" y="3" width="13" height="10" rx="1.2" fill="#c9a13f"/><path d="M1.5 3l2.5-1.5 2 2.5-2 1-2.5-2Zm4.5 1 2.5-1.5 2 2.5-2 1-2.5-2Zm4.5 1L13 3.5l1.5 2-2 1-1.5-1.5Z" fill="#a3822f"/><rect x="2.8" y="7" width="10.4" height="4.8" rx=".6" fill="#e8c766"/>`,
  script: `<path d="M4 1.5h6l3 3v10H4v-13Z" fill="#f0f0f0" stroke="#8b8d92"/><path d="M10 1.5v3h3" fill="none" stroke="#8b8d92"/><path d="M6 7.5 8 9l-2 1.5M9 11h2" stroke="#2ebd4e" stroke-width="1.2" fill="none"/>`,
  audioLine: `<path d="M2 9h2l1.5-4 2 8 2-10 1.5 6h3" stroke="#2ebd4e" stroke-width="1.3" fill="none"/>`,
};

export function I(name, cls = '') {
  const body = mono[name];
  if (body) return `<svg viewBox="0 0 16 16" class="${cls}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`;
  if (src[name]) return `<svg viewBox="0 0 16 16" class="${cls}" xmlns="http://www.w3.org/2000/svg">${src[name]}</svg>`;
  return `<svg viewBox="0 0 16 16" class="${cls}" xmlns="http://www.w3.org/2000/svg">${mono.question}</svg>`;
}

/* OBS logo (simplified authentic mark) */
export function ObsLogo(size = 96) {
  return `<svg viewBox="0 0 100 100" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="46" fill="#1b1b1d" stroke="#3c3c40" stroke-width="2"/>
  <path d="M50 18c9 0 16.5 6 18.8 14.2 5.8 3 9.8 9 9.8 16 0 2.2-.4 4.3-1.1 6.2a19 19 0 0 1-16.2 11.3l3.6-9.2a10.6 10.6 0 0 0 4.7-8.3c0-4.4-2.7-8.2-6.5-9.8A19 19 0 0 0 50 33a19 19 0 0 0-13.1 5.4c-3.8 1.6-6.5 5.4-6.5 9.8 0 3.5 1.8 6.6 4.7 8.3l3.6 9.2a19 19 0 0 1-16.2-11.3 17.4 17.4 0 0 1-1.1-6.2c0-7 4-13 9.8-16C33.5 24 41 18 50 18Z" fill="#f0f0f2"/>
  <circle cx="50" cy="54" r="7.4" fill="#f0f0f2"/>
  <path d="M46 68h8l-4 14-4-14Z" fill="#f0f0f2"/>
  <path d="M38.5 66.5 34 78l8.5-5.5-4-6Zm23 0L66 78l-8.5-5.5 4-6Z" fill="#f0f0f2"/>
</svg>`;
}

export const SOURCE_ICON = {
  display_capture: 'display', window_capture: 'window', game_capture: 'game',
  image: 'image', image_slideshow: 'slideshow', color_source: 'color',
  text: 'text', media_source: 'media', vlc_source: 'vlc', browser_source: 'browser',
  audio_input_capture: 'mic', audio_output_capture: 'speaker', application_audio_capture: 'headphones',
  group: 'group', scene: 'scene', wasapi_process_output_capture: 'app',
  monitor_capture: 'display',
};

export default { I, ObsLogo, SOURCE_ICON };
