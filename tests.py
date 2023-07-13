from numpy import frombuffer, uint8,array
from io import BytesIO
import requests
import time
import pytest
import cv2
import os



URL = 'http://localhost:5000'
FILE_PATH = 'images'
ERROR_FILES_PATH = 'errors_files'

@pytest.fixture
def images_fixture():
    images_list = os.listdir(path=FILE_PATH)
    images_bytes = {}
    for image in images_list:
        cv_image = cv2.imread(f'{FILE_PATH}/{image}')
        height, width = cv_image.shape[:2]
        with open (f'{FILE_PATH}/{image}', 'rb') as f:
            images_bytes[image] = {'height':height,'width':width,'file':BytesIO(f.read())}
    return images_bytes

@pytest.fixture
def error_files_fixture():
    
    images_list = os.listdir(path=ERROR_FILES_PATH)
    images_bytes = {}
    for image in images_list:
        with open (f'{ERROR_FILES_PATH}/{image}', 'rb') as f:
            images_bytes[image] = {'file':BytesIO(f.read())}
    return images_bytes


def test_connection():
    print('test_connection')
    response = requests.get(URL + '/home')
    assert response.status_code == 200
    
def test_server_full(images_fixture):

    print('test_server_full')
    tasks = {}
    for photo in images_fixture:
        file = {'image': images_fixture[photo]['file']}
        response = requests.post(URL + '/upscale', files=file)
        assert response.status_code == 201
        tasks[photo] = {'id':response.json()['task_id']}

    results = {}
    for task in tasks:
        id = tasks[task]['id']
        response = requests.get(URL + '/upscale/status',json={'task_id':id})
        assert response.status_code == 200
        response_json = response.json()
        while response_json['status'] != 'completed':
            print (response_json['status'])
            time.sleep(2)
            response_json = requests.get(URL + '/upscale/status',json={'task_id':id}).json()
            assert response.status_code == 200
        results[task] = {'url':response_json['url']}

    downloads = {}
    for result in results:
        url = results[result]['url']
        response = requests.get(url)
        assert response.status_code == 200
        downloads[result] = response.content

    for download in downloads:
        bimage = downloads[download]
        nparr = frombuffer(bimage, uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        base_height = images_fixture[download]['height']
        base_width = images_fixture[download]['width']
        new_height, new_width = image.shape[:2]

        assert new_height == base_height * 2
        assert new_width == base_width * 2

def test_upload_error_files(error_files_fixture):
    print('test_upload_error_files')
    for file in error_files_fixture:
        image = {'image': error_files_fixture[file]['file']}
        response = requests.post(URL + '/upscale', files=image)
        print(f'загружен файл с кодом {response.status_code}')
        if response.status_code == 201:
            task_id = response.json()['task_id']
            response = requests.get(URL + '/upscale/status', json={'task_id':task_id})
            print (f'Запрошен статус обработки {response.status_code}')
            while True:
                print ('Ожидание завершения обработки')
                if response.status_code == 200:
                    response_json = response.json()
                    if response_json['status'] == 'completed':
                        assert False
                        break
                    time.sleep(2)
                    response = requests.get(URL + '/upscale/status', json={'task_id':task_id})
                elif response.status_code == 400:
                    assert True
                    break
                else:
                    assert False
        elif response == 400:
            assert True
            continue
        else:
            assert False