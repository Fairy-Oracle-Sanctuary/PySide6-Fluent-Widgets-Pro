"""Create the gallery's five-second PCM WAV using only the Python standard library.

This is a synthetic test tone/envelope, not speech or a recording. No overwrite.
"""
import argparse
import sys
import wave
from array import array
from math import exp, pi, sin
from pathlib import Path


DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / 'gallery/resource/audio/waveform_sample.wav'


def generate(output=DEFAULT_OUTPUT):
    output = Path(output)
    sampleRate = 24000
    data = array('h')
    for frame in range(sampleRate * 5):
        t = frame / sampleRate
        envelope = .02 * exp(-t * 10)
        for center, width, height in ((.65, .28, .52), (1.5, .38, .65),
                                      (2.6, .2, .95), (3.25, .3, .56)):
            envelope += height * exp(-((t - center) / width) ** 2)
        envelope *= .28 + .72 * abs(sin(2 * pi * 6.7 * t))
        carrier = (sin(2 * pi * 173 * t) + .3 * sin(2 * pi * 347 * t)) / 1.3
        value = envelope * carrier if t < 4.15 else 0.
        data.append(round(max(-1., min(1., value)) * 32767))
    if sys.byteorder != 'little':
        data.byteswap()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Open exclusively: an existing user file is never silently overwritten.
    with output.open('xb') as destination:
        with wave.open(destination, 'wb') as file:
            file.setnchannels(1)
            file.setsampwidth(2)
            file.setframerate(sampleRate)
            file.writeframes(data.tobytes())
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(generate(args.output))
