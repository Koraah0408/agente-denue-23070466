import re

def numeros(texto: str) -> set:
    if not texto or not isinstance(texto, str):
        return set()

    # 1. Remove list markers at the start of lines: e.g. "1. ", "2) ", "10.- "
    lines = []
    for line in texto.splitlines():
        cleaned_line = re.sub(r"^\s*\d+[\.\)\-]+\s+", "", line)
        lines.append(cleaned_line)
    text_processed = "\n".join(lines)

    # 2. Extract numbers:
    # Match formatted numbers: commas for thousands like 1,570 or 12,345,678, decimals like 65.8, integers.
    # Regex pattern matching digits with optional commas/decimals
    # Avoid matching dates like 05/2026 as a single float.
    tokens = re.findall(r"\b\d{1,3}(?:,\d{3})+\b|\b\d+(?:\.\d+)?\b", text_processed)

    res = set()
    for tok in tokens:
        clean_tok = tok.replace(",", "")
        try:
            if "." in clean_tok:
                val = float(clean_tok)
                if val.is_integer():
                    val = int(val)
            else:
                val = int(clean_tok)
            res.add(val)
        except ValueError:
            pass

    return res


def numeros_en(obj) -> set:
    nums = set()
    if obj is None or isinstance(obj, bool):
        return nums

    if isinstance(obj, (int, float)):
        val = float(obj) if isinstance(obj, float) else obj
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        nums.add(val)
    elif isinstance(obj, str):
        nums.update(numeros(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            nums.update(numeros_en(v))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            nums.update(numeros_en(item))

    return nums


def cifras_sin_respaldo(respuesta: str, pregunta: str, resultados: list) -> list:
    cifras_resp = numeros(respuesta)
    cifras_preg = numeros(pregunta)
    cifras_res = numeros_en(resultados)

    cifras_validas = cifras_preg | cifras_res
    sin_respaldo = cifras_resp - cifras_validas

    return sorted(list(sin_respaldo))
