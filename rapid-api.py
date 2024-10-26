import requests

def translate_text_mymemory(text, target_lang="es"):
    url = "https://api.mymemory.translated.net/get"

    params = {
        "q": text,
        "langpair": f"en|{target_lang}"
    }

    response = requests.get(url, params=params)
    response_json = response.json()
    
    # Verificar la estructura de la respuesta y extraer el texto traducido
    translated_text = response_json.get('responseData', {}).get('translatedText', 'No translation found')
    return translated_text

# Ejemplo de uso
texto_original = "Hello, how are you?"
texto_traducido = translate_text_mymemory(texto_original)
print("Texto traducido final:", texto_traducido)
