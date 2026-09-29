# Traza Manual de Ejecución y Validación de la Guardia de Cifras

## 1. Introducción
Este documento registra el análisis manual del ciclo de vida del agente analista del DENUE, incluyendo la resolución de la pregunta P05 y la verificación experimental del comportamiento del componente `Guardia de Cifras` (`app/guardia.py`).

---

## 2. Traza Manual de Resolución (Pregunta P05)
**Pregunta P05:** "¿Dónde hay más taquerías, en Tampico o en Ciudad Madero? Dame la cifra de cada municipio."

### Turno 1: Identificación de la Clase SCIAN
- **Mensaje del Usuario:** "¿Dónde hay más taquerías, en Tampico o en Ciudad Madero? Dame la cifra de cada municipio."
- **Llamada a Herramienta pedida por el Modelo:**
  - Herramienta: `buscar_actividades`
  - Argumento: `{"texto": "taqueria"}`
- **Ejecución y Respuesta de la Herramienta:**
  - Resultado: `{"ok": true, "fuente": "DENUE 05/2026, INEGI", "actividades": [{"codigo_act": "722514", "actividad": "Restaurantes con servicio de preparación de tacos y tortas", "establecimientos": 866}]}`

### Turno 2: Conteo Agrupado por Municipio
- **Llamada a Herramienta pedida por el Modelo:**
  - Herramienta: `contar`
  - Argumentos: `{"codigo_act": "722514", "por": "municipio"}`
- **Ejecución y Respuesta de la Herramienta:**
  - Resultado: `{"ok": true, "fuente": "DENUE 05/2026, INEGI", "por": "municipio", "filtros": {"codigo_act": "722514"}, "total_filtrado": 866, "filas": [{"valor": "Tampico", "total": 570}, {"valor": "Ciudad Madero", "total": 296}]}`

### Turno 3: Redacción Final y Verificación de Cifras
- **Respuesta generada por el Modelo:**
  "En Tampico hay más taquerías con 570 establecimientos (Restaurantes con servicio de preparación de tacos y tortas), mientras que en Ciudad Madero hay 296 establecimientos.

  Datos: DENUE 05/2026, INEGI. Filtros: Clase SCIAN 722514."
- **Validación de Guardia de Cifras:**
  - Cifras en la respuesta: `{570, 296, 722514, 05, 2026}`
  - Cifras respaldadas en la pregunta y resultados: `{570, 296, 722514, 05, 2026, 866}`
  - Cifras sin respaldo: `[]`
  - Estado: Aprobada sin corrección.

---

## 3. Pruebas Experimentales de la Guardia de Cifras (Experimento E.2)

A partir del contexto de la pregunta P05 y los resultados obtenidos por las herramientas (Tampico: 570, Madero: 296, Clase: 722514), se evaluaron las 6 variaciones de respuesta hipotéticas (G1 a G6):

| ID | Respuesta Hipotética | Cifras Extraídas | Cifras sin Respaldo | Resultado Guardia |
|---|---|---|---|---|
| **G1** | Tampico tiene 570 taquerías y Ciudad Madero 296. | `{296, 570}` | `[]` | Pasa limpia |
| **G2** | Tampico tiene 570 y Madero 296: una diferencia de 274. | `{274, 296, 570}` | `[274]` | Detecta cifra inventada (274) |
| **G3** | En total hay 866; Tampico concentra el 65.8 %. | `{65.8, 866}` | `[65.8]` | Detecta porcentaje calculado (65.8) |
| **G4** | 1. Tampico: 570<br>2. Ciudad Madero: 296<br>Clase SCIAN 722514, DENUE 05/2026. | `{5, 296, 570, 2026, 722514}` | `[]` | Ignora marcadores `1.` y `2.`, pasa limpia |
| **G5** | Tampico tiene 1,570 taquerías. | `{1570}` | `[1570]` | Detecta error en cifra (1570 != 570) |
| **G6** | Ciudad Madero tiene 570 taquerías y Tampico 296. | `{296, 570}` | `[]` | **Pasa limpia (Aviso especial)** |

### Análisis del Caso G6: ¿Por qué pasa la Guardia y qué componente la detecta?
- **¿Por qué la deja pasar la guardia?**
  La `Guardia de Cifras` (`app/guardia.py`) valida únicamente la **existencia cuantitativa** de las cifras en el conjunto de datos de respaldo (pregunta + resultados de herramientas). Como 570 y 296 existen explícitamente en el JSON de resultados de la herramienta `contar`, el conjunto diferencia `cifras_respuesta - cifras_respaldadas` resulta vacío `[]`. La guardia no analiza relaciones semánticas ni la asociación entre entidades y valores.

- **¿Qué parte del proyecto la detecta?**
  El script de evaluación automática `app/evaluar.py` en combinación con `evaluacion/esperadas.json`. El evaluador valida que las respuestas cumplan con los criterios semánticos y numéricos exactos asociados a cada entidad o municipio.

---

## 4. Conclusión
El diseño modular del agente garantiza que las alucinaciones numéricas (cálculos de diferencias, porcentajes no solicitados o cifras erróneas) sean interceptadas en el ciclo del agente mediante el prompt de revisión automática.
