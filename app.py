# Asegúrate de instalar las bibliotecas necesarias
# pip install Flask yt-dlp moviepy gTTS SpeechRecognition deep-translator

from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
from moviepy.editor import VideoFileClip, AudioFileClip,concatenate_audioclips,CompositeAudioClip
from moviepy.editor import *
from deep_translator import GoogleTranslator  
import os
from faster_whisper import WhisperModel
from speechify.speechify import  SpeechifyAPI
import os  
from datetime import datetime
import ffmpeg
from pydub import AudioSegment
import io
import requests





app = Flask(__name__)

# Crear una instancia the Speechify API 
speechify_api = SpeechifyAPI()

lista_de_eventos=[]
lista_de_errores=[]



def hora():
    # Obtener la hora actual
    now = datetime.now()
    # Formatear la hora como hh:mm:ss
    time_string = now.strftime("%H:%M:%S")
    return time_string


def api_traducir(text, target_lang="es"):
    url = "https://api.mymemory.translated.net/get"

    params = {
        "q": text,
        "langpair": f"en|{target_lang}"}
    

    response = requests.get(url, params=params)
    response_json = response.json()
    
    # Verificar la estructura de la respuesta y extraer el texto traducido
    translated_text = response_json.get('responseData', {}).get('translatedText', 'No translation found')
    return translated_text
        

   




@app.route('/')
def index():
    global lista_de_eventos
    global lista_de_errores
    lista_de_eventos=[]
    lista_de_errores=[]
    
    files_to_delete = ["downloaded_video.mp4", "edu-definitivo.mp3", 
                       "output_video.mp4","downloaded_audio.m4a",
                       "audio_de_fondo.mp3","audio_espanol.mp3",
                       "edu-mezclado.mp3"]
    for file in files_to_delete:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Archivo {file} eliminado.")
            else:
                print(f"Archivo {file} no existe.")
        except Exception as e:
            print(f"Error al eliminar {file}: {str(e)}")
        
    return render_template('index.html')

