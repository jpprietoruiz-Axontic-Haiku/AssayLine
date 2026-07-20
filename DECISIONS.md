# Decisiones de diseño

Notas de por qué el sistema está construido como está, no solo qué hace. Cada
sección es una decisión con su alternativa descartada y el motivo.

## 1. Tool-calling en vez de extracción directa (un solo prompt pidiendo JSON)

**Alternativa descartada:** un único prompt a un LLM con visión, "aquí tienes
el documento, devuélveme este JSON", parseando la respuesta a mano.

**Por qué no:** un LLM que solo genera texto no tiene forma de comprobar su
propio trabajo. Si convierte mal una unidad, o mira el spec range equivocado,
o suma mal dos valores de una tabla, el error queda enterrado en un blob de
JSON que parece perfectamente válido. No hay señal de que algo salió mal.

**Qué se hizo en su lugar:** el agente ([`app/services/extraction_agent.py`](worker/app/services/extraction_agent.py))
tiene acceso a herramientas deterministas —`convert_units`, `lookup_spec_profile`,
`calculate`— que ejecuta código Python real, no al modelo "razonando" aritmética
en su cabeza. El modelo decide *cuándo* usar cada herramienta y *cómo*
interpretar el resultado, pero el cálculo en sí es determinista y verificable.
Esto es exactamente la diferencia entre "el LLM adivina" y "el LLM orquesta
herramientas confiables". El resultado final se entrega a través de un tool
call de schema fijo (`submit_extraction`), no de texto libre parseado con
regex — el modelo no puede devolver un JSON mal formado porque la propia API
de tool-calling se lo impide.

## 2. Validación de esquema por campo, no del documento completo

**Alternativa descartada:** un único modelo Pydantic grande por tipo de
informe (`CertificateOfAnalysis(BaseModel): ph: float; pureza: float; ...`)
que se valida de una vez.

**Por qué no:** con validación "todo o nada", un solo campo mal extraído
(confidence fuera de rango, tipo incorrecto) tira todo el documento a la
papelera — incluidos los 9 campos que sí se extrajeron bien. Eso es peor que
inútil para un revisor humano: prefiere ver 9 campos correctos y 1 marcado
como sospechoso, no "extracción fallida, intenta de nuevo".

**Qué se hizo en su lugar:** [`app/schemas/extraction.py`](worker/app/schemas/extraction.py)
valida cada campo individualmente contra `ExtractedField`. Un campo inválido
se reporta en `validation_errors` con su motivo; el resto de campos válidos
se persiste igual. Esto es lo que permite que el dashboard muestre "3 de 4
campos extraídos, 1 con error de validación" en vez de fallar en bloque.

## 3. Confidence score por campo, generado por el propio modelo

El agente asigna una confianza (0–1) a cada campo que extrae, con instrucción
explícita de bajarla cuando el valor es ambiguo o inferido en vez de leído
directamente. No es una medida objetiva —es la propia autoevaluación del
modelo— pero es la señal más barata disponible para priorizar qué revisar
primero en el dashboard sin tener que releer todos los campos por igual.

## 4. Human-in-the-loop como parte central del flujo, no un añadido

**Por qué:** ningún pipeline de extracción con LLM es 100% fiable, y fingir
que lo es (auto-aprobando todo lo que devuelve el modelo) es la forma más
rápida de perder la confianza de alguien que trabaja con especificaciones de
proceso reales. Reconocer la incertidumbre — mostrar confidence, marcar
anomalías, dejar el documento original al lado del dato extraído para
comparar de un vistazo — es la propuesta de valor, no una limitación a
esconder.

Por eso `PATCH /reports/{id}/review` no es un endpoint secundario: es donde
vive la corrección real. Y al aprobar una revisión, el motor de anomalías se
**recalcula desde cero** contra los valores corregidos (no contra los
originales) — ver [`app/api/reports.py`](worker/app/api/reports.py), función
`review_report`. Si no se hiciera esto, una corrección humana que arregla un
valor fuera de spec dejaría el flag de anomalía "fantasma" en el sistema.

## 5. Clasificación determinista por keywords, no por LLM

El tipo de informe (`certificate_of_analysis` / `process_log`) se decide con
un matcher de regex sobre el texto transcrito
([`app/services/classifier.py`](worker/app/services/classifier.py)), no con
otra llamada al modelo. Es una decisión binaria/categórica de baja
ambigüedad sobre texto ya extraído — pedirle a un LLM que la resuelva sería
gastar latencia y tokens por algo que un `re.search` resuelve en microsegundos
y sin varianza. El LLM se reserva para donde realmente aporta: razonar sobre
tablas mal formadas, gráficas, y texto ambiguo durante la extracción de
campos.

## 6. OCR/visión condicional: solo cuando el PDF no trae texto embebido

`app/services/pipeline.py` intenta primero extraer el texto embebido de cada
página (PyMuPDF); solo si ese texto es sospechosamente corto
(`MIN_EMBEDDED_TEXT_CHARS`) llama a Claude vision para transcribir la imagen
de la página. La mayoría de certificados de análisis modernos se generan
digitalmente y ya traen una capa de texto perfecta — pagar tokens de visión
para volver a "leer" algo que ya es texto extraíble sería desperdiciar dinero
y latencia. La visión multimodal se reserva para lo que de verdad la necesita:
escaneos, fotos de operario, y gráficas.

## 7. Redis + RQ para la cola de jobs (vs. jobs respaldados en Postgres)

