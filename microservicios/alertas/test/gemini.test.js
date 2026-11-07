const assert = require("node:assert/strict");
const { test } = require("node:test");
const { createAiHandlers } = require("../src/gemini");

test("envía la solicitud de texto a Gemini usando la API key en un header", async (t) => {
  const originalFetch = global.fetch;
  let requestUrl;
  let requestOptions;
  global.fetch = async (url, options) => {
    requestUrl = url;
    requestOptions = options;
    return new Response(
      JSON.stringify({
        candidates: [{ content: { parts: [{ text: "Respuesta de prueba" }] } }],
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  };
  t.after(() => {
    global.fetch = originalFetch;
  });

  const ai = createAiHandlers("test-api-key");
  const answer = await ai.recommend({
    question: "Novelas colombianas",
    catalog: [],
  });

  assert.equal(answer, "Respuesta de prueba");
  assert.match(requestUrl, /gemini-3\.1-flash-lite:generateContent$/);
  assert.equal(requestOptions.headers["x-goog-api-key"], "test-api-key");
  assert.equal(new URL(requestUrl).search, "");
});

test("informa cuando falta la clave de Gemini", async () => {
  const ai = createAiHandlers("");

  await assert.rejects(
    ai.summarize({ book: { title: "Libro" } }),
    (error) => error.status === 503,
  );
});
