
from flask import Flask, jsonify, request
from celeryapp import make_celery
import upscale

app = Flask(__name__)
app.config.update(
    
    CELERY_BROKER_URL='redis://127.0.0.1:6379',
    CELERY_RESULT_BACKEND='redis://127.0.0.1:6379'
)

celery = make_celery(app)
@celery.task
def get_scaler():
    return upscale.get_scaler()

@celery.task
def decode_image(bimage):
    return upscale.decode_image(bimage)

@celery.task
def send_image():
    return upscale.write_image()

@celery.task
def upscale_image(image,scaler):
    return upscale.upscale(image,scaler)


@app.route('/upscale',methods = ['POST'] )
def post_upscale():
    file = request.files['image'].read()
    delay = decode_image.delay(file)
    print('id задачи:',delay.id)
    print('статус задачи:',delay.status)
    print('get задачи:',delay.get())
    return 'test upscale'


@app.route('/tasks/<task_id>', methods = ['GET'])
def get_tasks(task_id):

    return f'test tasks{task_id}'


@app.route('/processed/<file>', methods = ['GET'])
def get_photo(file):

    return f'test processed{file}'


if __name__ == '__main__':
    app.run()