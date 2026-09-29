import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

from app.herramientas import cargar_datos, Herramientas
from app.agente import responder


def main():
    parser = argparse.ArgumentParser(description="Agente Analista DENUE CLI")
    parser.add_argument("pregunta", type=str, help="Pregunta en lenguaje natural")
    parser.add_argument(
        "--simulado",
        action="store_true",
        help="Usar modelo simulado de 4 pasos (sin cuota de red)",
    )
    args = parser.parse_args()

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

    if args.simulado:
        from app.modelo_simulado import llamar_modelo
    else:
        from app.modelo import llamar_modelo

    res = responder(
        pregunta=args.pregunta,
        herramientas=herramientas,
        sistema=sistema,
        llamar=llamar_modelo,
        canal="terminal",
    )

    print("\n" + "=" * 60)
    print(res["respuesta"])
    print("=" * 60)
    print(
        f"Turnos: {res['turnos']} | Herramientas usadas: {res['herramientas']} | "
        f"Cifras sin respaldo: {res['cifras_sin_respaldo']} | Tiempo: {res['segundos']}s"
    )


if __name__ == "__main__":
    main()
