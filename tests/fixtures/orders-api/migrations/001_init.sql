CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  total FLOAT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  psp_ref TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
