const axios = require('axios');
const { PSP_BASE_URL } = require('../config');

async function capturePayment(orderId, amount) {
  const res = await axios.post(`${PSP_BASE_URL}/captures`, {
    reference: orderId,
    amount,
  });
  return res.data;
}

module.exports = { capturePayment };
