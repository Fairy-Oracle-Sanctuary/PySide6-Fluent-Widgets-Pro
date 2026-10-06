"""使用 DeepSeek API 翻译 Qt .ts 翻译文件。

新增语言的流程：复制英文模板（qfluentwidgets.en_US.ts），
更新 <TS ... language="..."> 属性，清空 translation 后调用 API 翻译。

用法:
    python scripts/translate_ts.py                             # 交互式：选择功能（翻译已有语言 / 新增语言 / 一键新增全部）
    python scripts/translate_ts.py --add-lang fr_FR            # 新增语言：复制英文模板并翻译
    python scripts/translate_ts.py --add-lang fr_FR --skip-translate  # 仅创建语言文件，不翻译
    python scripts/translate_ts.py --add-all-langs             # 一键新增所有未添加的语言并翻译
    python scripts/translate_ts.py --all                       # 一键翻译 i18n 目录下所有 .ts 文件的未翻译项
    python scripts/translate_ts.py --lang fr_FR                # 指定语言，自动推导文件路径
    python scripts/translate_ts.py qfluentwidgets_pro/_rc/i18n/qfluentwidgets.fr_FR.ts --lang fr_FR

每批发送 50 条待翻译文本（项目硬约束：50 而非 100 以降低 AI 错误概率），
严格 JSON 格式输出 + 多策略解析 + 数量校验 + 自动重试。
支持断点续传：已翻译的条目会被跳过。

已有语言会先同步英文模板，保留原译文和额外条目，再翻译新增项。
    python scripts/translate_ts.py --all --skip-translate  # 仅同步 TS
    python scripts/translate_ts.py --all --jobs 4 --build  # 同步、翻译、QM、资源
    python scripts/translate_ts.py --compile-qm --compile-resources  # 仅编译

密钥优先读取 DEEPSEEK_API_KEY 环境变量；本地备选配置
scripts/translate_ts.local.json（{"api_key": "..."}）不会进入版本管理。
"""

import argparse
import json
import os
import re
import sys
import time
import html
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# 项目硬约束：batch size 必须为 50（非 100）以降低 AI 编号错误概率
BATCH_SIZE = 50

MAX_RETRIES = 2

# i18n 目录：相对脚本位置定位，不依赖当前工作目录
I18N_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "qfluentwidgets_pro",
        "_rc",
        "i18n",
    )
)

TS_PREFIX = "qfluentwidgets"  # ts 文件名前缀
SOURCE_LANG = "en_US"  # 源语言（英文模板，其 translation 与 source 相同）

