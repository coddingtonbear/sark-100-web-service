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
    ohms_styles = (
        ('r', 'r:'),
        ('x', 'y:'),
        ('z', 'g:'),
    )
    x = []
    yswr = []
    handles = []

    for sample in samples:
        x.append(float(sample['frequency'])/10**6)
        yswr.append(sample['swr'])

    fake_file = StringIO()
    figure = Figure(figsize=(9, 6, ), facecolor='white')
    canvas = FigureCanvasAgg(figure)

    axis = figure.add_subplot(111)
    axis.set_ylabel('SWR')
    axis.set_xlabel('Frequency (MHz)')
    axis.set_axis_bgcolor((1, 1, 1,))
    axis_ohms = axis.twinx()
    axis_ohms.set_ylabel('Ohms')

    handles.append(
        axis.plot(x, yswr, 'b', label='SWR')[0]
    )
    for prop, style in ohms_styles:
        sample = [float(v.get(prop)) for v in samples]
        handles.append(
            axis_ohms.plot(x, sample, style, label=prop)[0]
        )

    figure.legend(
        handles=handles,
        labels=[
            'SWR'
        ] + [prop for prop, style in ohms_styles]
    )

    canvas.print_png(fake_file)
    data = fake_file.getvalue()

    return data


def get_center_frequency(samples):
    minimum_swr = 99
    center_frequency = None

    for sample in samples:
        if sample['swr'] < minimum_swr:
            center_frequency = sample['frequency']
            minimum_swr = sample['swr']

    return center_frequency


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
        'steps': '40',
    }

    frequency_start = request.form.get('start')
    frequency_end = request.form.get('end')
    if frequency_start and frequency_end:
        kwargs.update({
            'start': frequency_start,
            'end': frequency_end,
            'steps': request.form.get('steps', 100),
        })

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
        figure = generate_figure(samples)

        center_frequency = get_center_frequency(samples)

        bw_stats = []
        for swr_max in (1.5, 2, ):
            start, end = get_bandwidth(center_frequency, samples, swr_max)
            if start and end:
                bw_stats.append(
                    {
                        'swr_max': swr_max,
                        'start': float(start) / 10**6,
                        'end': float(end) / 10**6,
                        'bandwidth': float(end - start) / 10**6,
                    }
                )

        kwargs.update({
            'figure': b64encode(figure),
            'center_frequency': (
                float(center_frequency) / 10**6
                if center_frequency else None
            ),
            'bw_stats': bw_stats,
        })

    return render_template('index.html', **kwargs)
