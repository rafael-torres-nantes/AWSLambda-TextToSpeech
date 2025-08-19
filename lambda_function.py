import os
import json
import base64
from dotenv import load_dotenv

# Importar as classes de serviços necessárias para a Lambda Function
from services.polly_services import TTSPollyService

load_dotenv()

# Obtém o diretório temporário do arquivo .env
TMP_DIR = os.getenv('TMP_DIR', './tmp')

# ============================================================================
# Função Lambda para Text-to-Speech usando Amazon Polly (Processamento Local)
# ----------------------------------------------------------------------------
def lambda_handler(event, context):
    """
    Função Lambda para converter texto em fala usando Amazon Polly
    Processamento totalmente local, sem armazenamento em S3
    """
    
    # 1 - Imprime o evento recebido
    print('*********** Start TTS Lambda ***************') 
    print(f'[DEBUG] Event: {event}') 
    
    # 2 - Garantir que o diretório temporário existe
    os.makedirs(TMP_DIR, exist_ok=True)
    print(f'[DEBUG] Temporary directory configured: {TMP_DIR}')
    
    try:
        
        # 3 - Validar entrada obrigatória
        if 'text' not in event:
            raise ValueError("Field 'text' is required")
        
        text = event.get('text')
        if not text or len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")
        
        print(f'[DEBUG] Text for conversion (length: {len(text)} characters): {text[:100]}...')
        
        # 4 - Obter parâmetros opcionais com valores padrão
        voice_id = event.get('voice_id', 'Joanna')
        output_format = event.get('output_format', 'mp3')
        speed = event.get('speed', 'medium')
        use_neural = event.get('use_neural', True)
        
        print(f'[DEBUG] TTS parameters configured:')
        print(f'        - Voice ID: {voice_id}')
        print(f'        - Format: {output_format}')
        print(f'        - Speed: {speed}')
        print(f'        - Neural Engine: {use_neural}')
        
        # 5 - Instanciar serviço TTS com diretório temporário personalizado
        tts_service = TTSPollyService(output_dir=TMP_DIR)
        print(f'[DEBUG] TTS service successfully initialized')
        
        # 6 - Converter texto para fala
        audio_result = tts_service.text_to_speech(
            text=text,
            voice_id=voice_id,
            output_format=output_format,
            speed=speed,
            use_neural=use_neural
        )
        
        # 7 - Verificar se a conversão foi bem-sucedida
        if not audio_result['success']:
            raise Exception(f"TTS conversion error: {audio_result['error']}")
        
        print(f'[DEBUG] TTS conversion completed successfully:')
        print(f'        - File: {audio_result["filename"]}')
        print(f'        - Size: {audio_result["file_size_mb"]} MB')
        print(f'        - Duration: {audio_result["duration"]} seconds')
        print(f'        - Processing time: {audio_result["processing_time"]} seconds')
        
        local_file_path = audio_result['file_path']
        
        # 8 - Ler o arquivo de áudio e converter para base64
        with open(local_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        print(f'[DEBUG] File converted to base64 (size: {len(audio_base64)} characters)')
        
        # 9 - Obter informações do arquivo para resposta
        file_size_bytes = len(audio_data)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        relative_path = os.path.relpath(local_file_path, os.getcwd())
        
        # 10 - Preparar resposta de sucesso
        response_data = {
            'success': True,
            'message': 'Text successfully converted to speech',
            'audio_data': audio_base64,
            'voice_id': voice_id,
            'file_size_mb': file_size_mb,
            'duration': audio_result.get('duration', 0),
            'processing_time': audio_result.get('processing_time', 0)
        }
        
        print(f'[DEBUG] Response prepared successfully')
        print('*********** End TTS Lambda ***************')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f'[ERROR] Internal error: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'message': str(e)
            })
        }


# Teste da função lambda (apenas para desenvolvimento local)
if __name__ == "__main__":
    test_event = {
        "text": "Hello! This is a simple test of our text-to-speech conversion system.",
        "voice_id": "Joanna",  # English voice
        "output_format": "mp3",
        "speed": "medium"
    }
    
    print("Running lambda function test...")
    result = lambda_handler(test_event, None)
    
    # Exibir resultado do teste (sem o audio_data para não poluir o console)
    body = json.loads(result['body'])
    if 'audio_data' in body:
        audio_length = len(body['audio_data'])
        body['audio_data'] = f"[Base64 data - {audio_length} characters]"
    
    print("Test result:")
    print(json.dumps(body, indent=2, ensure_ascii=False))