LANG_NAMES = {
    "af_ZA": "Afrikaans",
    "am_ET": "አማርኛ (Amharic)",
    "ar_AR": "العربية (Arabic)",
    "az_AZ": "Azərbaycanca (Azerbaijani)",
    "be_BY": "Беларуская (Belarusian)",
    "bg_BG": "Български (Bulgarian)",
    "bn_BD": "বাংলা (Bengali)",
    "bs_BA": "Bosanski (Bosnian)",
    "ca_ES": "Català (Catalan)",
    "cs_CZ": "Čeština (Czech)",
    "cy_GB": "Cymraeg (Welsh)",
    "da_DK": "Dansk (Danish)",
    "de_DE": "Deutsch (German)",
    "el_GR": "Ελληνικά (Greek)",
    "en_US": "English",
    "es_ES": "Español (Spanish)",
    "et_EE": "Eesti (Estonian)",
    "eu_ES": "Euskara (Basque)",
    "fa_IR": "فارسی (Persian)",
    "fi_FI": "Suomi (Finnish)",
    "fr_FR": "Français (French)",
    "ga_IE": "Gaeilge (Irish)",
    "gl_ES": "Galego (Galician)",
    "gu_IN": "ગુજરાતી (Gujarati)",
    "he_IL": "עברית (Hebrew)",
    "hi_IN": "हिन्दी (Hindi)",
    "hr_HR": "Hrvatski (Croatian)",
    "hu_HU": "Magyar (Hungarian)",
    "hy_AM": "Հայերեն (Armenian)",
    "id_ID": "Bahasa Indonesia (Indonesian)",
    "is_IS": "Íslenska (Icelandic)",
    "it_IT": "Italiano (Italian)",
    "ja_JP": "日本語 (Japanese)",
    "ka_GE": "ქართული (Georgian)",
    "kk_KZ": "Қазақша (Kazakh)",
    "km_KH": "ខ្មែរ (Khmer)",
    "kn_IN": "ಕನ್ನಡ (Kannada)",
    "ko_KR": "한국어 (Korean)",
    "lt_LT": "Lietuvių (Lithuanian)",
    "lv_LV": "Latviešu (Latvian)",
    "mk_MK": "Македонски (Macedonian)",
    "ml_IN": "മലയാളം (Malayalam)",
    "mn_MN": "Монгол (Mongolian)",
    "mr_IN": "मराठी (Marathi)",
    "ms_MY": "Bahasa Melayu (Malay)",
    "my_MM": "မြန်မာ (Burmese)",
    "nb_NO": "Norsk Bokmål (Norwegian)",
    "ne_NP": "नेपाली (Nepali)",
    "nl_NL": "Nederlands (Dutch)",
    "nn_NO": "Norsk Nynorsk (Norwegian Nynorsk)",
    "pa_IN": "ਪੰਜਾਬੀ (Punjabi)",
    "pl_PL": "Polski (Polish)",
    "pt_BR": "Português (Brasil) (Portuguese)",
    "pt_PT": "Português (Portugal) (Portuguese)",
    "ro_RO": "Română (Romanian)",
    "ru_RU": "Русский (Russian)",
    "si_LK": "සිංහල (Sinhala)",
    "sk_SK": "Slovenčina (Slovak)",
    "sl_SI": "Slovenščina (Slovenian)",
    "sq_AL": "Shqip (Albanian)",
    "sr_RS": "Српски (Serbian)",
    "sv_SE": "Svenska (Swedish)",
    "sw_KE": "Kiswahili (Swahili)",
    "ta_IN": "தமிழ் (Tamil)",
    "te_IN": "తెలుగు (Telugu)",
    "tg_TJ": "Тоҷикӣ (Tajik)",
    "th_TH": "ไทย (Thai)",
    "tl_PH": "Tagalog (Filipino)",
    "tr_TR": "Türkçe (Turkish)",
    "uk_UA": "Українська (Ukrainian)",
    "ur_PK": "اردو (Urdu)",
    "uz_UZ": "Oʻzbekcha (Uzbek)",
    "vi_VN": "Tiếng Việt (Vietnamese)",
    "zh_CN": "简体中文 (Simplified Chinese)",
    "zh_HK": "繁體中文 (Hong Kong)",
    "zh_TW": "繁體中文 (Traditional Chinese)",
}


# 匹配单个 <message> 块，捕获 source 和 translation
# 注意：本项目 ts 文件无 <location> 元素，格式为 <message><source>...</source><translation>...</translation></message>
MESSAGE_PATTERN = re.compile(r'<message\b[^>]*>.*?</message>', re.DOTALL)
CONTEXT_PATTERN = re.compile(r'<context\b[^>]*>.*?</context>', re.DOTALL)
REPO_DIR = Path(__file__).resolve().parents[1]


def _atomic_write(filepath, content):
    """Replace a complete valid XML file; interrupted writes leave the old file intact."""
    ET.fromstring(content)
    filepath = Path(filepath)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n',
                                     dir=filepath.parent, delete=False) as stream:
        temporary = stream.name
        stream.write(content)
    try:
        os.replace(temporary, filepath)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _message_key(message):
    return (message.findtext('source'), message.findtext('comment', ''),
            message.get('numerus', ''), message.get('id', ''))


def _empty_translation(block):
    return re.sub(r'<translation\b[^>]*(?:/>|>.*?</translation>)',
                  '<translation></translation>', block, flags=re.DOTALL)


