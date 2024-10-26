import dl_translate as dlt
mt = dlt.TranslationModel(device="auto") # ("cpu" or "gpu")  Slow when you load it for the first time 
#print(mt.available_languages())  # All languages that you can use
#print(mt.available_codes())  # Code corresponding to each language accepted
#print(mt.get_lang_code_map())  # Dictionary of lang -> code

for i in range(5):
    text_hi = "i am doing things today, but i am worry.  ?"
    print(mt.translate(text_hi,  source="English", target="es"))