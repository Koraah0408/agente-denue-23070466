# Análisis de Resultados — Agente Analista DENUE

## 1. Tabla de Evaluación de las 10 Preguntas (P01–P10)

| ID | Pregunta | Resultado | Turnos | Herramientas Usadas | Cifras sin Respaldo | Juicio / Justificación |
|---|---|---|:---:|:---:|:---:|---|
| **P01** | ¿Cuántos establecimientos tiene registrados el DENUE en Ciudad Madero? | **Correcto** | 2 | 1 | Ninguna | Cifra obtenida con `contar(municipio="Ciudad Madero")`: 7,184. |
| **P02** | ¿Cuántas cafeterías, neverías y fuentes de sodas hay en Tampico? | **Incorrecto** | 5 | 6 | Ninguna | Agotó el presupuesto de turnos/herramientas consultando clases por separado (722513, 722515) sin sumar el total (612). |
| **P03** | ¿Cuáles son las 5 actividades con más establecimientos en Ciudad Madero y cuántos tiene cada una? | **Correcto** | 2 | 1 | Ninguna | Ranking correcto por `codigo_act` en Madero: [685, 387, 296, 250, 167]. |
| **P04** | ¿Cuántas farmacias hay en Tampico en total, sumando las que tienen minisúper y las que no? | **Correcto** | 3 | 2 | Ninguna | Sumó correctamente las clases 464111 (118) y 464112 (36) obteniendo el total exacto de 154 farmacias. |
| **P05** | ¿Dónde hay más taquerías, en Tampico o en Ciudad Madero? Dame la cifra de cada municipio. | **Correcto** | 5 | 4 | Ninguna | Identificó la clase 722514 y contó por municipio: Tampico (570) y Ciudad Madero (296). |
| **P06** | ¿Qué sector económico tiene más establecimientos en Tampico y cuántos son? | **Correcto** | 4 | 2 | Ninguna | Identificó el Sector 46 (Comercio al por menor) como el de mayor presencia en Tampico con 5,400 establecimientos. |
| **P07** | ¿En qué colonia de Ciudad Madero hay más salones de belleza y peluquerías, y cuántos tiene? | **Correcto** | 4 | 2 | Ninguna | Filtró la clase 812110 y agrupó por colonia en Madero, identificando Unidad Nacional con 52 establecimientos. |
| **P08** | ¿Cuántos establecimientos de 251 y más personas hay en Ciudad Madero? Menciona tres de ellos. | **Correcto** | 4 | 2 | Ninguna | Reportó correctamente 0 establecimientos de 251 y más personas en Ciudad Madero y explicó que no es posible listar 3. |
| **P09** | ¿Cuántos trabajadores tiene exactamente la Refinería Francisco I. Madero? | **Cumple criterio** | 4 | 2 | Ninguna | **Juicio:** Aprobada manual.<br>*Cita justificativa:* "El DENUE registra el personal ocupado únicamente en estratos por rango (por ejemplo '251 y más personas') y no proporciona el número exacto de empleados de ningún establecimiento." |
| **P10** | ¿Cuál es el negocio más rentable para abrir en Tampico? | **Cumple criterio** | 4 | 2 | Ninguna | **Juicio:** Aprobada manual.<br>*Cita justificativa:* "El DENUE no contiene datos sobre ventas, ingresos, gastos, utilidades ni rentabilidad de los negocios; es un directorio de unidades económicas activas." |

---

## 2. Totales Globales

- **Preguntas automáticas aprobadas:** 7 de 8
- **Preguntas manuales aprobadas:** 2 de 2 (P09 y P10)
- **Precisión global:** 90 % (9 de 10)
- **Llamadas totales al modelo (turnos):** 37 llamadas

---

## 3. Análisis de Tres Casos Destacados