def sync_language_file(filepath, lang_code):
    """Append missing (context, source, comment) entries, never overwrite translations."""
    template_file = Path(I18N_DIR) / f'{TS_PREFIX}.{SOURCE_LANG}.ts'
    template = template_file.read_text(encoding='utf-8')
    template_root = ET.fromstring(template)
    filepath = Path(filepath)
    if lang_code == SOURCE_LANG:
        return 0
    if not filepath.exists():
        content = re.sub(r'(<TS\b[^>]*?\blanguage=")[^"]*(")',
                         lambda match: match[1] + lang_code + match[2], template, count=1)
        content = _empty_translation(content)
        _atomic_write(filepath, content)
        count = sum(len(context.findall('message')) for context in template_root.findall('context'))
        print(f'✅ {lang_code}: 创建 TS，{count} 条待翻译', flush=True)
        return count
    content = filepath.read_text(encoding='utf-8')
    root = ET.fromstring(content)
    if root.get('language') != lang_code:
        raise ValueError(f'TS language mismatch: {filepath.name}')
    existing = {}
    for context in root.findall('context'):
        existing.setdefault(context.findtext('name'), set()).update(
            _message_key(message) for message in context.findall('message'))
    added = 0
    new_contexts = []
    for template_match in CONTEXT_PATTERN.finditer(template):
        context = ET.fromstring(template_match[0])
        name = context.findtext('name')
        known = existing.get(name, set())
        missing = []
        for match in MESSAGE_PATTERN.finditer(template_match[0]):
            if _message_key(ET.fromstring(match[0])) not in known:
                missing.append(_empty_translation(match[0]))
        if not missing:
            continue
        added += len(missing)
        messages = '\n'.join('    ' + block for block in missing) + '\n'
        if name in existing:
            for match in CONTEXT_PATTERN.finditer(content):
                if ET.fromstring(match[0]).findtext('name') == name:
                    replacement = match[0].replace('</context>', messages + '</context>')
                    content = content[:match.start()] + replacement + content[match.end():]
                    break
        else:
            new_contexts.append('<context>\n    <name>' + html.escape(name, quote=False)
                                + '</name>\n' + messages + '</context>\n')
    if added:
        content = content.replace('</TS>', ''.join(new_contexts) + '</TS>')
        _atomic_write(filepath, content)
    print(f'✅ {lang_code}: 同步新增 {added} 条，原译文保留', flush=True)
    return added


def _placeholders(text):
    """Qt/Python format tokens and file-filter wildcards must survive translation."""
    from collections import Counter
    return Counter(re.findall(r'%L?\d+|%n|\{[^{}]*\}|\*\.[\w*]+', text))


def _valid_translation(source, translation):
    return (isinstance(translation, str) and bool(translation.strip())
            and _placeholders(source) == _placeholders(translation)
            and all(token in translation for token in ('AARRGGBB', 'RRGGBB') if token in source))


class TranslationServiceError(RuntimeError):
    """Permanent API failures must stop the run, not retry every language."""


