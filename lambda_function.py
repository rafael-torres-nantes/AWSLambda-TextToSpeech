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
        "text": """The transmission began as a whisper, faint and broken, bouncing across the void of space. No one on the Odyssey was supposed to be awake when it arrived, yet something—or someone—adjusted the comms array just enough for the signal to slip through.

        Lieutenant Mara Vey rubbed her eyes as the console flickered. The hum of the ship’s life-support systems was the only constant sound in the otherwise silent monitoring bay. She leaned forward, watching as fragmented audio pulsed across the screen.

        “—help us—coordinates—”

        Mara froze. Every distress call received in deep space was routed through the central relay station near Titan. The Odyssey, patrolling near the edges of the Perseus Expanse, shouldn’t have been able to intercept it.

        She replayed the fragment. Same broken words. Same static.

        Her hand hovered over the ship’s log recorder. Do I wake the captain? Protocol demanded it, but curiosity rooted her in place. Mara had grown tired of routine patrols, endless scans of empty sectors. This… this was different.

        She typed the coordinates into the navigation system. A red warning blinked instantly: RESTRICTED SECTOR – UNCHARTED.

        That made her blood run cold. The Expanse was known for its anomalies: gravitational rifts, silent derelicts, stories told by exhausted crews after too many months in isolation.

        Still, the voice in the transmission sounded human. Desperate.

        Mara whispered to herself, “Just a quick look. 
        Three hours later, the Odyssey drifted through a debris field. Shattered hulls floated silently, their insignias unrecognizable. Some ships looked decades old, others impossibly ancient, their designs alien and jagged, like bones picked clean.

        The signal grew stronger.

        “—anyone hearing this—please respond—”

        This time, the voice was clearer. A woman’s voice, trembling with fear.

        Mara opened a channel. “This is Lieutenant Vey of the U.N.S. Odyssey. Identify yourself.”

        Static swallowed her words. Then, after a long pause:

        “Odyssey… you shouldn’t have come.”

        Before Mara could reply, proximity alarms screamed. Dozens of small objects detached from the wreckage, moving with unsettling precision. At first glance they looked like drones, but their forms shifted as if liquid metal clung to an invisible skeleton.

        They swarmed toward the Odyssey.

        “Defense grid online,” the ship’s AI announced calmly. Turrets emerged, blasting arcs of plasma into the dark. But each impact only scattered fragments, which reassembled in moments.

        Mara’s stomach knotted. “Not drones. Organisms.”

        The voice returned, louder now, cutting through the chaos:

        “You can’t fight them. Leave before they notice you.”

        Mara yelled at the comm. “Who are you? Where are you transmitting from?”

        Her radar pinged a location deep within the wreckage—a massive ship, its hull fractured yet still intact enough to dwarf the Odyssey. Symbols unlike any human language crawled across its surface, glowing faintly.

        The signal originated from inside.

        Against every regulation drilled into her, Mara locked the Odyssey onto the derelict’s docking bay. The AI protested, but she overrode the system.

        When the airlock opened, stale air and the faint smell of rust greeted her. She stepped inside, flashlight cutting through the dark. Shadows of alien architecture stretched across the walls, twisted and unsettling, as if grown rather than built.

        “Hello?” she called.

        Her voice echoed endlessly.

        Then—movement. A figure stumbled from the shadows. Human. Pale. Wearing a torn flight suit with an old Earth insignia.

        Mara’s heart raced. “Impossible. That crest was retired a century ago.”

        The woman lifted her head. Her eyes shimmered with unnatural light. “You shouldn’t have come,” she repeated, voice shaking. “They’re learning. Every rescue attempt makes them stronger.”

        Mara stepped closer. “Who are they?”

        The woman opened her mouth to answer, but a low vibration shook the entire derelict. Metal groaned as if the ship itself was alive. From the walls, liquid shadows began to drip, pulling themselves into humanoid forms.

        The woman grabbed Mara’s wrist with a strength that felt inhuman. “Run.”

        Mara barely made it back through the airlock as the derelict shuddered violently. The Odyssey’s AI screamed alerts: “Unidentified lifeforms detected. Hull breach imminent.”

        The swarm followed, slamming against the outer bulkhead like a rising tide.

        Mara sealed the hatch, lungs burning. “Get us out of here!”

        Engines roared. The Odyssey pulled free, but fragments of the swarm clung to the hull, their shapes already mimicking the ship’s armor.

        On the comm, the woman’s voice whispered one final time:

        “You brought them with you.”

        The stars stretched into streaks as the Odyssey jumped to faster-than-light. Mara collapsed into her chair, trembling. The console flickered with new messages—dozens of them—each identical to the one she’d first intercepted.

        “Help us. Coordinates—”

        Except now, every transmission carried her own voice.
        """,
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