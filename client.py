import requests

URL = 'http://127.0.0.1:5000'

def post (path):
    with open (path,'rb') as file:
        files = {'image':file}
        response = requests.post(URL + '/upscale',files=files)
    return response

def get():
    pass


if __name__ == '__main__':
    print(post('lama_300px.png'))
    pass