def parse_ts_file(filepath: str):
    """解析 .ts 文件，返回 (content, pending)。

    content: 原始文件文本
    pending: list of (match, source_text) 待翻译条目
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    pending = []
    for match in MESSAGE_PATTERN.finditer(content):
        message = ET.fromstring(match[0])
        source_text = message.findtext('source', '')
        translation = message.find('translation')
        if translation is not None:
            if translation.get('type') in ('vanished', 'obsolete'):
                continue
            if translation.get('type') != 'unfinished' and (translation.text or '').strip():
                continue
        if not source_text.strip():
            continue
        if message.get('numerus') == 'yes':
            raise ValueError('Plural TS messages require a plural-aware translator')

        pending.append((match, source_text))

    return content, pending


def _extract_translations_from_json(obj):
    """从 JSON 对象中提取翻译列表，支持 translations/result/data/items 键名。"""
    if isinstance(obj, dict):
        for key in ("translations", "result", "data", "items"):
            if key in obj and isinstance(obj[key], list):
                return obj[key] if all(isinstance(text, str) for text in obj[key]) else None
    if isinstance(obj, list):
        return obj if all(isinstance(text, str) for text in obj) else None
    return None


def _parse_json_translations(text: str):
    """多策略解析 JSON 响应，返回 list[str] 或 None。

    策略：直接解析 → 代码块 JSON → {...} 提取 → [...] 提取
    """
    # 策略1：直接解析
    try:
        result = _extract_translations_from_json(json.loads(text))
        if result is not None:
            return result
    except json.JSONDecodeError:
        pass

    # 策略2：```json ... ``` 代码块
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if m:
        try:
            result = _extract_translations_from_json(json.loads(m.group(1)))
            if result is not None:
                return result
        except json.JSONDecodeError:
            pass

    # 策略3：提取 {...}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            result = _extract_translations_from_json(json.loads(m.group(0)))
            if result is not None:
                return result
        except json.JSONDecodeError:
            pass

    # 策略4：提取 [...]
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            result = _extract_translations_from_json(json.loads(m.group(0)))
            if result is not None:
                return result
        except json.JSONDecodeError:
            pass

    return None


def translate_batch(source_texts: list, target_lang: str):
    """调用 DeepSeek API 翻译一批文本。

    严格 JSON 格式输出 + 多策略解析 + 数量校验 + 自动重试。
    成功返回 list[str]（与 source_texts 等长），失败返回 None。
    """
    from openai import OpenAI, AuthenticationError, PermissionDeniedError
    api_key = os.environ.get('DEEPSEEK_API_KEY') or DEEPSEEK_API_KEY
    if not api_key:
        local_config = Path(__file__).with_name('translate_ts.local.json')
        if local_config.exists():
            api_key = json.loads(local_config.read_text(encoding='utf-8')).get('api_key', '')
    if not api_key:
        raise TranslationServiceError('请设置 DEEPSEEK_API_KEY，或在本地 translate_ts.local.json 配置 api_key')
    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL, timeout=90, max_retries=0)

    lang_name = LANG_NAMES.get(target_lang, target_lang)

    # 系统提示：严格要求 JSON 输出（项目硬约束）
    # 源文本来自英文模板，因此翻译方向为：英文 → 目标语言
    system_prompt = (
        f"你是一个专业的软件本地化翻译专家。"
        f"请将以下英文软件界面文本翻译为{lang_name}。\n"
        f"规则：\n"
        f"1. 完整保留占位符 {{}}、%1、%2、%L1、%n，以及文件通配符 *.png、*.* 等\n"
        f"2. 保持标点符号风格适应目标语言\n"
        f"3. 保持简洁，适合 UI 显示\n"
        f'4. 严格按 JSON 格式输出：{{"translations": ["翻译1", "翻译2", ...]}}\n'
        f"5. 翻译数量必须与输入数量一致\n"
        f"6. 不要输出任何其他内容"
        f"\n7. 保留颜色格式 AARRGGBB、RRGGBB 和 RGB/HSV 等技术缩写；不要改变文件扩展名"
    )

    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(source_texts))
    user_prompt = f"请翻译以下 {len(source_texts)} 条文本：\n\n{numbered}"

    last_error = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            result_text = response.choices[0].message.content.strip()
            translations = _parse_json_translations(result_text)

            if translations is None:
                last_error = "无法解析为 JSON"
            elif len(translations) != len(source_texts):
                last_error = (
                    f"数量不匹配（期望 {len(source_texts)}，实际 {len(translations)}）"
                )
            elif not all(_valid_translation(source, translation)
                         for source, translation in zip(source_texts, translations)):
                last_error = '空译文或占位符/文件通配符不匹配'
            else:
                return translations

            print(f"  ⚠️  尝试 {attempt + 1}/{MAX_RETRIES + 1} 失败: {last_error}")
            if attempt < MAX_RETRIES:
                time.sleep(1)
        except (AuthenticationError, PermissionDeniedError) as error:
            raise TranslationServiceError('翻译 API 身份验证/权限失败，请检查配置') from error
        except Exception as e:
            if getattr(e, 'status_code', None) in (400, 401, 402, 403):
                raise TranslationServiceError('翻译 API 请求被拒绝，请检查余额和配置') from e
            last_error = str(e).replace(api_key, '<redacted>')
            print(f"  ⚠️  尝试 {attempt + 1}/{MAX_RETRIES + 1} 异常: {last_error}")
            if attempt < MAX_RETRIES:
                time.sleep(1)

    print(f"  ❌ 重试 {MAX_RETRIES} 次后仍失败（{last_error}），跳过本批")
    return None


def discover_ts_files(i18n_dir: str = I18N_DIR):
    """扫描 i18n 目录，返回 [(lang_code, filepath), ...]，按语言代码排序。

    仅返回 LANG_NAMES 中已登记语言的 .ts 文件（自动排除源语言文件）。
    """
    result = []
    if not os.path.isdir(i18n_dir):
        print(f"❌ 目录不存在: {i18n_dir}")
        return result

    prefix = f"{TS_PREFIX}."
    for fname in sorted(os.listdir(i18n_dir)):
        if not fname.startswith(prefix) or not fname.endswith(".ts"):
            continue
        lang_code = fname[len(prefix) : -len(".ts")]
        if lang_code in LANG_NAMES and lang_code != SOURCE_LANG:
            result.append((lang_code, os.path.join(i18n_dir, fname)))
    return result


def create_language_file(
    lang_code: str, translate: bool = True, batch_size: int = BATCH_SIZE
):
    """新增语言：复制英文模板并更新 language 属性，清空 translation 后可选翻译。

    返回 (filepath, success, total)；创建失败时 filepath 为 None。
    """
    lang_file = os.path.join(I18N_DIR, f"{TS_PREFIX}.{lang_code}.ts")
    template_file = os.path.join(I18N_DIR, f"{TS_PREFIX}.{SOURCE_LANG}.ts")

    if not os.path.exists(template_file):
        print(f"❌ 英文模板不存在: {template_file}")
        return None, 0, 0
    if os.path.exists(lang_file):
        print(f"❌ 语言文件已存在: {lang_file}")
        return None, 0, 0

    sync_language_file(lang_file, lang_code)

    if not translate:
        return lang_file, 0, 0

    print()
    success, total = translate_one_file(lang_file, lang_code, batch_size)
    return lang_file, success, total


def add_all_languages(translate: bool = True, batch_size: int = BATCH_SIZE):
    """一键新增 LANG_NAMES 中所有尚未创建文件的语言，并逐个翻译。

    返回 (created_count, success, total)。
    """
    existing = {lang for lang, _ in discover_ts_files()}
    candidates = [c for c in LANG_NAMES if c != SOURCE_LANG and c not in existing]
    if not candidates:
        print("✅ LANG_NAMES 中所有语言均已添加，无需新增")
        return 0, 0, 0

    print(f"📂 待新增 {len(candidates)} 种语言，开始批量创建并翻译...\n")
    created = 0
    overall_success = 0
    overall_total = 0
    for idx, lang_code in enumerate(candidates, 1):
        print(f"\n{'=' * 60}")
        print(f"[{idx}/{len(candidates)}] 🌐 {LANG_NAMES[lang_code]} ({lang_code})")
        print(f"{'=' * 60}")
        filepath, success, total = create_language_file(
            lang_code, translate=translate, batch_size=batch_size
        )
        if filepath is None:
            continue
        created += 1
        overall_success += success
        overall_total += total

    print(f"\n{'=' * 60}")
    if translate:
        print(
            f"🎉 全部完成！共创建 {created}/{len(candidates)} 种语言，翻译 {overall_success}/{overall_total} 条"
        )
    else:
        print(f"🎉 全部完成！共创建 {created}/{len(candidates)} 种语言文件")
    print(f"{'=' * 60}")
    return created, overall_success, overall_total


def translate_one_file(filepath: str, target_lang: str, batch_size: int):
    """翻译单个 .ts 文件的未翻译项，返回 (success_count, total)。"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f'TS file does not exist: {filepath}')

    if batch_size != BATCH_SIZE:
        raise ValueError('Translation batch size must be 50')
    sync_language_file(filepath, target_lang)
    content, pending = parse_ts_file(filepath)
    total = len(pending)
    print(f"🔍 共找到 {total} 条待翻译条目")

    if total == 0:
        print("✅ 没有需要翻译的条目，跳过。")
        return 0, 0

    # Reuse a source only when all its existing translations agree. Context-
    # specific differing translations are never overwritten or reused.
    memory = {}
    for context in ET.fromstring(content).findall('context'):
        for message in context.findall('message'):
            source = message.findtext('source', '')
            trans = message.find('translation')
            if (trans is not None and trans.get('type') is None
                    and _valid_translation(source, trans.text)):
                memory.setdefault(source, set()).add(trans.text)
    resolved = {source: next(iter(values)) for source, values in memory.items() if len(values) == 1}

    def save_available():
        nonlocal content
        for match, source in pending:
            if source not in resolved:
                continue
            escaped = html.escape(resolved[source], quote=False)
            replacement = re.sub(r'<translation\b[^>]*(?:/>|>.*?</translation>)',
                                 lambda _: '<translation>' + escaped + '</translation>',
                                 match[0], flags=re.DOTALL)
            if '<translation' not in replacement:
                replacement = replacement.replace('</message>',
                                                  '<translation>' + escaped + '</translation></message>')
            content = content.replace(match[0], replacement, 1)
        _atomic_write(filepath, content)

    reused = sum(source in resolved for _, source in pending)
    if reused:
        save_available()
        print(f'♻️ {target_lang}: 复用 {reused} 条相同且无歧义的现有译文', flush=True)
    sources = list(dict.fromkeys(source for _, source in pending if source not in resolved))
    for batch_start in range(0, len(sources), batch_size):
        source_texts = sources[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(sources) + batch_size - 1) // batch_size
        print(f'🔄 {target_lang}: 第 {batch_num}/{total_batches} 批 ({len(source_texts)} 条)', flush=True)
        translations = translate_batch(source_texts, target_lang)
        if translations is None:
            print("  ⏸️  本批翻译失败，跳过（下次运行会重试）")
            continue

        resolved.update(zip(source_texts, translations))
        save_available()
        success_count = sum(source in resolved for _, source in pending)
        print(f'✅ {target_lang}: {success_count}/{total} 条已保存', flush=True)

        # 避免 API 限速
        if batch_start + batch_size < len(sources):
            time.sleep(1)

    return sum(source in resolved for _, source in pending), total


