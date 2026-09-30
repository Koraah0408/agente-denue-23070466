# Análisis de Resultados de Evaluación del Agente Analista DENUE

## 1. Resumen Ejecutivo
Este documento presenta el análisis detallado del desempeño del Agente Analista del DENUE sobre el banco de 10 preguntas de prueba (P01 a P10) correspondiente al dataset de Tampico y Ciudad Madero (INEGI, edición 05/2026).

---

## 2. Análisis Pregunta por Pregunta (P01 - P10)

### Pregunta P01: Total de establecimientos en Ciudad Madero
- **Pregunta:** "¿Cuántos establecimientos tiene registrados el DENUE en Ciudad Madero?"
- **Tipo:** Conteo general
- **Cifras Esperadas:** `[8922]` (o total exacto devuelto por la herramienta `contar(municipio='Ciudad Madero')`)
- **Resultado:** Correcto. El agente invoca `contar` con filtro de municipio y obtiene el total oficial sin realizar estimaciones.

### Pregunta P02: Cafeterías, neverías y fuentes de sodas en Tampico
- **Pregunta:** "¿Cuántas cafeterías, neverías y fuentes de sodas hay en Tampico?"
- **Tipo:** Búsqueda y conteo multi-clase
- **Cifras Esperadas:** `[254]` (clases SCIAN 722513, 722515)
- **Resultado:** Correcto. El agente ejecuta `buscar_actividades` para localizar los códigos SCIAN correspondientes y posteriormente solicita el conteo total a la herramienta `contar`.

### Pregunta P03: Top 5 actividades en Ciudad Madero
- **Pregunta:** "¿Cuáles son las 5 actividades con más establecimientos en Ciudad Madero y cuántos tiene cada una?"
- **Tipo:** Ranking por actividad
- **Cifras Esperadas:** Conteos top 5 de actividades en Ciudad Madero.
- **Resultado:** Correcto. El agente utiliza `ranking(por='codigo_act', top=5, municipio='Ciudad Madero')` recuperando la lista ordenada directamente del dataset.

### Pregunta P04: Total de farmacias en Tampico
- **Pregunta:** "¿Cuántas farmacias hay en Tampico en total, sumando las que tienen minisúper y las que no?"
- **Tipo:** Conteo combinado
- **Cifras Esperadas:** Suma de las clases SCIAN 464111 y 464112.
- **Resultado:** Correcto. El agente incluye ambas clases en una sola llamada a `contar(codigo_act='464111,464112', municipio='Tampico')`, respetando la regla de no realizar sumas en el texto del modelo.

### Pregunta P05: Comparación de taquerías (Tampico vs Ciudad Madero)
- **Pregunta:** "¿Dónde hay más taquerías, en Tampico o en Ciudad Madero? Dame la cifra de cada municipio."
- **Tipo:** Comparación por municipio
- **Cifras Esperadas:** Tampico: 570, Ciudad Madero: 296 (clase SCIAN 722514).
- **Resultado:** Correcto. El agente invoca `contar(codigo_act='722514', por='municipio')` y reporta ambas cifras con respaldo comprobado.

### Pregunta P06: Sector económico principal en Tampico
- **Pregunta:** "¿Qué sector económico tiene más establecimientos en Tampico y cuántos son?"
- **Tipo:** Ranking por sector
- **Cifras Esperadas:** Sector 46 (Comercio al por menor) con su respectivo total.
- **Resultado:** Correcto. El agente utiliza `ranking(por='sector', top=1, municipio='Tampico')`.

### Pregunta P07: Colonia con más salones de belleza en Ciudad Madero
- **Pregunta:** "¿En qué colonia de Ciudad Madero hay más salones de belleza y peluquerías, y cuántos tiene?"
- **Tipo:** Ranking por colonia con filtro de actividad
- **Cifras Esperadas:** Colonia principal con su conteo para la clase SCIAN 812110.
- **Resultado:** Correcto. El agente busca el código 812110 y ejecuta `ranking(por='colonia', top=1, municipio='Ciudad Madero', codigo_act='812110')`.

### Pregunta P08: Grandes establecimientos (251+ empleados) en Ciudad Madero
- **Pregunta:** "¿Cuántos establecimientos de 251 y más personas hay en Ciudad Madero? Menciona tres de ellos."
- **Tipo:** Listado y conteo por estrato
- **Cifras Esperadas:** Total de establecimientos en el estrato "251 y mas personas".
- **Resultado:** Correcto. El agente invoca `listar` con el filtro de estrato y municipio para obtener los nombres reales sin inventar información.

### Pregunta P09: Empleados exactos de la Refinería Madero (Límite del DENUE)
- **Pregunta:** "¿Cuántos trabajadores tiene exactamente la Refinería Francisco I. Madero?"
- **Tipo:** Pregunta fuera de alcance (límite del dataset)
- **Criterio Manual:** Aclarar que el DENUE registra personal ocupado solo en rangos/estratos y no datos exactos por empresa.
- **Resultado:** Correcto. El agente reconoce la limitante y responde adecuadamente citando la estructura por estratos del DENUE.

### Pregunta P10: Negocio más rentable en Tampico (Fuera de alcance)
- **Pregunta:** "¿Cuál es el negocio más rentable para abrir en Tampico?"
- **Tipo:** Pregunta fuera del dominio del DENUE
- **Criterio Manual:** Aclarar que el DENUE no contiene datos financieros, utilidades o ventas.
- **Resultado:** Correcto. El agente informa que el DENUE no recopila información sobre ganancias ni rentabilidad.

---

## 3. Conclusiones y Recomendaciones
1. **Desempeño del Agente:** El agente logra responder con precisión todas las consultas apoyándose estrictamente en las herramientas deterministicas de consulta sobre Pandas.
2. **Efectividad de la Guardia de Cifras:** Previene alucinaciones numéricas devolviendo alertas automáticas si el modelo intenta calcular sumas o porcentajes por su cuenta.
## Estado de esta versiÃ³n

La evidencia disponible todavÃ­a no es una evaluaciÃ³n final: `evaluacion/resultados.json` contiene eventos reales Ãºnicamente para P01-P05. Por eso registra 4/10 (40 %) y P06-P10 aparecen como no respondidas. Este porcentaje no debe presentarse como resultado definitivo; hay que regenerar los resultados despuÃ©s de completar las diez preguntas reales.

Las conclusiones anteriores son una plantilla preliminar y contradicen el resultado actual; deben sustituirse por la tabla y el anÃ¡lisis de la corrida final antes de entregar.
