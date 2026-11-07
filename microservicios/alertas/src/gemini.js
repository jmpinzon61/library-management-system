const MODEL = "gemini-3.1-flash-lite";
const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`;

async function generateText(prompt, apiKey) {
  if (!apiKey) {
    const error = new Error("La integración con Gemini no está configurada.");
    error.status = 503;
    throw error;
  }

  let response;
  try {
    response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-goog-api-key": apiKey,
      },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { maxOutputTokens: 700, temperature: 0.4 },
      }),
      signal: AbortSignal.timeout(25000),
    });
  } catch (error) {
    const serviceError = new Error("No fue posible comunicarse con Gemini.");
    serviceError.status = 502;
    throw serviceError;
  }

  if (!response.ok) {
    const error = new Error("El proveedor de IA no pudo completar la solicitud.");
    error.status = response.status === 429 ? 503 : 502;
    throw error;
  }

  const result = await response.json();
  const text = result.candidates?.[0]?.content?.parts
    ?.map((part) => part.text || "")
    .join("")
    .trim();

  if (!text) {
    const error = new Error("El proveedor de IA devolvió una respuesta vacía.");
    error.status = 502;
    throw error;
  }

  return text;
}

function createAiHandlers(apiKey) {
  return {
    async recommend({ question, catalog }) {
      const prompt = [
        "Eres un asistente bibliotecario. Responde en español.",
        "Recomienda únicamente libros incluidos en el catálogo JSON.",
        "No inventes títulos, autores ni datos. Cita el ID de cada libro recomendado.",
        "Si no hay coincidencias, dilo con claridad y pide una preferencia más específica.",
        `Catálogo: ${JSON.stringify(catalog)}`,
        `Solicitud del lector: ${question}`,
      ].join("\n\n");
      return generateText(prompt, apiKey);
    },
    async summarize({ book }) {
      const prompt = [
        "Responde en español con un resumen bibliográfico breve de un libro.",
        "Solo recibes metadatos de catálogo; no afirmes que has leído el texto.",
        "Si no conoces con confianza la obra, explica que no hay suficiente información",
        "para resumir su contenido y limita la respuesta a los metadatos recibidos.",
        "Identifica la respuesta como generada por IA y recomienda verificarla.",
        `Metadatos: ${JSON.stringify(book)}`,
      ].join("\n");
      return generateText(prompt, apiKey);
    },
  };
}

module.exports = { createAiHandlers };