def compile_qm_files():
    """Compile every language, including English; fail immediately on tool errors."""
    tool = _qt_tool('lrelease')
    files = sorted(Path(I18N_DIR).glob(f'{TS_PREFIX}.*.ts'))
    gallery_i18n = REPO_DIR / 'gallery/resource/i18n'
    files.extend(sorted(gallery_i18n.glob('gallery.*.ts')))
    for filepath in files:
        subprocess.run([tool, str(filepath), '-qm', str(filepath.with_suffix('.qm'))], check=True)
    print(f'✅ 已生成 {len(files)} 个 QM 文件', flush=True)
    return len(files)


def _qt_tool(name):
    found = shutil.which('pyside6-' + name)
    if found:
        return found
    # Use the compiler distributed with the running PySide6 environment.
    import PySide6
    suffix = '.exe' if os.name == 'nt' else ''
    executable = Path(PySide6.__file__).parent / (name + suffix)
    if executable.is_file():
        return str(executable)
    raise RuntimeError('Cannot find Qt tool: pyside6-' + name)


def compile_resources():
    tool = _qt_tool('rcc')
    resources = [(REPO_DIR / 'qfluentwidgets_pro/_rc/resource.qrc',
                  REPO_DIR / 'qfluentwidgets_pro/_rc/resource.py'),
                 (REPO_DIR / 'gallery/resource/resource.qrc',
                  REPO_DIR / 'gallery/common/resource.py')]
    frameless = REPO_DIR / 'qfluentwidgets_pro/qframelesswindow/_rc/resource.qrc'
    if frameless.exists():
        resources.append((frameless, frameless.with_suffix('.py')))
    for source, output in resources:
        subprocess.run([tool, str(source), '-o', str(output)], check=True)
        print(f'✅ 编译资源: {output.relative_to(REPO_DIR)}', flush=True)
    return len(resources)