**Alternativa considerada:** una tabla `jobs` en Postgres con
`SELECT ... FOR UPDATE SKIP LOCKED`, evitando un servicio adicional.

**Por qué Redis+RQ igual:** el pipeline de un informe puede tardar (varias
llamadas a Claude, potencialmente varias páginas), así que reintentos,
timeouts de visibilidad y colas separadas por prioridad importan desde el
día uno — construir eso a mano sobre Postgres es reinventar RQ con más
código propio que mantener. Además, el target de despliegue (Railway) ya
provee Redis gestionado junto al worker, así que no es infraestructura extra
real, es la misma pieza que hacía falta de todos modos.

## 8. Alembic + SQLAlchemy como única fuente de verdad del schema

El hito 1 arrancó con una migración SQL escrita a mano. Se reemplazó en el
hito 2 por modelos SQLAlchemy ([`app/models/`](worker/app/models/)) + una
migración de Alembic generada a partir de ellos. Mantener el SQL y el ORM
como dos fuentes separadas garantiza que en algún momento diverjan
silenciosamente; con Alembic hay un solo lugar donde el schema vive y una
sola forma de evolucionarlo (`alembic revision` + `alembic upgrade`).

## 9. SQLite en tests, Postgres en producción

Los tests usan SQLite en archivo temporal (ver `worker/tests/conftest.py`)
en vez de levantar un Postgres real. Los modelos usan tipos genéricos de
SQLAlchemy (`Uuid`, `JSON().with_variant(JSONB, "postgresql")`) que se
comportan igual en ambos dialectos para lo que el código realmente usa
(CRUD + filtros simples, nada de funciones específicas de Postgres). El
trade-off consciente: se gana una suite de tests que corre en cualquier
máquina sin Docker, en segundos, sin estado compartido entre tests — a
cambio de no probar comportamiento Postgres-específico (constraints exactos,
locking) en CI. Para este proyecto, ese comportamiento se considera de bajo
riesgo frente al valor de tests rápidos y deterministas; la migración de
Alembic se verifica por separado en modo offline (`alembic upgrade head --sql`)
para confirmar que el DDL generado es válido para Postgres.

## 10. Severidad de anomalía por desviación relativa al ancho del rango

`app/services/anomaly_engine.py` clasifica una anomalía como `critical` si
el valor se desvía más de un 15% del ancho del rango spec (`max - min`), y
`warning` en caso contrario. Es una heurística de demo explícitamente
documentada como tal en el código — no pretende ser un criterio regulatorio.
La decisión de diseño real es que la severidad se calcule con una fórmula,
no con un LLM: es exactamente el tipo de comparación numérica donde un
modelo puede alucinar sutilmente, y donde una función pura es más barata,
más rápida y 100% auditable.

## 11. Unidades normalizadas antes de comparar contra spec

Si un campo extraído trae una unidad distinta a la del spec_profile
(`6000 mg` extraído vs. spec en `g`), el motor de anomalías convierte antes
de comparar (reutilizando la misma herramienta `convert_units` del agente de
extracción). Si la conversión no es posible (unidades de dimensiones
distintas), el campo se **omite** en vez de compararse a ciegas — un falso
"todo en orden" por comparar peras con manzanas es peor que no flaggear nada.

## 12. Datos de demo con extracción precomputada, no generados en vivo

Los 4 informes sintéticos de [`app/demo/data.py`](worker/app/demo/data.py)
traen su extracción ya resuelta a mano, no se re-extraen con el LLM cada vez
que se siembra la demo. Sembrar la demo es una operación que puede correr en
cualquier entorno (CI, onboarding de un nuevo dev, redeploy) — hacerla
depender de una API key de Anthropic y de tokens reales cada vez sería
frágil y con costo recurrente por nada. El motor de anomalías sí corre en
vivo contra esos datos (no está hardcodeado), así que la demo sigue
demostrando el pipeline real de comparación y flagging.

## 13. Almacenamiento de archivos: disco local, no object storage

`STORAGE_DIR` es un directorio local (montable como volumen persistente en
Railway). Para el alcance de este proyecto —un solo worker, sin necesidad de
escalar horizontalmente— añadir S3/R2 hubiera sido complejidad sin beneficio
inmediato. Si el proyecto necesitara múltiples workers o instancias
efímeras, esto es lo primero que migraría a object storage; `app/services/storage.py`
ya aísla todo el acceso a disco detrás de una interfaz pequeña, así que ese
cambio no debería tocar el resto del pipeline.

## 14. Qué falta para ser "producción de verdad" (limitaciones honestas)

- **Sin autenticación/autorización.** Cualquiera con la URL puede subir,
  revisar y exportar informes. Para un despliegue real haría falta al menos
  un login básico y, probablemente, scoping por organización.
- **Un solo worker RQ, sin dead-letter queue.** Un job que falla se marca
  `failed` en `reports.status` con el error en `error_message`, pero no hay
  reintentos automáticos ni alerta operativa.
- **El agente de extracción no soporta gráficas complejas de verdad.** El
  prompt de visión pide describir curvas/gráficas, pero no hay un caso de
  prueba end-to-end con una gráfica real extrayendo puntos numéricos — es la
  parte del blueprint original menos verificada.
- **Sin versionado de spec_profiles.** Si una especificación cambia, se
  edita la fila existente; no queda auditoría de "qué spec estaba vigente
  cuando se evaluó este informe".
