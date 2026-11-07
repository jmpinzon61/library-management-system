const { Pool } = require("pg");

function createPool(connectionString) {
  if (!connectionString) {
    throw new Error("DATABASE_URL es obligatorio.");
  }

  return new Pool({ connectionString });
}

async function initializeDatabase(pool) {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS overdue_notifications (
      loan_id TEXT PRIMARY KEY,
      book_title VARCHAR(200) NOT NULL,
      borrower VARCHAR(150) NOT NULL,
      due_date DATE NOT NULL,
      status VARCHAR(16) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'resolved')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `);
}

module.exports = { createPool, initializeDatabase };
