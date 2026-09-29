from google.genai import types

_paso_actual = 1

def reset_simulado():
    global _paso_actual
    _paso_actual = 1

def respuesta_falsa(partes):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=partes)
            )
        ]
    )

def llamar_modelo(historial, sistema, declaraciones, forzar_texto=False):
    global _paso_actual

    paso = _paso_actual
    _paso_actual = (_paso_actual % 4) + 1

    if paso == 1:
        if forzar_texto:
            partes = [types.Part(text="Respuesta: No pude completar la consulta con el presupuesto.")]
        else:
            partes = [
                types.Part(
                    function_call=types.FunctionCall(
                        id="sim-1",
                        name="buscar_actividades",
                        args={"texto": "farmacia"},
                    )
                )
            ]
    elif paso == 2:
        if forzar_texto:
            partes = [types.Part(text="Respuesta: No pude completar la consulta con el presupuesto.")]
        else:
            partes = [
                types.Part(
                    function_call=types.FunctionCall(
                        id="sim-2",
                        name="contar",
                        args={
                            "codigo_act": "464111,464112",
                            "municipio": "Tampico",
                        },
                    )
                )
            ]
    elif paso == 3:
        partes = [
            types.Part(
                text="Respuesta: En Tampico hay 160 farmacias.\nDatos: DENUE 05/2026, INEGI"
            )
        ]
    elif paso == 4:
        partes = [
            types.Part(
                text="Respuesta: En Tampico hay 154 farmacias (clases 464111 y 464112).\nDatos: DENUE 05/2026, INEGI"
            )
        ]

    return respuesta_falsa(partes)
