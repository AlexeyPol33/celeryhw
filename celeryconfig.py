from kombu import Queue, Exchange




broker_url = 'redis://127.0.0.1:6379/0'
result_backend = 'redis://127.0.0.1:6379/1'

task_queues = (

    Queue('default', Exchange('default'),routing_key='default'),
    Queue('decode_image_queue', Exchange('decode_image_ex'),routing_key='decode_image_route'),
    Queue('get_scaler_queue', Exchange('get_scaler_ex'),routing_key='get_scaler_route'),
    Queue('send_image_queue',Exchange('send_image_ex'),routing_key='send_image_route'),
    Queue('upscale_image_queue',Exchange('upscale_image_ex'),routing_key='upscale_image_route'),
)

task_routes = {
    'main.decode_image':{'queue':'decode_image_queue','routing_key': 'decode_image_route','priority':10},
    'main.get_scaler':{'queue':'get_scaler_queue','routing_key': 'get_scaler_route','priority':1},
    'main.send_image':{'queue':'send_image_queue','routing_key':'send_image_route','priority':1},
    'main.upscale_image':{'queue':'upscale_image_queue','routing_key':'upscale_image_route','priority':1}
}