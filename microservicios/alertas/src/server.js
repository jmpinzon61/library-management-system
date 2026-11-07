const { createApp } = require("./app");
const { createPool, initializeDatabase } = require("./database");
const { createAiHandlers } = require("./gemini");

async function start() {
  const token = process.env.NODE_SERVICE_TOKEN;
  if (!token || token.length < 32) {
    throw new Error("NODE_SERVICE_TOKEN debe tener al menos 32 caracteres.");
  }

  const pool = createPool(process.env.DATABASE_URL);
  await initializeDatabase(pool);

  const app = createApp({
    pool,
    token,
    ai: createAiHandlers(process.env.GEMINI_API_KEY),
  });
  const port = Number(process.env.PORT || 3000);
  const server = app.listen(port, "0.0.0.0", () => {
    console.log(`Microservicio disponible en el puerto ${port}.`);
  });

  const shutdown = () => {
    server.close(async () => {
      await pool.end();
      process.exit(0);
    });
  };
  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);
}

start().catch((error) => {
  console.error("No se pudo iniciar el microservicio:", error.message);
  process.exitCode = 1;
});
