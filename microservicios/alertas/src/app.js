const crypto = require("node:crypto");
const express = require("express");
const swaggerUi = require("swagger-ui-express");
const openapi = require("./openapi");

const asyncHandler = (handler) => (request, response, next) => {
  Promise.resolve(handler(request, response, next)).catch(next);
};

function equalToken(received, expected) {
  const receivedBytes = Buffer.from(received || "");
  const expectedBytes = Buffer.from(expected || "");
  return (
    receivedBytes.length === expectedBytes.length &&
    receivedBytes.length > 0 &&
    crypto.timingSafeEqual(receivedBytes, expectedBytes)
  );
}

function validLoan(loan) {
  const date = typeof loan?.dueDate === "string"
    ? new Date(`${loan.dueDate}T00:00:00Z`)
    : null;

  return (
    loan &&
    (typeof loan.loanId === "number" || typeof loan.loanId === "string") &&
    String(loan.loanId).length > 0 &&
    String(loan.loanId).length <= 64 &&
    typeof loan.bookTitle === "string" &&
    loan.bookTitle.trim().length > 0 &&
    loan.bookTitle.length <= 200 &&
    typeof loan.borrower === "string" &&
    loan.borrower.trim().length > 0 &&
    loan.borrower.length <= 150 &&
    typeof loan.dueDate === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(loan.dueDate) &&
    !Number.isNaN(date?.getTime()) &&
    date.toISOString().slice(0, 10) === loan.dueDate
  );
}

function validBook(book) {
  return (
    book &&
    Number.isInteger(book.id) &&
    typeof book.title === "string" &&
    book.title.trim().length > 0 &&
    book.title.length <= 200 &&
    typeof book.author === "string" &&
    book.author.trim().length > 0 &&
    book.author.length <= 100 &&
    Number.isInteger(book.year) &&
    book.year >= 1000 &&
    book.year <= 9999
  );
}

function createApp({ pool, token, ai }) {
  if (!pool || !token || !ai) {
    throw new Error("La aplicación requiere pool, token y handlers de IA.");
  }

  const app = express();
  app.disable("x-powered-by");
  app.use(express.json({ limit: "100kb" }));

  app.get("/", (_request, response) => {
    response.redirect("/docs");
  });
  app.get("/health", asyncHandler(async (_request, response) => {
    await pool.query("SELECT 1");
    response.json({ status: "ok", database: "ok" });
  }));
  app.get("/openapi.json", (_request, response) => {
    response.json(openapi);
  });
  app.use("/docs", swaggerUi.serve, swaggerUi.setup(openapi));

  const requireServiceToken = (request, response, next) => {
    const authorization = request.get("authorization") || "";
    const suppliedToken = authorization.startsWith("Bearer ")
      ? authorization.slice("Bearer ".length)
      : "";

    if (!equalToken(suppliedToken, token)) {
      return response.status(401).json({ error: "No autorizado." });
    }

    return next();
  };

  app.post(
    "/api/notifications/overdue/sync",
    requireServiceToken,
    asyncHandler(async (request, response) => {
      const loans = request.body?.loans;
      if (
        !Array.isArray(loans) ||
        loans.length > 500 ||
        !loans.every(validLoan)
      ) {
        return response.status(400).json({
          error: "Envía una lista válida de hasta 500 préstamos vencidos.",
        });
      }

      const client = await pool.connect();
      try {
        await client.query("BEGIN");
        for (const loan of loans) {
          await client.query(
            `INSERT INTO overdue_notifications
              (loan_id, book_title, borrower, due_date, status, updated_at)
             VALUES ($1, $2, $3, $4, 'open', NOW())
             ON CONFLICT (loan_id) DO UPDATE SET
               book_title = EXCLUDED.book_title,
               borrower = EXCLUDED.borrower,
               due_date = EXCLUDED.due_date,
               status = 'open',
               updated_at = NOW()`,
            [
              String(loan.loanId),
              loan.bookTitle.trim(),
              loan.borrower.trim(),
              loan.dueDate,
            ],
          );
        }

        if (loans.length) {
          await client.query(
            `UPDATE overdue_notifications
             SET status = 'resolved', updated_at = NOW()
             WHERE status = 'open' AND NOT (loan_id = ANY($1::text[]))`,
            [loans.map((loan) => String(loan.loanId))],
          );
        } else {
          await client.query(
            `UPDATE overdue_notifications
             SET status = 'resolved', updated_at = NOW()
             WHERE status = 'open'`,
          );
        }

        await client.query("COMMIT");
      } catch (error) {
        await client.query("ROLLBACK");
        throw error;
      } finally {
        client.release();
      }

      response.json({ synchronized: loans.length });
    }),
  );

  app.get(
    "/api/notifications/overdue",
    requireServiceToken,
    asyncHandler(async (_request, response) => {
      const result = await pool.query(
        `SELECT loan_id, book_title, borrower, due_date, status, created_at
         FROM overdue_notifications
         WHERE status = 'open'
         ORDER BY due_date ASC, loan_id ASC`,
      );
      response.json({
        notifications: result.rows.map((row) => ({
          loanId: row.loan_id,
          bookTitle: row.book_title,
          borrower: row.borrower,
          dueDate: row.due_date,
          status: row.status,
          createdAt: row.created_at,
        })),
      });
    }),
  );

  app.post(
    "/api/ai/recommendations",
    requireServiceToken,
    asyncHandler(async (request, response) => {
      const { question, catalog } = request.body || {};
      if (
        typeof question !== "string" ||
        !question.trim() ||
        question.length > 500 ||
        !Array.isArray(catalog) ||
        catalog.length > 100 ||
        !catalog.every(validBook)
      ) {
        return response.status(400).json({
          error: "Envía una pregunta y un catálogo válidos (máximo 100 libros).",
        });
      }

      const answer = await ai.recommend({
        question: question.trim(),
        catalog,
      });
      response.json({ answer });
    }),
  );

  app.post(
    "/api/ai/summaries",
    requireServiceToken,
    asyncHandler(async (request, response) => {
      const book = request.body?.book;
      if (!validBook(book)) {
        return response.status(400).json({
          error: "Los metadatos del libro no son válidos.",
        });
      }

      const summary = await ai.summarize({ book });
      response.json({ summary });
    }),
  );

  app.use((error, _request, response, _next) => {
    if (error?.type === "entity.parse.failed") {
      return response.status(400).json({ error: "El cuerpo JSON no es válido." });
    }

    if (error.status && error.status < 500) {
      return response.status(error.status).json({ error: error.message });
    }

    console.error("Fallo procesando una solicitud del microservicio:", error);
    return response.status(error.status || 500).json({
      error: error.status ? error.message : "Error interno del microservicio.",
    });
  });

  return app;
}

module.exports = { createApp };
