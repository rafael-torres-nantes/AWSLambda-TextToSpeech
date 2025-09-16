# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# RUN LOCALY
from utils.check_aws import AWS_SERVICES

aws_services = AWS_SERVICES()
session = aws_services.login_session_AWS()
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import os
import json
import boto3
import time
from typing import Dict, Optional
from botocore.exceptions import BotoCoreError, ClientError

class TTSPollyService:
    """
    Serviço simplificado para Text-to-Speech usando Amazon Polly
    Focado em performance e qualidade de voz natural
    """
    
    def __init__(self, region_name: str = 'us-east-1', output_dir: str = None):
        """
        Inicializa o serviço Polly
        
        Args:
            region_name (str): Região AWS para o serviço Polly
            output_dir (str): Diretório para salvar arquivos de áudio (padrão: /tmp)
        """
        try:
            self.polly_client = session.client('polly', region_name=region_name)
            self.output_dir = output_dir or "/tmp"
            
            # Configuração padrão otimizada para voz natural e rápida
            self.default_config = {
                'voice_id': 'Joanna',
                'output_format': 'mp3',
                'sample_rate': '24000',
                'text_type': 'text',
                'language_code': 'en-US',
                'speed': 'medium',      # Added default speed
                'use_neural': True      # Added default for using neural engine
            }
            
            print(f'[DEBUG] TTS parameters configured:')
            print(f'        - Voice ID: {self.default_config["voice_id"]}')
            print(f'        - Format: {self.default_config["output_format"]}')
            print(f'        - Speed: {self.default_config.get("speed", "medium")}')
            print(f'        - Neural Engine: {"neural" if self.default_config.get("use_neural") else "standard"}')
            
            self.recommended_voices = {
                'female': ['Joanna', 'Kimberly', 'Salli', 'Kendra', 'Ivy'],
                'male': ['Matthew', 'Joey', 'Justin', 'Kevin'],
                'neural': ['Joanna', 'Matthew', 'Ivy', 'Justin', 'Kendra', 'Kimberly', 'Salli', 'Joey', 'Kevin']
            }
            
            os.makedirs(self.output_dir, exist_ok=True)
            
        except Exception as e:
            raise Exception(f"Erro ao inicializar TTSPollyService: {e}")

    def text_to_speech(self, text: str, voice_id: Optional[str] = None, speed: Optional[str] = None, use_neural: Optional[bool] = None) -> Dict:
        """
        Converte texto para fala usando Amazon Polly
        
        Args:
            text (str): Texto para conversão
            voice_id (str, optional): ID da voz a ser usada.
            speed (str, optional): Velocidade da fala ('x-slow', 'slow', 'medium', 'fast', 'x-fast').
            use_neural (bool, optional): Se deve usar o motor neural.
            
        Returns:
            dict: Resultado da conversão
        """
        try:
            start_time = time.time()
            
            # --- FIX 3: Prioritize passed arguments over defaults ---
            final_voice_id = voice_id or self.default_config['voice_id']
            final_speed = speed or self.default_config['speed']
            final_use_neural = use_neural if use_neural is not None else self.default_config['use_neural']
            
            processed_text = text.strip()
            if len(processed_text) > 3000:
                processed_text = processed_text[:2900] + "..."
            
            synthesis_params = {
                'Text': processed_text,
                'OutputFormat': self.default_config['output_format'],
                'VoiceId': final_voice_id,
                'LanguageCode': self.default_config['language_code'],
                'SampleRate': self.default_config['sample_rate']
            }
            
            if final_use_neural and final_voice_id in self.recommended_voices['neural']:
                synthesis_params['Engine'] = 'neural'
            else:
                synthesis_params['Engine'] = 'standard'
            
            if final_speed != 'medium':
                ssml_text = f'<speak><prosody rate="{final_speed}">{processed_text}</prosody></speak>'
                synthesis_params['Text'] = ssml_text
                synthesis_params['TextType'] = 'ssml'
            
            response = self.polly_client.synthesize_speech(**synthesis_params)
            
            timestamp = int(time.time() * 1000)
            filename = f"tts_audio_{timestamp}.{self.default_config['output_format']}"
            file_path = os.path.join(self.output_dir, filename)
            
            with open(file_path, 'wb') as audio_file:
                audio_file.write(response['AudioStream'].read())
            
            processing_time = time.time() - start_time
            file_size = os.path.getsize(file_path)
            
            chars_per_second = 165
            estimated_duration = len(text) / chars_per_second
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 3),
                'processing_time': round(processing_time, 2),
                'duration': round(estimated_duration, 2),
                'voice_id': final_voice_id,
                'output_format': self.default_config['output_format'],
                'engine': synthesis_params.get('Engine', 'standard'),
                'text_length': len(text),
                'processed_text_length': len(processed_text)
            }
            
        except (BotoCoreError, ClientError) as e:
            return {'success': False, 'error': str(e), 'error_type': 'aws_error'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'error_type': 'general_error'}
            
    def text_to_speech_streaming(self, text: str, voice_id: str = None) -> Dict:
        """
        Converte texto para fala usando streaming para textos longos

        Args:
            text (str): Texto para conversão
            voice_id (str, optional): ID da voz a ser usada.

        Returns:
            dict: Resultado da conversão
        """
        try:
            final_voice_id = voice_id or self.default_config['voice_id']
            chunks = self._split_text_for_streaming(text)
            
            timestamp = int(time.time() * 1000)
            filename = f"tts_streaming_{timestamp}.mp3"
            file_path = os.path.join(self.output_dir, filename)
            
            total_size = 0
            
            with open(file_path, 'wb') as output_file:
                for chunk in chunks:
                    response = self.polly_client.synthesize_speech(
                        Text=chunk,
                        OutputFormat='mp3',
                        VoiceId=final_voice_id,
                        Engine='neural' if final_voice_id in self.recommended_voices['neural'] else 'standard'
                    )
                    
                    chunk_data = response['AudioStream'].read()
                    output_file.write(chunk_data)
                    total_size += len(chunk_data)
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'file_size_bytes': total_size,
                'file_size_mb': round(total_size / (1024 * 1024), 3),
                'chunks_processed': len(chunks),
                'voice_id': final_voice_id
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _split_text_for_streaming(self, text: str, max_length: int = 2500) -> list:
        """
        Divide texto em chunks para processamento streaming
        """
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def cleanup_temp_files(self, max_age_minutes: int = 60) -> int:
        """
        Remove arquivos temporários antigos

        Args:
            max_age_minutes (int): Idade máxima dos arquivos em minutos para serem mantidos
        """
        try:
            removed_count = 0
            current_time = time.time()
            max_age_seconds = max_age_minutes * 60
            
            # Remove only files created by this service
            for filename in os.listdir(self.output_dir):

                # Consider only files starting with 'tts_'
                if filename.startswith('tts_'):
                    file_path = os.path.join(self.output_dir, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    # Remove files older than max_age_seconds
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        removed_count += 1
            
            return removed_count
        except Exception as e:
            return 0

# --- FIX 4: Update quick_tts to pass arguments correctly ---
def quick_tts(text: str, voice: str = 'Joanna', speed: str = 'medium') -> str:
    """
    Função rápida para TTS simples
    """
    try:
        tts = TTSPollyService()
        # The method now correctly accepts these named arguments
        result = tts.text_to_speech(text=text, voice_id=voice, speed=speed)
        
        if result.get('success'):
            return result.get('file_path')
        else:
            print(f"Error in quick_tts: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"Exception in quick_tts: {e}")
        return None

# Teste do serviço (apenas para desenvolvimento local)
if __name__ == "__main__":
    tts_service = TTSPollyService()
    
    test_text = "Hello! This is a test of our fast and natural text-to-speech system using Amazon Polly."
    
    # This call now works correctly with the updated method signature
    result = tts_service.text_to_speech(
        text=test_text,
        voice_id='Joanna',
        speed='fast',
        use_neural=True
    )
    
    if result.get('success'):
        print(f"\n✅ TTS Test Success!")
        print(f"   File: {result['filename']}")
        print(f"   Size: {result['file_size_mb']} MB")
        print(f"   Estimated Duration: {result['duration']} seconds")
        print(f"   Processing Time: {result['processing_time']} seconds")
        print(f"   Engine Used: {result['engine']}")
    else:
        print(f"\n❌ TTS Test Failed: {result.get('error')}")