    audio_file = "audio_espanol.mp3"
    video_file = "downloaded_video.mp4"
    audio_duration = len(AudioSegment.from_file(audio_file)) / 1000  # Duración en segundos
    video_duration = VideoFileClip(video_file).duration  # Duración en segundos

    # Factor de velocidad (1.2 para acelerar en 20%)
    speed_factor = video_duration/audio_duration

    # Cambiar la velocidad del audio
    def change_audio_speed(sound, speed=1.0):
        sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * speed)
        })
        return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    audio_adjusted = change_audio_speed(audio_file, speed_factor)
    # Exportar el nuevo audio
    audio_adjusted.export("edu-definitivo.mp3", format="mp3")
    
    
     