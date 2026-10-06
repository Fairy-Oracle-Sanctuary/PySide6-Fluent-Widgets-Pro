"""Offline regression tests for TS sync, safe translation and build ordering."""
import importlib.util
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('translate_ts', ROOT / 'scripts/translate_ts.py')
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def values(filepath):
    root = ET.parse(filepath).getroot()
    return {(context.findtext('name'), message.findtext('source')): message.findtext('translation')
            for context in root.findall('context') for message in context.findall('message')}


def run():
    with tempfile.TemporaryDirectory(prefix='fluent-ts-tests-') as temporary:
        base = Path(temporary)
        template = base / 'qfluentwidgets.en_US.ts'
        language = base / 'qfluentwidgets.fr_FR.ts'
        template.write_text('''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS><TS version="2.1" language="en_US">
<context><name>One</name>
<message><source>Save</source><translation>Save</translation></message>
<message><source>Value: %1</source><translation>Value: %1</translation></message>
<message><source>Images (*.png *.jpg)</source><translation>Images (*.png *.jpg)</translation></message>
</context><context><name>Two</name>
<message><source>Save</source><translation>Save</translation></message>
<message><source>Drag &amp; drop</source><translation>Drag &amp; drop</translation></message>
</context></TS>''', encoding='utf-8')
        language.write_text('''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS><TS version="2.1" language="fr_FR">
<context><name>One</name>
<message><source>Save</source><translation>Enregistrer</translation></message>
<message><source>Legacy</source><translation>Ancien</translation></message>
</context><context><name>Extra</name>
<message><source>Old</source><translation>Vieux</translation></message>
</context></TS>''', encoding='utf-8')
        original = values(language)
        with patch.object(script, 'I18N_DIR', str(base)):
            assert script.sync_language_file(language, 'fr_FR') == 4
            synchronized = language.read_text(encoding='utf-8')
            assert all(values(language)[key] == value for key, value in original.items())
            assert script.sync_language_file(language, 'fr_FR') == 0
            assert synchronized == language.read_text(encoding='utf-8')
            calls = []

            def translate(sources, lang):
                assert lang == 'fr_FR' and len(sources) <= 50
                calls.append(sources)
                return ['Traduit ' + source + r' \1 & <test>' for source in sources]

            with patch.object(script, 'translate_batch', side_effect=translate):
                assert script.translate_one_file(language, 'fr_FR', 50) == (4, 4)
            assert values(language)[('Two', 'Save')] == 'Enregistrer'
            assert 'Drag & drop' in calls[0]  # API receives decoded XML, not &amp;.
            assert values(language)[('Two', 'Drag & drop')].endswith(r'\1 & <test>')
            assert all(values(language)[key] == value for key, value in original.items())
            with patch.object(script, 'translate_batch', side_effect=AssertionError('Unexpected API call')):
                assert script.translate_one_file(language, 'fr_FR', 50) == (0, 0)
            german = base / 'qfluentwidgets.de_DE.ts'
            assert script.sync_language_file(german, 'de_DE') == 5
            assert ET.parse(german).getroot().get('language') == 'de_DE'
            assert len(script.parse_ts_file(german)[1]) == 5

            # Unfinished translations are work-in-progress; obsolete entries
            # stay untouched. The XML format may include location elements.
            german.write_text('''<TS language="de_DE"><context><name>One</name>
<message><location filename="a.py" line="3"/><source>Save</source><translation type="unfinished">Entwurf</translation></message>
<message><source>Gone</source><translation type="vanished">Alt</translation></message>
</context></TS>''', encoding='utf-8')
            assert [source for _, source in script.parse_ts_file(german)[1]] == ['Save']

            # 51 unique sources split into 50 + 1, not batches of 100.
            messages = ''.join('<message><source>Text %d</source><translation>Text %d</translation></message>'
                               % (i, i) for i in range(51))
            template.write_text('<TS language="en_US"><context><name>Batch</name>' + messages
                                + '</context></TS>', encoding='utf-8')
            italian = base / 'qfluentwidgets.it_IT.ts'
            with patch.object(script, 'translate_batch', side_effect=lambda sources, _: ['T ' + s for s in sources]) as api, \
                    patch.object(script.time, 'sleep'):
                try:
                    script.translate_one_file(str(italian), 'it_IT', 50)
                    raise AssertionError('Missing TS must not report a successful 0/0 run')
                except FileNotFoundError:
                    pass
                script.sync_language_file(italian, 'it_IT')
                assert script.translate_one_file(str(italian), 'it_IT', 50) == (51, 51)
                assert [len(call.args[0]) for call in api.call_args_list] == [50, 1]

    assert script._valid_translation('Duration: %1 ms', 'Dauer: %1 ms')
    assert not script._valid_translation('Duration: %1 ms', 'Dauer: %2 ms')
    assert not script._valid_translation('Images (*.png *.jpg)', 'Images (*.png)')
    assert not script._valid_translation('Save', '')
    assert not script._valid_translation('Hex AARRGGBB or RRGGBB', 'Hex ARGB or RGB')
    assert script._parse_json_translations('{"translations":["A","B"]}') == ['A', 'B']
    assert script._parse_json_translations('{"translations":[null,123]}') is None
    order = []
    args = SimpleNamespace(build=True, compile_qm=False, compile_resources=False, skip_translate=False)
    with patch.object(script, 'compile_qm_files', side_effect=lambda: order.append('qm')), \
            patch.object(script, 'compile_resources', side_effect=lambda: order.append('resources')):
        assert script._build_if_requested(args, complete=False) == 1
        assert order == []
        assert script._build_if_requested(args) == 0
        assert order == ['qm', 'resources']
    print('PASS: additive/idempotent TS sync, preserved legacy translations, XML '
          'escaping, deduplication, 50-item batches, placeholders, resume and build ordering')


if __name__ == '__main__':
    run()
