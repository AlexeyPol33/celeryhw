import cv2
from cv2 import dnn_superres
from numpy import frombuffer, uint8



def get_scaler(model_path: str = 'EDSR_x2.pb'):
    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    return scaler

def decode_image(bimage):
    image = cv2.imdecode(frombuffer(bimage,uint8),cv2.IMREAD_UNCHANGED)
    return image

def write_image(path,image):
    
    cv2.imwrite(path, image)


def upscale(image, scaler) -> None:
   
    result = scaler.upsample(image)
    return result


def example():
    upscale('lama_300px.png', 'lama_600px.png')


if __name__ == '__main__':
    example()