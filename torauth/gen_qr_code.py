import io
import base64
import qrcode


def gen_qr_code(deep_link_url: str, seq: str, rand: str, webhook_url: str) -> str:
    """ Function returns image in a .png format encoded as a base64 string
    :params deep_link_url: string
    :params random: string
    :return: base64 string
    """
    # TODO: move QRcode params into config.py
    qr = qrcode.QRCode(
        version=1,
        border=4,
        box_size=10,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
    )

    qr.add_data(deep_link_url + ','.join([rand, seq, webhook_url]))
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    stream = io.BytesIO()
    img.save(stream, 'PNG')
    base64png = base64.b64encode(stream.getvalue()).decode('utf-8')
    stream.close()
    return base64png