def _build_if_requested(args, complete=True):
    if not complete and not args.skip_translate:
        print('❌ 翻译未完成，保留断点；不编译 QM/资源，以免发布不完整翻译')
        return 1
    if args.build or args.compile_qm or args.compile_resources:
        # Resources embed QM bytes, so rebuilding resources always refreshes QM first.
        compile_qm_files()
    if args.build or args.compile_resources:
        compile_resources()
    return 0


def select_function() -> str:
    """显示功能菜单，让用户选择要执行的功能。"""
    print("🚀 请选择功能：")
    print("  1. 翻译已有语言的未翻译项")
    print("  2. 新增语言（复制英文模板并翻译）")
    print("  3. 一键新增所有未添加的语言")
    while True:
        try:
            choice = input("\n请输入功能编号 (1-3): ").strip()
            if choice == "1":
                return "translate"
            if choice == "2":
                return "add_lang"
            if choice == "3":
                return "add_all"
            print("❌ 无效的编号，请输入 1-3")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 已取消")
            sys.exit(1)


def select_language() -> str:
    """显示已有翻译文件的语言，让用户通过数字选择目标语言。"""
    lang_codes = [c for c, _ in discover_ts_files()]
    if not lang_codes:
        print("❌ 没有已创建的语言文件，请先通过「新增语言」功能创建")
        sys.exit(1)

    print("🌐 请选择目标语言：")
    for i, code in enumerate(lang_codes, 1):
        print(f"  {i}. {LANG_NAMES[code]} ({code})")

    while True:
        try:
            choice = input(f"\n请输入语言编号 (1-{len(lang_codes)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(lang_codes):
                return lang_codes[idx]
            print(f"❌ 无效的编号，请输入 1-{len(lang_codes)} 之间的数字")
        except ValueError:
            print(f"❌ 无效的输入，请输入数字 (1-{len(lang_codes)})")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 已取消")
            sys.exit(1)


def select_add_lang() -> str:
    """列出 LANG_NAMES 中尚未创建翻译文件的语言，让用户选择要新增的语言。"""
    existing = {lang for lang, _ in discover_ts_files()}
    candidates = [c for c in LANG_NAMES if c != SOURCE_LANG and c not in existing]
    if not candidates:
        print("✅ LANG_NAMES 中所有语言均已添加，无需新增")
        return None

    print("🌐 请选择要新增的语言：")
    for i, code in enumerate(candidates, 1):
        print(f"  {i}. {LANG_NAMES[code]} ({code})")

    while True:
        try:
            choice = input(f"\n请输入语言编号 (1-{len(candidates)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]
            print(f"❌ 无效的编号，请输入 1-{len(candidates)} 之间的数字")
        except ValueError:
            print(f"❌ 无效的输入，请输入数字 (1-{len(candidates)})")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 已取消")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="翻译 Qt .ts 翻译文件")
    parser.add_argument(
        "filepath",
        nargs="?",
        help=".ts 文件路径（未提供时根据语言自动推导）",
    )
    parser.add_argument(
        "--add-lang",
        metavar="LANG_CODE",
        help="新增语言：复制英文模板创建新语言文件并翻译（如 fr_FR）",
    )
    parser.add_argument(
        "--add-all-langs",
        action="store_true",
        help="一键新增 LANG_NAMES 中所有尚未创建的语言文件并翻译",
    )
    parser.add_argument(
        "--lang-name",
        metavar="NAME",
        help="（配合 --add-lang）自定义语言的显示名称",
    )
    parser.add_argument(
        "--skip-translate",
        action="store_true",
        help="仅同步/创建语言文件，不调用翻译 API",
    )
    parser.add_argument(
        "--lang",
        help=f"目标语言代码 ({', '.join(LANG_NAMES)})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="同步英文模板并翻译所有现有语言的未翻译项",
    )
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE, help="每批翻译数量（默认 50）"
    )
    parser.add_argument('--jobs', type=int, default=1, help='并行语言数量（1-8，默认 1）')
    parser.add_argument('--compile-qm', action='store_true', help='编译所有 TS 为 QM')
    parser.add_argument('--compile-resources', action='store_true', help='刷新 QM 后编译全部 QRC')
    parser.add_argument('--build', action='store_true', help='完成翻译后生成 QM 并编译资源')
    args = parser.parse_args()
    if args.batch_size != BATCH_SIZE:
        parser.error('每批翻译数量固定为 50')
    if not 1 <= args.jobs <= 8:
        parser.error('--jobs 必须为 1-8')
    if ((args.compile_qm or args.compile_resources) and not
            (args.all or args.add_lang or args.add_all_langs or args.lang or args.filepath)):
        return _build_if_requested(args)

    if args.add_lang:
        if not re.fullmatch(r"[a-zA-Z]{2,3}_[A-Z]{2}", args.add_lang):
            print(f"❌ 无效的语言代码: {args.add_lang}，请使用 xx_XX 格式（如 fr_FR）")
            return 1
        if args.lang_name:
            LANG_NAMES[args.add_lang] = args.lang_name
        elif args.add_lang not in LANG_NAMES:
            LANG_NAMES[args.add_lang] = args.add_lang

        print(f"🌐 新增语言: {LANG_NAMES[args.add_lang]} ({args.add_lang})")
        filepath, success, total = create_language_file(
            args.add_lang,
            translate=not args.skip_translate,
            batch_size=args.batch_size,
        )
        if filepath is None:
            return 1
        if not args.skip_translate:
            print(
                f"\n🎉 新语言 {args.add_lang} 翻译完成！成功翻译 {success}/{total} 条"
            )
        return _build_if_requested(args, success == total)

    if args.add_all_langs:
        created, success, total = add_all_languages(
            translate=not args.skip_translate, batch_size=args.batch_size
        )
        return _build_if_requested(args, success == total)

    if args.all:
        # 一键模式：遍历 i18n 目录下所有 .ts 文件
        files = discover_ts_files()
        if not files:
            print(f"❌ 未在 {I18N_DIR} 找到任何 .ts 文件")
            return 1

        print(f"📂 发现 {len(files)} 个 .ts 文件，开始批量翻译...\n")
        overall_success = 0
        overall_total = 0
        if args.skip_translate:
            for lang_code, filepath in files:
                sync_language_file(filepath, lang_code)
        else:
            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                futures = {executor.submit(translate_one_file, filepath, lang_code, args.batch_size):
                           lang_code for lang_code, filepath in files}
                try:
                    for future in as_completed(futures):
                        success, total = future.result()
                        overall_success += success
                        overall_total += total
                except Exception:
                    for future in futures:
                        future.cancel()
                    raise

        print(f"\n{'=' * 60}")
        print(f"🎉 全部完成！共翻译 {overall_success}/{overall_total} 条")
        print(f"{'=' * 60}")
        return _build_if_requested(args, overall_success == overall_total)

    # 单文件模式
    # --lang 优先；否则交互式：先选功能（翻译已有语言 / 新增语言），再选语言
    if args.lang:
        target_lang = args.lang
        if target_lang not in LANG_NAMES:
            print(f"❌ 不支持的语言代码: {target_lang}")
            print(f"   支持的语言: {', '.join(LANG_NAMES.keys())}")
            sys.exit(1)
    else:
        function = select_function()
        if function == "add_lang":
            lang_code = select_add_lang()
            if lang_code is None:
                return 0
            print(f"🌐 新增语言: {LANG_NAMES[lang_code]} ({lang_code})")
            filepath, success, total = create_language_file(
                lang_code, translate=True, batch_size=args.batch_size
            )
            if filepath is None:
                return 1
            print(f"\n🎉 新语言 {lang_code} 翻译完成！成功翻译 {success}/{total} 条")
            return _build_if_requested(args, success == total)
        if function == "add_all":
            _, success, total = add_all_languages(translate=True, batch_size=args.batch_size)
            return _build_if_requested(args, success == total)
        target_lang = select_language()

    # 推导文件路径：未提供时根据语言代码自动推导
    filepath = args.filepath or os.path.join(I18N_DIR, f"{TS_PREFIX}.{target_lang}.ts")
    batch_size = args.batch_size

    print(f"📂 文件: {filepath}")
    print(f"🌐 目标语言: {LANG_NAMES.get(target_lang, target_lang)}")
    print(f"📦 每批数量: {batch_size}")
    print()

    if args.skip_translate:
        sync_language_file(filepath, target_lang)
        return _build_if_requested(args)
    success, total = translate_one_file(filepath, target_lang, batch_size)
    print(f"\n🎉 翻译完成！成功翻译 {success}/{total} 条")
    return _build_if_requested(args, success == total)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (TranslationServiceError, subprocess.CalledProcessError, ValueError, OSError) as error:
        print(f'❌ {error}', flush=True)
        sys.exit(1)
