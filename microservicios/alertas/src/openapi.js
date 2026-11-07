const openapi = {
  openapi: "3.0.3",
  info: {
    title: "API de Biblioteca: alertas y asistencia",
    version: "1.0.0",
    description:
      "Microservicio Node.js para sincronizar alertas internas de préstamos vencidos y ofrecer asistencia bibliográfica con Gemini.",
  },
  servers: [{ url: "/", description: "Servidor actual" }],
  tags: [
    { name: "Sistema", description: "Estado del microservicio" },
    { name: "Alertas", description: "Alertas internas de vencimientos" },
    { name: "IA", description: "Recomendaciones y resúmenes bibliográficos" },
  ],
  paths: {
    "/health": {
      get: {
        tags: ["Sistema"],
        summary: "Verifica el servicio y la base de datos",
        responses: {
          200: {
            description: "Servicio disponible",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "string", example: "ok" },
                    database: { type: "string", example: "ok" },
                  },
                },
              },
            },
          },
          503: { description: "Base de datos no disponible" },
        },
      },
    },
    "/api/notifications/overdue/sync": {
      post: {
        tags: ["Alertas"],
        summary: "Sincroniza préstamos vencidos como alertas internas",
        description:
          "Operación idempotente llamada por Django. Los préstamos que dejan de estar vencidos se marcan como resueltos.",
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["loans"],
                properties: {
                  loans: {
                    type: "array",
                    items: { $ref: "#/components/schemas/OverdueLoan" },
                  },
                },
              },
              example: {
                loans: [
                  {
                    loanId: 42,
                    bookTitle: "Cien años de soledad",
                    borrower: "lector1",
                    dueDate: "2026-10-30",
                  },
                ],
              },
            },
          },
        },
        responses: {
          200: { description: "Alertas sincronizadas" },
          400: { description: "Datos de préstamos inválidos" },
          401: { description: "Token de servicio inválido" },
        },
      },
    },
    "/api/notifications/overdue": {
      get: {
        tags: ["Alertas"],
        summary: "Lista alertas internas abiertas",
        security: [{ bearerAuth: [] }],
        responses: {
          200: {
            description: "Alertas abiertas para Bibliotecarios y Administradores",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    notifications: {
                      type: "array",
                      items: { $ref: "#/components/schemas/OverdueNotification" },
                    },
                  },
                },
              },
            },
          },
          401: { description: "Token de servicio inválido" },
        },
      },
    },
    "/api/ai/recommendations": {
      post: {
        tags: ["IA"],
        summary: "Recomienda libros del catálogo",
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["question", "catalog"],
                properties: {
                  question: { type: "string", maxLength: 500 },
                  catalog: {
                    type: "array",
                    maxItems: 100,
                    items: { $ref: "#/components/schemas/CatalogBook" },
                  },
                },
              },
            },
          },
        },
        responses: {
          200: { description: "Recomendación generada" },
          401: { description: "Token de servicio inválido" },
          503: { description: "Servicio de IA no configurado o temporalmente limitado" },
        },
      },
    },
    "/api/ai/summaries": {
      post: {
        tags: ["IA"],
        summary: "Genera un resumen bibliográfico de un libro",
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["book"],
                properties: {
                  book: { $ref: "#/components/schemas/CatalogBook" },
                },
              },
            },
          },
        },
        responses: {
          200: { description: "Resumen bibliográfico generado" },
          401: { description: "Token de servicio inválido" },
          503: { description: "Servicio de IA no configurado o temporalmente limitado" },
        },
      },
    },
  },
  components: {
    securitySchemes: {
      bearerAuth: { type: "http", scheme: "bearer" },
    },
    schemas: {
      CatalogBook: {
        type: "object",
        required: ["id", "title", "author", "year"],
        properties: {
          id: { type: "integer", example: 1 },
          title: { type: "string", example: "Cien años de soledad" },
          author: { type: "string", example: "Gabriel García Márquez" },
          year: { type: "integer", example: 1967 },
        },
      },
      OverdueLoan: {
        type: "object",
        required: ["loanId", "bookTitle", "borrower", "dueDate"],
        properties: {
          loanId: { type: "string", example: "42" },
          bookTitle: { type: "string", example: "Cien años de soledad" },
          borrower: { type: "string", example: "lector1" },
          dueDate: { type: "string", format: "date", example: "2026-10-30" },
        },
      },
      OverdueNotification: {
        allOf: [
          { $ref: "#/components/schemas/OverdueLoan" },
          {
            type: "object",
            properties: {
              status: { type: "string", enum: ["open", "resolved"] },
              createdAt: { type: "string", format: "date-time" },
            },
          },
        ],
      },
    },
  },
};

module.exports = openapi;