@app.route('/traducir', methods=['POST','GET'])
def traducir_audio_youtube():
    global lista_de_eventos
    global mensaje_de_error
    url = request.json.get('url')
    sexo= request.json.get('sexo')
    tiempo_segmento=0
    tiempo_total=0
    lista_de_eventos.append(f"{hora()} - Se han iniciado los procesos de Servidor")
    
     # Función para acelerar el audio
    def accelerate_audio(audio_segment, speed=1):
        return audio_segment._spawn(audio_segment.raw_data, overrides={
            "frame_rate": int(audio_segment.frame_rate * speed)
        }).set_frame_rate(audio_segment.frame_rate)
    
    
    files_to_delete = ["downloaded_video.mp4", "edu-definitivo.mp3", 
                       "output_video.mp4","downloaded_audio.m4a",
                       "audio_de_fondo.mp3","audio_espanol.mp3",
                       "edu-mezclado.mp3"]

    for file in files_to_delete:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Archivo {file} eliminado.")
            else:
                print(f"Archivo {file} no existe.")
        except Exception as e:
            print(f"Error al eliminar {file}: {str(e)}")
    
    
    
                    
                    
    # Descargar el video y el audio usando yt-dlp
    ydl_opts = {
        'format': 'bestvideo[filesize<70M][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': 'downloaded_video.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'noplaylist': True,
        'quiet': True,
        'cookiefile': "yt.txt",
        'nocontinue': True,  # No continuar desde archivos existentes
        'rm_cachedir': True  # Eliminar archivos en caché
    }
    

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            info_dict = ydl.extract_info(url, download=False)
            video_file = f"downloaded_video.{info_dict['ext']}"
            print(f"Video descargado: {video_file}")
            lista_de_eventos.append(f"{hora()} - Video descargado correctamente")
           
    except Exception as e:
        lista_de_errores.append(f"{hora()} - Error al descargar video. Reload App")
        return jsonify({'data': f'Error al descargar el video: {str(e)}'}), 500
      

    # Descargar el audio
    audio_file = f"downloaded_audio.m4a"
    ydl_opts_audio = {
        'format': 'bestaudio[ext=m4a]',
        'outtmpl': audio_file,
        'noplaylist': True,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url])
            print(f"Audio descargado: {audio_file}")
            lista_de_eventos.append(f"{hora()} - Audio descargado correctamente")
    except Exception as e:
        lista_de_errores.append(f"{hora()} - Error al descargar audio. Reload App")
        return jsonify({'data': f'Error al descargar el audio: {str(e)}'}), 500
       


    
    #sacar audio del fondo
    try:
        
        sound_stereo = AudioSegment.from_file("downloaded_audio.m4a", format="m4a")
        sound_monoL = sound_stereo.split_to_mono()[0]
        sound_monoR = sound_stereo.split_to_mono()[1]

        # Invert phase of the Right audio file
        sound_monoR_inv = sound_monoR.invert_phase()

        # Merge two L and R_inv files, this cancels out the centers
        sound_CentersOut = sound_monoL.overlay(sound_monoR_inv)

        # Export merged audio file
        sound_CentersOut.export("audio_de_fondo.mp3", format="mp3") 
        print("musica de Fondo capturada")
        lista_de_eventos.append(f"{hora()} - Remove Vocals from audio terminado")
    except:
        lista_de_errores.append(f"{hora()} - Error al remover voces")
    
   

 

    try:
        # Transcribir el audio usando Whisper
        lista_de_eventos.append(f"{hora()} - .......... Procesando Speech to text. ( Take some minutes )")
        audio_for_whisper = "downloaded_audio.m4a"
        # model = whisper.load_model("small")  # Puedes usar "small", "medium", "large" según tus necesidades
        # modelo para whisper
        model_size = "small"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        # result = model.transcribe(audio_for_whisper)
        segments, info = model.transcribe(audio_for_whisper, beam_size=5)
        # segments = result["segments"]
        lista_de_eventos.append(f"{hora()} - Texto extraído correctamente")
        print("Transcripción completa.")

        # Imprimir el texto transcrito y los tiempos antes de la traducción y generación de voz
        #for segment in segments:
            #print(f"Segmento original: Start: {segment['start']} - End: {segment['end']} - Text: {segment['text']}")

        # Traducir cada fragmento y unir los resultados
        translated_segments = []
        for segment in segments:
            translated_text = GoogleTranslator(source='auto', target='es').translate(segment.text)
            #translated_text=api_traducir(segment.text)
            #translated_text = GoogleTranslator(source='auto', target='es').translate(segment["text"])
            #translated_text=mt.translate(segment.text,  source="English", target="es")
            
            #start = segment["start"]
            #end = segment["end"]
            start = segment.start
            end = segment.end
            tiempo=end-start
            tiempo_total +=tiempo
            print("-------------------------------------------------------")
            print(tiempo_segmento,tiempo_total)
            translated_segments.append((start, end, translated_text))

        lista_de_eventos.append(f"{hora()} - Traducción al castellano terminada")
        print("Traducción completa.")

        # Imprimir cada segmento traducido
        #for start, end, text in translated_segments:
            #print(f"Segmento traducido: Start: {start} - End: {end} - Text: {text}")

        # Sintetizar voz en español usando  implementación de Spechify
        output_audio = AudioSegment.silent(duration=0)
        print("Inicio de la síntesis de voz.")

        for i, (start, end, text) in enumerate(translated_segments):
            try:
                # Generar el audio usando Spechify
                if sexo=="hombre":
                     audio_io =  speechify_api.generate_audio_files(text, "tanner", "speechify", "en-EN")
                else:
                     audio_io =  speechify_api.generate_audio_files(text, "kristy", "speechify", "en-US")    
                # Crear un segmento de audio desde BytesIO
                segment_audio = AudioSegment.from_file(audio_io, format="mp3")
                
                # relentizar audio
                #segment_audio = accelerate_audio(segment_audio, speed=1)
                segment_duration = len(segment_audio)  # Longitud del audio acelerado

                # Calcular el tiempo de inicio del segmento actual en milisegundos
                start_time_ms = start * 1000
                end_time_ms= end*1000
                tiempo_segmento=end_time_ms-start_time_ms
              
                # Calcular el silencio necesario al principio del segmento
                silence_at_start = max(tiempo_segmento - segment_duration, 1.05)
                output_audio += AudioSegment.silent(duration=silence_at_start) + segment_audio

                #print(f"Audio generado para el segmento: Start: {start}, End: {end}, Text: {text}")

            except Exception as e:
                print(f"Error al generar audio para el segmento: Start: {start}, End: {end}, Text: {text}, Error: {str(e)}")
                lista_de_errores.append(f"{hora()} - Error al generar audio para un segmento. Verifica los logs para más detalles.")

        print("Síntesis de voz completa.")
        
        # Exportar el audio final
        output_audio.export("audio_espanol.mp3", format="mp3")
        print("Exportación del audio completada.")

    except Exception as e:
        print("Error en el proceso completo.")
        lista_de_errores.append(f"{hora()} - Error al procesar el audio: {str(e)}")
        return jsonify({'data': f'Error al procesar el audio: {str(e)}'}), 500


  
        
    """ # Verificar y añadir silencio al final si es necesario para completar la duración total esperada
    final_duration_ms = segments[-1]["end"] * 1000
    if len(output_audio) < final_duration_ms:
        output_audio += AudioSegment.silent(duration=final_duration_ms - len(output_audio))

    # Exportar el audio final
    output_audio.export("audio_espanol.mp3", format="mp3")
    print("Exportación del audio completada.")
    lista_de_eventos.append(f"{hora()} - Ya se ha generado nuevo audio sintetico español") """
 
    # Calcular la duración del audio generado y del video original
    audio_file = "audio_espanol.mp3"
    video_file = "downloaded_video.mp4"
    audio_duration = len(AudioSegment.from_file(audio_file)) / 1000  # Duración en segundos
    #video_duration = VideoFileClip(video_file).duration  # Duración en segundos
    video_duration=int(tiempo_total)
    

    # Factor de velocidad (1.2 para acelerar en 20%)
    if audio_duration>video_duration:
          speed_factor = (audio_duration/video_duration)
    else: 
          speed_factor =(video_duration / audio_duration)
    if audio_duration==video_duration:
        speed_factor=1          
    print("------------------------------")
    print(video_duration,audio_duration)
    print("------------------------------")
    # Cambiar la velocidad del audio
    def change_audio_speed(audio_file, speed=1.0):
        sound = AudioSegment.from_file(audio_file)
        sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)})
        return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    audio_adjusted = change_audio_speed(audio_file, speed_factor)

    # Exportar el nuevo audio
    audio_adjusted.export("edu-definitivo.mp3", format="mp3")
    print("Ajuste de velocidad del audio completo.") 


     
    
   

        
    # subir volumen musica de fondo 
    
    #sub e le volumen de musica de fondo
    audio = AudioSegment.from_file("audio_de_fondo.mp3")
    # Aumento de volumen en decibelios (6 dB para duplicar el volumen)
    volume_increase_db = 2
    # Aumentar el volumen del audio
    audio_adjusted = audio + volume_increase_db
    # Exportar el nuevo audio
    audio_adjusted.export("audio_de_fondo.mp3", format="mp3") 
    print("se aumenta decibelios música de fondo")
    lista_de_eventos.append(f"{hora()} - Aumentar 2 decibelios para el fondo de audio")
        
    #combinar audio+ audio-fondo
    sound1 = AudioSegment.from_file("audio_de_fondo.mp3", format="mp3")
    sound2 = AudioSegment.from_file("edu-definitivo.mp3", format="mp3")
    overlay = sound2.overlay(sound1, position=0)    
    overlay.export("edu-mezclado.mp3", format="mp3")
    print("se ha mezclado audio y musica de fondo")
    lista_de_eventos.append(f"{hora()} - Se ha mezclado audio principal y fondo sonoro")
    
    
    # pegar audio y video
    
    """ videoclip = VideoFileClip("downloaded_video.mp4")
    audioclip = AudioFileClip("edu-mezclado.mp3")
    new_audioclip = CompositeAudioClip([audioclip])
    videoclip.audio = new_audioclip
    videoclip.write_videofile("output_video.mp4") """
    
    path_imagesource="downloaded_video.mp4"
    path_audiosource="edu-mezclado.mp3"
    out_video_path="output_video.mp4"
    video = ffmpeg.input(path_imagesource).video
    audio = ffmpeg.input(path_audiosource).audio
    ffmpeg.output(audio, video, out_video_path, vcodec='copy', acodec='copy').run() 
    print("se ha unido audio y video")
    lista_de_eventos.append(f"{hora()} - Se ha unido los audios correctamente. Fin del proceso")
      
    return jsonify({'data': 'ok'}) 

   

@app.route('/download')
def download():
    file_path = 'output_video.mp4'
    return send_file(file_path, as_attachment=True)
     
   
 
@app.route('/informacion')
def informacion():
    global lista_de_eventos
    global lista_de_errores    
    return render_template("informacion.html",lista_de_errores=lista_de_errores,lista_de_eventos=lista_de_eventos)
 



if __name__ == '__main__':
    app.run()
