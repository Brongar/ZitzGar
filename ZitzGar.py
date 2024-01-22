# Importa as bibliotecas necessárias
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import threading # Módulo para possibilitar a programação concorrente
import queue # Módulo para implementar filas
import speech_recognition as sr # Biblioteca para reconhecimento de fala
import os

#----------------------------------------------------------------------------
def transcrever(fila_audio, evento_parada):
    """
    Transcreve trechos de áudio da fila e os adiciona à lista de texto.
    Para quando o evento de parada é acionado.
    """
    recognizer = sr.Recognizer()

    while not evento_parada.is_set():
        # Verifica se a fila não está vazia
        if not fila_audio.empty():
            audio_data = fila_audio.get()
            fila_audio.task_done()

            if audio_data is None:
                continue

            # Reconhece a fala e trata os erros
            try:
                texto = recognizer.recognize_google_cloud(audio_data, language="pt-BR")

                # Tokeniza o texto
                inputs = tokenizer(texto, return_tensors="pt")

                # Gera a tradução
                outputs = model.generate(**inputs, max_length=50, num_beams=4, length_penalty=1.0, early_stopping=True)
                decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

                # Ajusta o texto traduzido
                nova_frase = ajuste_caractere(decoded_output, diacriticos)

                # Exibe a tradução
                print("Tradução:", nova_frase.upper())

                # Verifica o comando de parada
                if texto.lower() == "parar test ":
                    evento_parada.set()

            except sr.UnknownValueError:
                print("Não foi possível reconhecer a fala.")
            except sr.RequestError as e:
                print(f"Erro ao solicitar o reconhecimento: {e}")

def capturar_audio(reconhecedor, microfone, fila_audio, evento_parada):
    """
    Captura trechos de áudio do microfone e os coloca na fila.
    Para quando o evento de parada é acionado.
    """
    while not evento_parada.is_set():
        with microfone as source:
            print("Aguardando fala...")
            try:
                # Captura áudio com detecção automática de início e fim da fala
                audio_data = reconhecedor.listen(source, timeout=None, phrase_time_limit=3)
                fila_audio.put(audio_data)
            except sr.WaitTimeoutError:
                print("Nenhuma fala detectada.")

# Exemplo de função de ajuste de caracteres
def ajuste_caractere(frase, diacriticos):
    for diacritico in diacriticos:
        posicao_diacritico = frase.find(diacritico)
        while posicao_diacritico != -1:
            posicao_primeiro_espaco = frase.find(' ', posicao_diacritico + 1)
            if posicao_primeiro_espaco != -1:
                parte1 = frase[:posicao_primeiro_espaco]
                parte2 = frase[posicao_primeiro_espaco + 1:]
                frase = parte1 + parte2
            else:
                break
            posicao_diacritico = frase.find(diacritico, posicao_diacritico + 1)
    return frase

# Carrega o tokenizador e o modelo treinado do diretório local
checkpoint = "ajustado"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint)

if __name__ == "__main__":
    # Inicializa os recursos
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '../APIGoogleKey/librasc3-1c891ff849f3.json'
    reconhecedor = sr.Recognizer()
    microfone = sr.Microphone()
    evento_parada = threading.Event()
    fila_audio = queue.Queue()

    # Cria e inicia as threads
    thread_transcricao = threading.Thread(target=transcrever, args=(fila_audio, evento_parada))
    thread_captura = threading.Thread(target=capturar_audio, args=(reconhecedor, microfone, fila_audio, evento_parada))

    thread_transcricao.start()
    thread_captura.start()

    # Aguarda o término das threads
    try:
        thread_captura.join()
        thread_transcricao.join()

    except KeyboardInterrupt:
        print("Encerrado pelo usuário.")

    # Imprime a mensagem final
    print("Threads finalizadas.")
