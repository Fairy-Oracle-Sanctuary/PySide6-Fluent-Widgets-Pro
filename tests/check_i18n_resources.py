"""Verify every TS/QM and all rebuilt Qt resource modules, not just file existence."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run():
    from PySide6.QtCore import QFile, QIODevice, QTranslator
    import qfluentwidgets_pro._rc.resource
    import qfluentwidgets_pro.qframelesswindow._rc.resource
    import gallery.common.resource

    base = ROOT / 'qfluentwidgets_pro/_rc/i18n'
    template = ET.parse(base / 'qfluentwidgets.en_US.ts').getroot()

    def messages(root):
        result = {}
        for context in root.findall('context'):
            for message in context.findall('message'):
                key = (context.findtext('name'), message.findtext('source'))
                assert key not in result, ('Duplicate message', key)
                result[key] = message
        return result

    keys = messages(template).keys()
    files = sorted(base.glob('*.ts'))
    count = 0
    for filepath in files:
        entries = messages(ET.parse(filepath).getroot())
        assert not keys - entries.keys(), ('Missing template keys', filepath.name)
        qm = filepath.with_suffix('.qm')
        embedded = QFile(':/qfluentwidgets/i18n/' + qm.name)
        assert embedded.open(QIODevice.ReadOnly), qm.name
        assert bytes(embedded.readAll()) == qm.read_bytes(), ('Stale resource QM', qm.name)
        disk, resource = QTranslator(), QTranslator()
        assert disk.load(str(qm)), qm.name
        assert resource.load(':/qfluentwidgets/i18n/' + qm.name), qm.name
        for context, source in keys:
            translation = entries[(context, source)].find('translation')
            assert translation is not None and translation.get('type') is None, (filepath.name, source)
            assert translation.text and translation.text.strip(), (filepath.name, source)
            assert disk.translate(context, source) == translation.text, (qm.name, context, source)
            assert resource.translate(context, source) == translation.text, (qm.name, context, source)
            count += 1
    resources = ('qfluentwidgets_pro/_rc/resource.qrc', 'gallery/resource/resource.qrc',
                 'qfluentwidgets_pro/qframelesswindow/_rc/resource.qrc')
    resource_count = 0
    for relative in resources:
        qrc = ROOT / relative
        for group in ET.parse(qrc).getroot().findall('qresource'):
            prefix = group.get('prefix', '').rstrip('/')
            for item in group.findall('file'):
                resource_name = ':' + prefix + '/' + item.get('alias', item.text)
                embedded = QFile(resource_name)
                assert embedded.open(QIODevice.ReadOnly), resource_name
                assert bytes(embedded.readAll()) == (qrc.parent / item.text).read_bytes(), (
                    'Stale or missing embedded asset', resource_name)
                resource_count += 1
    print('PASS: %d language TS/QM catalogs, %d translated template lookups, '
          '%d QRC modules and %d embedded assets verified byte-for-byte'
          % (len(files), count, len(resources), resource_count))


if __name__ == '__main__':
    run()
