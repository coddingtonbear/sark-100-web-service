from base64 import b64encode
import json
import logging

from flask import Flask, make_response, render_template, request
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from six import StringIO

from .device import scan_range


logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.errorhandler(500)
def error_encountered(e):
    return render_template(
        'error.html',
        error=e
    )


@app.route('/api/get-samples', methods=['POST'])
def api():
    frequency_start = request.form.get('start')
    frequency_end = request.form.get('end')
    if frequency_start and frequency_end:
        frequency_start = float(frequency_start)
        frequency_end = float(frequency_end)
        _frequency_steps = int(request.form.get('steps', 100))
        frequency_step = int(
            (10 ** 6 * (frequency_end - frequency_start)) / _frequency_steps
        )
        samples = scan_range(
            app.config['SERIAL_PORT'],
            frequency_start * (10 ** 6),
            frequency_end * (10 ** 6),
            frequency_step
        )

        response = make_response(json.dumps(samples, indent=2), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    return make_response(
        json.dumps({}),
        400,
    )


def generate_figure(samples):
    x = []
    yswr = []

    for sample in samples:
        x.append(float(sample['frequency'])/10**6)
        yswr.append(sample['swr'])

    fake_file = StringIO()
    figure = Figure(figsize=(8, 6, ))
    canvas = FigureCanvasAgg(figure)
    axis = figure.add_subplot(111)
    axis.plot(x, yswr, 'b')
    canvas.print_png(fake_file)
    data = fake_file.getvalue()

    return data


def get_resonating_frequency(samples):
    minimum_swr = 99
    resonating_frequency = None

    for sample in samples:
        if sample['swr'] < minimum_swr:
            resonating_frequency = sample['frequency']
            minimum_swr = sample['swr']

    return resonating_frequency


def get_bandwidth(frequency, samples, max_swr):
    band_start = None
    found_freq = False

    for sample in samples:
        if (
            sample['swr'] <= max_swr and
            band_start is None
        ):
            band_start = sample['frequency']
        elif (
            sample['swr'] > max_swr and
            band_start is not None and
            not found_freq
        ):
            band_start = None
        elif (
            sample['swr'] > max_swr and
            band_start is not None and
            found_freq
        ):
            return band_start, sample['frequency']

        if sample['frequency'] == frequency:
            found_freq = True

    return None, None


@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info('Connection received...')

    kwargs = {
        'start': '12',
        'end': '17',
        'steps': '100',
    }

    frequency_start = request.form.get('start')
    frequency_end = request.form.get('end')
    if frequency_start and frequency_end:
        kwargs.update({
            'start': frequency_start,
            'end': frequency_end,
            'steps': request.form.get('steps', 100),
        })

        frequency_start = int(frequency_start)
        frequency_end = int(frequency_end)
        _frequency_steps = int(request.form.get('steps', 100))
        frequency_step = int(
            (10 ** 6 * (frequency_end - frequency_start)) / _frequency_steps
        )

        samples = scan_range(
            app.config['SERIAL_PORT'],
            frequency_start * (10 ** 6),
            frequency_end * (10 ** 6),
            frequency_step
        )
        figure = generate_figure(samples)

        resonating_frequency = get_resonating_frequency(samples)
        start, end = get_bandwidth(resonating_frequency, samples, 2.0)

        kwargs.update({
            'figure': b64encode(figure),
            'resonating_frequency': (
                float(resonating_frequency) / 10**6
                if resonating_frequency else None
            ),
            'bw_start': float(start) / 10**6 if start else None,
            'bw_end': float(end) / 10**6 if end else None,
        })

    return render_template('index.html', **kwargs)