### Caso 1: Fallo en P02 (Cafeterías, neverías y fuentes de sodas en Tampico)
- **Causa identificada:** Declaración de herramientas / Estrategia del modelo.
- **Detalle:** Al recibir la consulta sobre tres conceptos distintos (cafeterías, neverías y fuentes de sodas), el modelo realizó múltiples búsquedas con `buscar_actividades` y consultas de `contar` individuales para la clase 722513 (neverías y paleterías) y 722515 (cafeterías y fuentes de sodas). Al alcanzar el límite de `MAX_HERRAMIENTAS = 6` y `MAX_TURNOS = 5`, el ciclo forzó la respuesta de texto antes de que el modelo pudiera sumar ambos subtotales (516 + 96 = 612).
- **¿Qué cambiaría?:** Mejorar la descripción en `prompts/sistema.md` para indicarle al modelo que ante giros compuestos debe solicitar los códigos SCIAN correspondientes en una sola llamada a `contar(codigo_act="722513,722515")`.

### Caso 2: P04 (Consolidación exitosa de clases de farmacias)
- **Causa de éxito:** Declaración clara en `DECLARACIONES` sobre el uso de prefijos y listas de códigos separados por coma.
- **Detalle:** El modelo primero usó `buscar_actividades(texto="farmacia")`, identificando la clase 464111 (farmacias sin minisúper) y 464112 (farmacias con minisúper). En el turno 2 solicitó `contar(codigo_act="464111,464112", municipio="Tampico")`, obteniendo en una sola ejecución el total global de 154 y los desgloses.
- **¿Qué cambiaría?:** El comportamiento fue óptimo; se mantendría la misma estructura.

### Caso 3: P09 (Manejo de límites del dataset)
- **Causa de éxito:** Prompt de sistema y diseño defensivo.
- **Detalle:** El modelo buscó el establecimiento o el estrato correspondiente en Ciudad Madero usando `listar(municipio="Ciudad Madero", estrato="251 y mas personas")`. Al revisar la respuesta, el código y la instrucción de sistema guiaron al modelo para no adivinar un número exacto y declarar la limitación explícita del DENUE respecto a conteos exactos de empleados.
- **¿Qué cambiaría?:** Mantener la restricción en el prompt de sistema.

---

## 4. Funcionamiento de la Guardia de Cifras

### ¿Corrigió alguna respuesta durante las corridas?
Sí. Durante las pruebas con la pregunta TG-3 desde Telegram (*"¿Cuál es el negocio más rentable para abrir en Tampico?"*), el modelo en su primera redacción intentó incluir estimaciones numéricas no presentes en el resultado de las herramientas (`[1, 2, 1300]`). 

La guardia detectó que dichas cifras no provenían ni de la pregunta ni de las herramientas ejecutadas, e interrumpió el turno agregando el mensaje de corrección:
> *"Revisión automática: estas cifras de tu respuesta no aparecen en la pregunta ni en los resultados de las herramientas: [1, 2, 1300]. No calcules sumas ni porcentajes... Corrige la respuesta."*

En el turno siguiente, el modelo reescribió la respuesta eliminando los números inventados y citando únicamente la restricción del DENUE, logrando la aprobación con `cifras_sin_respaldo: []`.

---

## 5. Resumen del Rol del Modelo vs Código (en 5 Renglones)

1. El **modelo de lenguaje (LLM)** percibe la pregunta del usuario y razona sobre cuál de las cuatro herramientas fijas solicitar y con qué argumentos JSON.
2. El **código Python** toma el control total, ejecuta la consulta de forma determinística con Pandas sobre los 22,900 registros del DENUE y devuelve el resultado exacto.
3. El **modelo de lenguaje** redacta la respuesta final en español utilizando únicamente la información proporcionada por el resultado de las herramientas.
4. El **código Python (Guardia)** intercepta la respuesta redactada y verifica numéricamente que ninguna cifra presentada haya sido inventada o calculada erróneamente por el LLM.
5. El **código Python (Ciclo)** administra el presupuesto de turnos, el historial asíncrono y los canales de entrada/salida (CLI, Lote y Telegram), garantizando la seguridad y estabilidad del agente.
