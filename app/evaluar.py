import os
import sys
import json
import argparse
import unicodedata
from app.guardia import numeros


def _normalizar_eval(texto: str) -> str:
    if not texto:
        return ""
    t = texto.lower()
    nfkd = unicodedata.normalize("NFKD", t)
    ascii_t = "".join(c for c in nfkd if not unicodedata.combining(c) and ord(c) < 128)
    return " ".join(ascii_t.split())

def evaluar_respuesta(id_p: str, respuesta: str, esperada: dict) -> dict:
    revision = esperada.get("revision", "automatica")
    cifras_en_resp = numeros(respuesta)

    if revision == "automatica":
        cifras_clave = set(esperada.get("cifras_clave", []))
        cumplido = True if not cifras_clave else cifras_clave.issubset(cifras_en_resp)
        textos_clave = esperada.get("textos_clave") or []
        resp_n = _normalizar_eval(respuesta)
        textos_faltan = [t for t in textos_clave if _normalizar_eval(t) not in resp_n]
        if textos_faltan:
            cumplido = False
        return {
            "cumplido": cumplido,
            "cifras_clave_esperadas": list(cifras_clave),
            "cifras_encontradas": sorted(list(cifras_en_resp)),
            "textos_clave": textos_clave,
            "textos_faltan": textos_faltan,
            "revision": "automatica",
        }
    else:
        return {
            "cumplido": None,
            "criterio": esperada.get("criterio", ""),
            "revision": "manual",
        }


def main():
    parser = argparse.ArgumentParser(description="Evaluador de corridas DENUE")
    parser.add_argument("bitacoras", nargs="+", help="Archivos .jsonl de bitácoras de corrida real")
    args = parser.parse_args()

    ruta_esperadas = os.path.join("evaluacion", "esperadas.json")
    if not os.path.exists(ruta_esperadas):
        print("ERROR: evaluacion/esperadas.json no existe. Ejecuta primero evaluacion/calcular_esperadas.py")
        sys.exit(1)

    with open(ruta_esperadas, "r", encoding="utf-8") as f:
        esperadas_dict = {e["id"]: e for e in json.load(f)["esperadas"]}

    eventos_fin = {}

    for bit_path in args.bitacoras:
        if not os.path.exists(bit_path):
            print(f"Advertencia: El archivo {bit_path} no existe.")
            continue
        with open(bit_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get("evento") == "fin" and ev.get("modelo") not in (None, "simulado"):
                        p_id = ev.get("id")
                        eventos_fin[p_id] = ev
                except json.JSONDecodeError:
                    continue

    evaluaciones = []
    correctas = 0

    print("=" * 70)
    print("EVALUACIÓN DE RESPUESTAS DEL AGENTE")
    print("=" * 70)

    for p_id in sorted(esperadas_dict.keys()):
        esp = esperadas_dict[p_id]
        if p_id not in eventos_fin:
            print(f"[{p_id}] FALTA: Sin evento 'fin' en las bitácoras proporcionadas")
            evaluaciones.append({
                "id": p_id,
                "cumplido": False,
                "error": "Pregunta no respondida en las bitácoras",
            })
            continue

        ev = eventos_fin[p_id]
        respuesta_texto = ev.get("respuesta", "")
        res_eval = evaluar_respuesta(p_id, respuesta_texto, esp)

        if res_eval.get("revision") == "manual":
            estado_str = "MANUAL"
        elif res_eval["cumplido"]:
            correctas += 1
            estado_str = "OK"
        else:
            estado_str = "FALLO"

        print(f"[{p_id}] {estado_str} | Turnos: {ev.get('turnos')} | Herramientas: {ev.get('herramientas')} | Cifras sin respaldo: {ev.get('cifras_sin_respaldo')}")
        evaluaciones.append({
            "id": p_id,
            "pregunta": esp.get("pregunta"),
            "cumplido": res_eval["cumplido"],
            "detalles_evaluacion": res_eval,
            "turnos": ev.get("turnos"),
            "herramientas": ev.get("herramientas"),
            "cifras_sin_respaldo": ev.get("cifras_sin_respaldo"),
            "segundos": ev.get("segundos"),
        })

    total_preguntas = len(esperadas_dict)
    porcentaje = round((correctas / total_preguntas) * 100, 2) if total_preguntas > 0 else 0.0

    res_final = {
        "total_preguntas": total_preguntas,
        "correctas": correctas,
        "porcentaje_precision": porcentaje,
        "evaluaciones": evaluaciones,
    }

    ruta_res = os.path.join("evaluacion", "resultados.json")
    with open(ruta_res, "w", encoding="utf-8") as f:
        json.dump(res_final, f, ensure_ascii=False, indent=2)

    print("-" * 70)
    print(f"RESULTADO GLOBAL: {correctas}/{total_preguntas} ({porcentaje}%)")
    print(f"Evaluación guardada en {ruta_res}")


if __name__ == "__main__":
    main()
