const express = require('express');
const { requireAuth } = require('./middleware/auth');
const orders = require('./routes/orders');

const app = express();
app.use(express.json({ limit: '1mb' }));
app.get('/health', (req, res) => res.json({ ok: true }));
app.use('/orders', requireAuth, orders);

app.listen(process.env.PORT || 3000);
