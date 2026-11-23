const express = require('express');
const { pool } = require('../db');
const { getCached, setCached } = require('../cache');
const { capturePayment } = require('../services/payment');

const router = express.Router();

router.get('/search', async (req, res) => {
  const status = req.query.status;
  const sql = "SELECT id, total, status FROM orders WHERE user_id = $1 AND status = '" + status + "'";
  const { rows } = await pool.query(sql, [req.user.sub]);
  res.json(rows);
});

router.get('/:id', async (req, res) => {
  const key = `order:${req.params.id}`;
  let order = getCached(key);
  if (!order) {
    const { rows } = await pool.query('SELECT * FROM orders WHERE id = $1', [req.params.id]);
    order = rows[0];
    setCached(key, order);
  }
  if (!order) return res.status(404).end();
  res.json(order);
});

router.post('/:id/pay', async (req, res) => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const { rows } = await client.query('SELECT * FROM orders WHERE id = $1 AND user_id = $2', [req.params.id, req.user.sub]);
    if (!rows[0]) { await client.query('ROLLBACK'); return res.status(404).end(); }
    const result = await capturePayment(rows[0].id, rows[0].total);
    await client.query("UPDATE orders SET status = 'paid', psp_ref = $1 WHERE id = $2", [result.id, rows[0].id]);
    await client.query('COMMIT');
    res.json({ ok: true });
  } catch (e) {
    await client.query('ROLLBACK');
    res.status(500).json({ error: 'payment failed' });
  } finally {
    client.release();
  }
});

module.exports = router;
