# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# RUN LOCALY
from utils.check_aws import AWS_SERVICES

aws_services = AWS_SERVICES()

session = aws_services.login_session_AWS()

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #

import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError

class S3BucketClass: 
    def __init__(self):
        """
        Construtor da classe S3BucketClass que inicializa o cliente S3 da sessão.
        """

        # Cria uma sessão AWS usando as credenciais configuradas
        self.s3_client = session.client('s3', region_name='ca-central-1')

        # Define o caminho de download para os arquivos baixados do S3
        self.download_path = './tmp/' 

        # Cria o diretório de download se não existir
        os.makedirs(self.download_path, exist_ok=True)
    
    def upload_file(self, file_path: str, bucket: str, key: str) -> bool:
        """
        Função para fazer upload de um arquivo para o bucket S3

        Args:
            file_path (str): Caminho do arquivo a ser enviado
            bucket (str): Nome do bucket S3
            key (str): Nome do arquivo no bucket
        """
        try:
            # Upload do arquivo para o bucket S3
            self.s3_client.upload_file(file_path, bucket, key)
            return True
        
        except ClientError as e:
            print(f"[DEBUG] Erro ao fazer upload do arquivo para o S3: {e}")
            raise
    
    def download_file(self, bucket: str, key: str, filename : str = None) -> bool:
        """
        Download de um arquivo do bucket S3 para o caminho especificado

        Args:
            bucket (str): Nome do bucket S3
            key (str): Nome do arquivo no bucket
            filename (str): Nome do arquivo local para salvar o download
        """

        if not filename:
            # Caminho do arquivo para download
            file_path = os.path.join(self.download_path, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if filename:
            # Caminho do arquivo para download
            file_path = os.path.join(self.download_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Download do arquivo do bucket S3
            self.s3_client.download_file(bucket, key, file_path)
            return file_path
        
        except ClientError as e:
            print(f"[DEBUG] Erro ao fazer download do arquivo do S3: {e}")
            raise e
              
    def delete_object(self, bucket: str, key: str) -> bool:
        """
        Deleta um objeto do bucket S3 especificado por chave

        Args:
            bucket (str): Nome do bucket S3
            key (str): Nome do arquivo no bucket
        """
        try:
            # Deleta o objeto do bucket S3 especificado
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        
        except ClientError as e:
            print(f"[DEBUG] Erro ao deletar objeto do S3: {e}")
            raise e
    
    def get_object(self, bucket: str, key: str) -> Optional[dict]:
        """
        Obter um objeto do bucket S3 especificado por chave

        Args:
            bucket (str): Nome do bucket S3
            key (str): Nome do arquivo
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response
        
        except ClientError as e:
            print(f"[DEBUG] Erro ao obter objeto do S3: {e}")
            raise
    
    def generate_presigned_url(self, bucket: str, key: str) -> str:
        """
        Gerar uma URL pré-assinada para um objeto no bucket S3

        Args:
            bucket (str): Nome do bucket S3
            key (str): Nome do arquivo
        """
        try:
            # Gerar URL pré-assinada para o objeto no bucket S3
            presigned_url = self.s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key})
            return presigned_url
       
        except ClientError as e:
            print(f"[DEBUG] Error generating presigned URL: {e}")


    def create_presigned_post(self, bucket, object_name,
                            fields=None, conditions=None, expiration=3600):
        """
        Função para gerar uma URL pré-assinada para upload de um arquivo para o bucket S3
        
        Args:
            object_name (str): Nome do arquivo
            fields (dict): Campos de formulário para incluir na URL
            conditions (list): Condições de formulário para incluir na URL
            expiration (int): Tempo de expiração da URL em segundos
        
        Returns:
            dict: Dicionário contendo a URL pré-assinada e os campos de formulário necessários
        """

        # Generate a presigned S3 POST URL
        try:
            response = self.s3_client.generate_presigned_post(bucket,
                                                        object_name,
                                                        Fields=fields,
                                                        Conditions=conditions,
                                                        ExpiresIn=expiration)
        except ClientError as e:
            print(f"[DEBUG] Error generating presigned POST URL: {e}")

        # The response contains the presigned URL and required fields
        return response
    
    def upload_dir(self, bucket: str, key: str, dir_path: str):
        """
        Função para fazer upload de um diretório para o bucket S3

        Args:
            bucket (str): Nome do bucket S3
            key (str): Nome do arquivo no bucket
            dir_path (str): Caminho do diretório a ser enviado
        """
        try:
            # Upload do diretório para o bucket S3
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    key_path = os.path.join(key, file)
                    self.s3_client.upload_file(file_path, bucket, key_path)
            return True
        
        except ClientError as e:
            print(f"[DEBUG] Erro ao fazer upload do diretório para o S3: {e}")
            raise e 
    
    def download_all_files(self, bucket: str, prefix: str = '', sufix: str = '') -> list:
        """
        Realiza o download de todos os arquivos de um bucket S3, opcionalmente
        filtrando por um prefixo e/ou sufixo específico
        
        Args:
            bucket (str): Nome do bucket S3
            prefix (str, optional): Prefixo para filtrar os objetos. Defaults to ''.
            sufix (str, optional): Sufixo para filtrar os objetos. Defaults to ''.
        
        Returns:
            list: Lista com os caminhos locais dos arquivos baixados
        """
        downloaded_files = []
        
        try:
            # Lista todos os objetos no bucket com o prefixo especificado
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
            
            for page in page_iterator:
                if 'Contents' not in page:
                    print(f"[DEBUG] Nenhum arquivo encontrado no bucket {bucket} com prefixo {prefix}")
                    return downloaded_files
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    # Ignora "pastas" (objetos que terminam com /)
                    if key.endswith('/'):
                        continue
                    
                    # Verifica se o arquivo termina com o sufixo especificado (se fornecido)
                    if sufix and not key.endswith(sufix):
                        continue
                        
                    # Cria diretórios locais se necessário                   
                    local_filepath = os.path.join(self.download_path, key)
                    os.makedirs(os.path.dirname(local_filepath), exist_ok=True)
                    
                    # print(f"[DEBUG] Baixando {key} para {local_filepath}")
                    self.s3_client.download_file(bucket, key, local_filepath)
                    downloaded_files.append(local_filepath)
                    
            return downloaded_files
            
        except ClientError as e:
            print(f"[DEBUG] Erro ao fazer download de todos os arquivos do S3: {e}")
            raise e
        
    
    def list_files(self, bucket: str, prefix: str = '', sufix: str = '') -> list:
        """
        Lista todos os arquivos de um diretório no bucket S3, opcionalmente
        filtrando por um prefixo específico

        Args:
            bucket (str): Nome do bucket S3
            prefix (str, optional): Prefixo para filtrar os objetos. Defaults to ''.
            sufix (str, optional): Sufixo para filtrar os objetos. Defaults to ''.

        Returns:
            list: Lista com os nomes dos arquivos no bucket
        """
        files = []

        try:
            # Lista todos os objetos no bucket com o prefixo especificado
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

            for page in page_iterator:
                if 'Contents' not in page:
                    print(f"[DEBUG] Nenhum arquivo encontrado no bucket {bucket} com prefixo {prefix}")
                    return files
                
                for obj in page['Contents']:
                    key = obj['Key']
                    # Ignora "pastas" (objetos que terminam com /)
                    if key.endswith('/'):
                        continue

                    # Verifica se o arquivo termina com o sufixo especificado (se fornecido)
                    if sufix and not key.endswith(sufix):
                        continue
                    
                    files.append(key)

            return files

        except ClientError as e:
            print(f"[DEBUG] Erro ao listar arquivos do S3: {e}")
            raise e
        

    def get_file_size(self, bucket: str, key: str) -> float:
        """
        Obter o tamanho de um arquivo no bucket S3 em MB

        Args:
            bucket (str): Nome do bucket S3
            key (str): Nome do arquivo no bucket
            
        Returns:
            float: Tamanho do arquivo em MB
        """
        try:
            # Obter metadados do objeto para extrair o tamanho
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            size_bytes = response['ContentLength']
            
            # Converter bytes para MB (1 MB = 1024 * 1024 bytes)
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 2)
        
        except ClientError as e:
            print(f"[DEBUG] Erro ao obter tamanho do arquivo do S3: {e}")
            raise e