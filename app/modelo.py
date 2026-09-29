import os
from google import genai
from google.genai import types

def obtener_cliente():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=5,
                initial_delay=2.0,
                max_delay=30.0,
            )
        ),
    )


def llamar_modelo(historial, sistema, declaraciones, forzar_texto=False):
    cliente = obtener_cliente()
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    config = types.GenerateContentConfig(
        system_instruction=sistema,
        tools=[types.Tool(function_declarations=declaraciones)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="NONE" if forzar_texto else "AUTO"
            )
        ),
    )

    respuesta = cliente.models.generate_content(
        model=model_name,
        contents=historial,
        config=config,
    )

    return respuesta
