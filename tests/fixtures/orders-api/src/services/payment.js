const pspClient = require('./psp-client');
const { PSP_CAPTURE_PATH } = require('../config');

async function capturePayment(orderId, amount) {
  const res = await pspClient.post(PSP_CAPTURE_PATH, {
    reference: orderId,
    amount,
  });
  return res.data;
}

module.exports = { capturePayment };
