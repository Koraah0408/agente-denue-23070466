import os
import json
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

from app.herramientas import cargar_datos, Herramientas
from app.agente import responder


def main():
    parser = argparse.ArgumentParser(description="Ejecución por lote del banco de preguntas DENUE")
    parser.add_argument("--desde", type=str, default="P01", help="ID de pregunta inicial (ej: P01)")
    parser.add_argument("--hasta", type=str, default="P10", help="ID de pregunta final (ej: P10)")
    parser.add_argument("--simulado", action="store_true", help="Usar modelo simulado")
    args = parser.parse_args()

    # Create logs directory and timestamped run log file
    os.makedirs("logs", exist_ok=True)
    fecha_str = time.strftime("%Y%m%d-%H%M%S")
    bitacora_path = os.path.join("logs", f"corrida-{fecha_str}.jsonl")

    # Load system prompt
    sistema_path = os.path.join("prompts", "sistema.md")
    if os.path.exists(sistema_path):
        with open(sistema_path, "r", encoding="utf-8") as f:
            sistema = f.read()
    else:
        sistema = "Eres un agente analista del DENUE."

    # Load data
    ruta_denue = os.path.join("data", "denue_tampico_madero.csv")
    ruta_sectores = os.path.join("data", "sectores_scian.csv")
    df, sectores = cargar_datos(ruta_denue, ruta_sectores)
    herramientas = Herramientas(df, sectores)

    # Load questions
    ruta_preguntas = os.path.join("data", "preguntas_prueba.json")
    with open(ruta_preguntas, "r", encoding="utf-8") as f:
        data_preg = json.load(f)

    preguntas = data_preg.get("preguntas", [])

    if args.simulado:
        from app.modelo_simulado import llamar_modelo, reset_simulado
        reset_simulado()
    else:
        from app.modelo import llamar_modelo

    # Filter questions between --desde and --hasta
    ids = [p["id"] for p in preguntas]
    try:
        idx_desde = ids.index(args.desde)
    except ValueError:
        idx_desde = 0

    try:
        idx_hasta = ids.index(args.hasta)
    except ValueError:
        idx_hasta = len(preguntas) - 1

    preguntas_a_correr = preguntas[idx_desde : idx_hasta + 1]

    print(f"--- Iniciando lote desde {args.desde} hasta {args.hasta} ({len(preguntas_a_correr)} preguntas) ---")

    for i, item in enumerate(preguntas_a_correr):
        p_id = item["id"]
        pregunta_text = item["pregunta"]
        print(f"\n[{i+1}/{len(preguntas_a_correr)}] Ejecutando {p_id}: {pregunta_text}")

        try:
            res = responder(
                pregunta=pregunta_text,
                herramientas=herramientas,
                sistema=sistema,
                llamar=llamar_modelo,
                bitacora_path=bitacora_path,
                id_pregunta=p_id,
                canal="lote",
            )
            print(f"-> Terminado en {res['turnos']} turnos | Herramientas: {res['herramientas']} | Tiempo: {res['segundos']}s")
        except Exception as e:
            print(f"-> ERROR en {p_id}: {e}")
            # Register error event in bitacora
            corrida_name = os.path.basename(bitacora_path).replace(".jsonl", "").replace("corrida-", "")
            err_event = {
                "id": p_id,
                "evento": "error",
                "error": str(e),
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "corrida": corrida_name,
                "modelo": "simulado" if args.simulado else os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
            }
            with open(bitacora_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(err_event, ensure_ascii=False) + "\n")

        if not args.simulado and i < len(preguntas_a_correr) - 1:
            print("Pausa de 4 segundos entre llamadas reales...")
            time.sleep(4)

    print(f"\n--- Lote completado. Bitácora guardada en {bitacora_path} ---")


if __name__ == "__main__":
    main()
