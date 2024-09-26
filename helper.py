import time
import random
import qrcode


def generate_rid():
    e = int(time.time())
    t = hex(e)[2:]
    e = ''.join(random.choice('01234567') for _ in range(8))
    return t + '-' + e


def convert_cookie(cookies):
    ret = ''
    for name, value in cookies:
        ret += '{0}={1};'.format(name, value)
    return ret


def create_qc_code(url):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("finder_login_code.png")