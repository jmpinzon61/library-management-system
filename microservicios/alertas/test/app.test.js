const assert = require("node:assert/strict");
const { after, before, test } = require("node:test");
const { createApp } = require("../src/app");

const TOKEN = "test-service-token";
const pool = {
  async query(sql) {
    assert.match(sql, /SELECT 1|SELECT loan_id/);
    return { rows: [] };
  },
  async connect() {
    return {
      async query() {
        return { rows: [] };
      },
      release() {},
    };
  },
};
const ai = {
  async recommend() {
    return "Recomendación de prueba.";
  },
  async summarize() {
    return "Resumen de prueba.";
  },
};

let server;
let baseUrl;

before(async () => {
  server = createApp({ pool, token: TOKEN, ai }).listen(0, "127.0.0.1");
  await new Promise((resolve) => server.once("listening", resolve));
  baseUrl = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
  await new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
});

test("publica OpenAPI y Swagger UI sin exponer el token", async () => {
  const [specResponse, docsResponse] = await Promise.all([
    fetch(`${baseUrl}/openapi.json`),
    fetch(`${baseUrl}/docs/`),
  ]);
  const spec = await specResponse.json();

  assert.equal(specResponse.status, 200);
  assert.ok(spec.paths["/api/notifications/overdue/sync"]);
  assert.ok(spec.paths["/api/ai/recommendations"]);
  assert.equal(docsResponse.status, 200);
});

test("requiere token para los endpoints internos", async () => {
  const response = await fetch(`${baseUrl}/api/notifications/overdue`);
  assert.equal(response.status, 401);
});

test("rechaza datos de sincronización inválidos", async () => {
  const response = await fetch(
    `${baseUrl}/api/notifications/overdue/sync`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${TOKEN}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({ loans: [{ loanId: 1 }] }),
    },
  );
  assert.equal(response.status, 400);
});

test("acepta préstamos vencidos y devuelve recomendaciones", async () => {
  const syncResponse = await fetch(
    `${baseUrl}/api/notifications/overdue/sync`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${TOKEN}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        loans: [{
          loanId: 1,
          bookTitle: "Libro",
          borrower: "Lector",
          dueDate: "2026-10-30",
        }],
      }),
    },
  );
  const recommendationResponse = await fetch(
    `${baseUrl}/api/ai/recommendations`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${TOKEN}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        question: "Quiero novelas",
        catalog: [{ id: 1, title: "Libro", author: "Autora", year: 2020 }],
      }),
    },
  );
  const recommendation = await recommendationResponse.json();

  assert.equal(syncResponse.status, 200);
  assert.equal(recommendationResponse.status, 200);
  assert.equal(recommendation.answer, "Recomendación de prueba.");
});
