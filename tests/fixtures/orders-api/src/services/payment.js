const axios = require('axios');

async function capturePayment(orderId, amount) {
  const res = await axios.post(`${process.env.PSP_URL}/captures`, {
    reference: orderId,
    amount,
  });
  return res.data;
}

module.exports = { capturePayment };
