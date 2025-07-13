#!/usr/bin/env python3
"""
Скрипт для инициализации S3 bucket в LocalStack
"""

import boto3
import os
import time
import requests
from botocore.exceptions import ClientError


def wait_for_localstack():
    """Ожидание готовности LocalStack"""
    print("⏳ Ожидание готовности LocalStack...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:4566/_localstack/health", timeout=5)
            if response.status_code == 200:
                print("✅ LocalStack готов к работе")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"  Попытка {attempt + 1}/{max_attempts}...")
            time.sleep(2)
    
    print("❌ LocalStack не отвечает")
    return False


def init_localstack():
    """Инициализация LocalStack S3"""
    
    # Настройки для LocalStack
    endpoint_url = "http://localhost:4566"
    bucket_name = "events-bot-uploads"
    
    # Ждем готовности LocalStack
    if not wait_for_localstack():
        print("❌ Не удалось дождаться готовности LocalStack")
        print("Убедитесь, что LocalStack запущен:")
        print("docker-compose -f docker-compose-dev.yaml up localstack")
        return False
    
    # Создаем клиент S3
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    print(f"🔧 Инициализация LocalStack S3...")
    print(f"Endpoint: {endpoint_url}")
    print(f"Bucket: {bucket_name}")
    
    try:
        # Проверяем, существует ли bucket
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' уже существует")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket не существует, создаем его
                print(f"📦 Создаем bucket '{bucket_name}'...")
                s3_client.create_bucket(Bucket=bucket_name)
                print(f"✅ Bucket '{bucket_name}' создан успешно")
            else:
                raise
        
        # Настраиваем CORS для bucket (если нужно)
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['ETag']
            }]
        }
        
        try:
            s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
            print("✅ CORS настроен для bucket")
        except Exception as e:
            print(f"⚠️ Не удалось настроить CORS: {e}")
        
        # Тестируем загрузку файла
        test_data = b"test file content"
        test_key = "test.txt"
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_data
            )
            print(f"✅ Тестовая загрузка файла '{test_key}' успешна")
            
            # Удаляем тестовый файл
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            print(f"✅ Тестовый файл '{test_key}' удален")
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании загрузки: {e}")
        
        print("\n🎉 LocalStack S3 инициализирован успешно!")
        print(f"Bucket: {bucket_name}")
        print(f"Endpoint: {endpoint_url}")
        print("Теперь можно использовать S3 функциональность локально")
        print("\nДля запуска полной среды разработки:")
        print("docker-compose -f docker-compose-dev.yaml up -d")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации LocalStack: {e}")
        print("Убедитесь, что LocalStack запущен: docker-compose -f docker-compose-dev.yaml up localstack")
        return False


if __name__ == "__main__":
    init_localstack() 