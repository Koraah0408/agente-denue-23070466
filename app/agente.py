import os
import json
import time
from google.genai import types
from app.herramientas import DECLARACIONES
from app.guardia import cifras_sin_respaldo

MAX_TURNOS = 5
MAX_HERRAMIENTAS = 6

def ejecutar(herramientas, nombre: str, args: dict) -> dict:
    valid_names = ["buscar_actividades", "contar", "ranking", "listar"]
    if nombre not in valid_names:
        return {
            "ok": False,
            "error": f"herramienta inexistente: '{nombre}'",
            "valores_validos": valid_names,
        }

    try:
        metodo = getattr(herramientas, nombre)
        res = metodo(**args)
        if isinstance(res, dict):
            return res
        return {"ok": True, "fuente": "DENUE 05/2026, INEGI", "resultado": res}
    except TypeError as te:
        return {"ok": False, "error": f"Argumento invalido para {nombre}: {str(te)}"}
    except Exception as e:
        return {"ok": False, "error": f"Error al ejecutar {nombre}: {str(e)}"}


def responder(
    pregunta: str,
    herramientas,
    sistema: str,
    llamar,
    bitacora_path: str = None,
    id_pregunta: str = "P00",
    canal: str = "terminal",
    usuario: str = None,
    modelo_nombre: str = None,
) -> dict:
    t_inicio = time.time()

    if not bitacora_path:
        os.makedirs("logs", exist_ok=True)
        fecha_str = time.strftime("%Y%m%d-%H%M%S")
        bitacora_path = os.path.join("logs", f"corrida-{fecha_str}.jsonl")

    corrida_name = os.path.basename(bitacora_path).replace(".jsonl", "").replace("corrida-", "")
    modelo_name = modelo_nombre or os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    def registrar_evento(evento: dict):
        evento["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        evento["corrida"] = corrida_name
        if "modelo" not in evento:
            evento["modelo"] = modelo_name
        try:
            with open(bitacora_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(evento, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # 1. Evento Inicio
    init_ev = {
        "id": id_pregunta,
        "evento": "inicio",
        "pregunta": pregunta,
        "canal": canal,
    }
    if usuario:
        init_ev["usuario"] = usuario
    registrar_evento(init_ev)

    historial = [types.Content(role="user", parts=[types.Part(text=pregunta)])]
    resultados = []
    usadas = 0
    corregida = False
    forzar_texto = False
    texto_final = ""
    sin_respaldo_final = []

    for turno in range(1, MAX_TURNOS + 1):
        if turno == MAX_TURNOS:
            forzar_texto = True

        # 4. llamar modelo
        registrar_evento({
            "id": id_pregunta,
            "evento": "modelo",
            "turno": turno,
            "forzar_texto": forzar_texto,
        })

        respuesta = llamar(historial, sistema, DECLARACIONES, forzar_texto=forzar_texto)

        # Append model response to history as arrived
        if respuesta.candidates and respuesta.candidates[0].content:
            historial.append(respuesta.candidates[0].content)

        pedidas = respuesta.function_calls or []

        if pedidas:
            partes_response = []
            for fc in pedidas:
                fc_args = dict(fc.args or {})
                if usadas >= MAX_HERRAMIENTAS:
                    resultado = {"ok": False, "error": "presupuesto agotado"}
                else:
                    usadas += 1
                    resultado = ejecutar(herramientas, fc.name, fc_args)
                    resultados.append(resultado)

                registrar_evento({
                    "id": id_pregunta,
                    "evento": "herramienta",
                    "nombre": fc.name,
                    "args": fc_args,
                    "ok": resultado.get("ok", False),
                    "error": resultado.get("error"),
                })

                partes_response.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response=resultado,
                        )
                    )
                )

            historial.append(types.Content(role="user", parts=partes_response))

            if usadas >= MAX_HERRAMIENTAS:
                forzar_texto = True

            continue

        # Model returned text
        texto_final = respuesta.text or ""
        sin_respaldo = cifras_sin_respaldo(texto_final, pregunta, resultados)
        sin_respaldo_final = sin_respaldo

        registrar_evento({
            "id": id_pregunta,
            "evento": "guardia",
            "cifras_sin_respaldo": sin_respaldo,
            "corregida": corregida,
        })

        if sin_respaldo and not corregida and turno < MAX_TURNOS:
            corregida = True
            corr_msg = (
                f"Revisión automática: estas cifras de tu respuesta no aparecen en la pregunta "
                f"ni en los resultados de las herramientas: {sin_respaldo}. "
                f"No calcules sumas ni porcentajes: si necesitas un total, pídelo a una herramienta. "
                f"Corrige la respuesta."
            )
            historial.append(types.Content(role="user", parts=[types.Part(text=corr_msg)]))
            continue

        if sin_respaldo:
            texto_final += f"\n\n[Aviso] Cifras sin respaldo en los datos: {sin_respaldo}"

        segundos = round(time.time() - t_inicio, 2)
        res_dict = {
            "respuesta": texto_final,
            "turnos": turno,
            "herramientas": usadas,
            "cifras_sin_respaldo": sin_respaldo_final,
            "segundos": segundos,
        }

        fin_ev = {
            "id": id_pregunta,
            "evento": "fin",
            "respuesta": texto_final,
            "turnos": turno,
            "herramientas": usadas,
            "cifras_sin_respaldo": sin_respaldo_final,
            "segundos": segundos,
        }
        registrar_evento(fin_ev)
        return res_dict

    # Agotados turnos sin texto
    segundos = round(time.time() - t_inicio, 2)
    err_dict = {
        "respuesta": texto_final or "Error: se agotaron los turnos sin texto",
        "turnos": MAX_TURNOS,
        "herramientas": usadas,
        "cifras_sin_respaldo": sin_respaldo_final,
        "segundos": segundos,
    }
    registrar_evento({
        "id": id_pregunta,
        "evento": "error",
        "error": "Se agotaron los turnos sin texto",
    })
    return err_dict
