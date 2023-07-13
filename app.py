import time, os, cv2
from flask import Flask, request, jsonify, send_file,url_for, make_response
from numpy import frombuffer, uint8,array
from flask.views import MethodView
from celery import Celery
from celery.result import AsyncResult
from cv2 import dnn_superres
import logging
import json
import io

app_name='app'
app=Flask(app_name)
app.config['UPLOAD_FOLDER']='files'
celery=Celery(
    app_name,
    backend='redis://redis:6379/1',
    broker='redis://redis:6379/2',
    
)
celery.conf.update(app.config)

logging.getLogger('celery').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

class ContextTask(celery.Task):
    def call(self, *args,**kwargs):
        with app.app_context():
            return self.run(args,**kwargs)
        
celery.Task=ContextTask

class HttpError(Exception):
    def __init__(self,status_code, message) -> None:
        self.status_code = status_code
        self.message = message
  
@app.errorhandler(HttpError)
def http_error_handler(error: HttpError):
    error_message = {"status":"error", "descriprion": error.message}
    response=jsonify(error_message)
    response.status_code=error.status_code
    return response

def get_scaler(model_path: str = 'EDSR_x2.pb'):
    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    LOGGER.info('загрузка scaler завершина')
    return scaler

SCALER = get_scaler()

def decode_image(bimage):
    nparr = frombuffer(bimage, uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    
    return image

@celery.task
def upscale(bimage:bytes) -> hex:
    image = decode_image(bimage)
    try:
        result = SCALER.upsample(image)
        return result.tolist()
    except:
        return None
    


@app.route('/home',methods = ['GET'])
def home_page():
    LOGGER.info('Запрос домашней страницы')
    return 'Домашняя страница '

@app.route('/upscale',methods = ['POST'] )
def post_upscale():
    
    file = request.files['image'].read()
    try:
        filename = request.files['image'].filename
        LOGGER.info(f'Загружен файл с названием {filename}')
    except:
        LOGGER.info(f'Загружен файл без имени')
    delay = upscale.delay(file)
    response = make_response(jsonify({'task_id': delay.id}), 201)
    return response


@app.route('/upscale/status', methods=['GET'])
def get_task_status():
    task_id = request.json['task_id']
    task = AsyncResult(task_id, app=celery)
    
    # Проверяем статус задачи
    if task.ready():
        # Если задача выполнена, возвращаем результат
        LOGGER.info('запрос завершенной задачи')
        try:
            if task.get() == None:
                LOGGER.info('Ошибка обработки файла')
                raise HttpError(400,'err file cannot be scaled')
        except:
            LOGGER.info('Ошибка celery на сервере')
            raise HttpError(400,'err file cannot be scaled')
        upload_url = url_for('upload_image', file=task.id,_external=True)
        return jsonify({'status': 'completed','url':upload_url})
    else:
        # Если задача еще выполняется, возвращаем статус "в процессе"
        LOGGER.info('запрос статуса не завершенной задачи')
        return jsonify({'status': 'processing'})

@app.route('/processed/<file>')
def upload_image(file):
    task = AsyncResult(file,app=celery)

    if task.ready():
        image_array = array(task.get(), dtype=uint8)
        success, encoded_image = cv2.imencode('.png', image_array)
        encoded_image = io.BytesIO(encoded_image.tobytes())
        return send_file(encoded_image,mimetype='image/png',as_attachment=True,download_name=f'{task.id}.png')
    


if __name__ == '__main__':
    app.run(host='0.0.0.0')