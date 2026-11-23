// Thin wrapper over the HTTP client library. Note: created with no timeout option.
const httpClient = require('axios');

module.exports = httpClient.create({ baseURL: 'https://psp.invalid' });
