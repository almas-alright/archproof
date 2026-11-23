// Simple in-process cache for order lookups.
const cache = new Map();

function getCached(key) {
  return cache.get(key);
}

function setCached(key, value) {
  cache.set(key, value);
}

module.exports = { getCached, setCached };
