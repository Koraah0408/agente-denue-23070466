# Traza Manual de Ejecución y Validación de la Guardia de Cifras

## 1. Introducción

Este documento describe paso a paso cómo el agente resuelve la pregunta P05, cómo funciona la Guardia de Cifras ante seis variaciones hipotéticas de respuesta, y un caso real de corrección desde Telegram.

---

## 2. Resolución de la Pregunta P05

**Pregunta:** "¿Dónde hay más taquerías, en Tampico o en Ciudad Madero? Dame la cifra de cada municipio."

### Turno 1 — Identificar la clase SCIAN

El modelo solicita la herramienta `buscar_actividades` con el texto "taqueria".

Resultado devuelto:
```json
{"codigo_act": "722514", "actividad": "Restaurantes con servicio de preparación de tacos y tortas", "establecimientos": 866}
```

### Turno 2 — Contar por municipio

El modelo solicita `contar` con el código encontrado, agrupando por municipio.

Argumentos: `{"codigo_act": "722514", "por": "municipio"}`

Resultado devuelto:
```json
{"filas": [{"valor": "Tampico", "total": 570}, {"valor": "Ciudad Madero", "total": 296}], "total_filtrado": 866}
```

### Turno 3 — Respuesta final y validación

El modelo redacta la respuesta con las cifras obtenidas de las herramientas:

> "En Tampico hay más taquerías con 570 establecimientos, mientras que en Ciudad Madero hay 296. Datos: DENUE 05/2026, INEGI. Clase SCIAN 722514."

La Guardia de Cifras revisa:

- Cifras en la respuesta: `{570, 296, 722514, 5, 2026}`
- Cifras respaldadas (pregunta + herramientas): `{570, 296, 866, 722514, 5, 2026}`
- Cifras sin respaldo: ninguna

Estado: aprobada sin corrección.

---

## 3. Experimentos de la Guardia de Cifras (E.2)

Contexto de respaldo: Tampico 570, Ciudad Madero 296, clase 722514, total 866.

| ID | Respuesta hipotética | Cifras sin respaldo | Resultado |
|---|---|---|---|
| G1 | "Tampico tiene 570 taquerías y Ciudad Madero 296." | ninguna | Pasa |
| G2 | "Tampico 570 y Madero 296: diferencia de 274." | `[274]` | Rechaza |
| G3 | "En total hay 866; Tampico concentra el 65.8 %." | `[65.8]` | Rechaza |
| G4 | "1. Tampico: 570  2. Ciudad Madero: 296, clase 722514." | ninguna | Pasa (los `1.` y `2.` no se cuentan como cifras) |
| G5 | "Tampico tiene 1,570 taquerías." | `[1570]` | Rechaza |
| G6 | "Ciudad Madero tiene 570 y Tampico 296." | ninguna | Pasa |

### Análisis del caso G6

La guardia compara conjuntos de números, no el significado de cada cifra. Como 570 y 296 existen en los datos de respaldo, la diferencia es vacía y la respuesta pasa aunque los municipios estén invertidos.

Lo que detecta esta inversión es el evaluador (`app/evaluar.py`), que compara la respuesta contra los criterios semánticos de `evaluacion/esperadas.json`. Este es un límite de diseño conocido: la guardia previene cifras inventadas; la corrección semántica corresponde al evaluador.

---

## 4. Caso real desde Telegram — TG-3

**Pregunta:** "¿Cuál es el negocio más rentable para abrir en Tampico?"

El agente consultó `ranking(por="sector")` y `ranking(por="codigo_act")` para tener datos reales antes de responder.

En la primera redacción la guardia detectó cifras sin respaldo (`[1, 2, 1300]`) y devolvió el control al modelo para que corrigiera. En la segunda redacción las cifras sin respaldo resultaron vacías y la respuesta fue aprobada.

Extracto de la respuesta final:

> "El DENUE no registra datos financieros, por lo que no es posible calcular rentabilidad. Los sectores con más establecimientos en Tampico son: Comercio al por menor (5 400), Otros servicios (2 589) y Servicios de alimentos (2 275). Datos: DENUE 05/2026, INEGI."

Métricas de la corrida:

| Métrica | Valor |
|---|---|
| Turnos del modelo | 4 |
| Herramientas ejecutadas | 2 |
| Guardia activó corrección | sí |
| Cifras sin respaldo en la respuesta final | ninguna |

---

## 5. Conclusión

La guardia intercepta cifras numéricas sin respaldo en cada turno del ciclo del agente. Los experimentos muestran que detecta diferencias calculadas, porcentajes no solicitados y errores tipográficos en cifras, pero no inversiones de asignación entidad-valor cuando los números sí existen en los datos. Esa responsabilidad recae en el evaluador automático.
