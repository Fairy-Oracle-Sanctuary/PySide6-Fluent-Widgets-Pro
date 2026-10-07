"""Native CodeEdit gallery with explicit sample replacement."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets_pro import BodyLabel, CheckBox, ComboBox, PushButton, toggleTheme
from qfluentwidgets_pro.components.widgets.code_edit import CodeEdit


SAMPLES = {
    'python': '# Unicode and multiline strings\nclass Greeter:\n    def hello(self, name):\n        message = """Hello\n世界 🌍\n"""\n        return f"{message}, {name}"\n',
    'c': '/* multiline\n   comment */\n#include <stdio.h>\nint main(void) {\n    printf("Hello\\n");\n    return 0;\n}\n',
    'cpp': '#include <iostream>\n/* multiline\n   comment */\nint main() {\n    std::cout << "Hello" << std::endl;\n    return 0;\n}\n',
    'csharp': 'using System;\nclass Demo {\n    static void Main() { Console.WriteLine("Hello"); }\n}\n',
    'java': 'class Demo {\n    public static void main(String[] args) {\n        System.out.println("Hello");\n    }\n}\n',
    'javascript': '// Template strings\nconst name = "World";\nconst message = `Hello\n${name}`;\nconsole.log(message);\n',
    'typescript': 'interface User { name: string; active: boolean; }\nconst user: User = {name: "Hello", active: true};\n',
    'json': '{\n    "configurations": [\n        {\n            "name": "Win32",\n            "includePath": [\n                "${workspaceFolder}/**",\n                "D:/Qt/5.15.2/mingw81_64/include"\n            ],\n            "defines": ["_DEBUG", "UNICODE"],\n            "windowsSdkVersion": "10.0.19041.0",\n            "configurationProvider": "ms-vscode.cmake-tools"\n        }\n    ],\n    "version": 4,\n    "start": true\n}\n',
    'html': '<!-- embedded languages -->\n<html>\n<style>body { color: #0078d4; }</style>\n<script>const value = "Hello";</script>\n<body>Hello</body>\n</html>\n',
    'css': '/* Theme */\n.card {\n    color: #0078d4;\n    border-radius: 8px;\n}\n',
    'xml': '<?xml version="1.0"?>\n<settings enabled="true">\n    <name>Hello</name>\n</settings>\n',
    'yaml': '# Configuration\nname: Hello\nmessage: |\n  multiline\n  text\nitems:\n  - one\n  - two\n',
    'toml': '# Configuration\n[window]\ntitle = "Hello"\nsize = [900, 700]\nenabled = true\n',
    'ini': '; Configuration\n[window]\ntitle = Hello\nwidth = 900\n',
    'bash': '#!/bin/bash\nname="Hello"\nfor file in *.txt; do\n    echo "$name: $file"\ndone\n',
    'powershell': '# Configuration\n$name = "Hello"\nGet-ChildItem | ForEach-Object {\n    Write-Output "$name: $_"\n}\n',
    'sql': '-- Query\nSELECT name, COUNT(*) AS total\nFROM users\nWHERE active = TRUE\nGROUP BY name;\n',
    'go': 'package main\nimport "fmt"\nfunc main() {\n    fmt.Println("Hello")\n}\n',
    'rust': '// Hello\nfn main() {\n    let name = "World";\n    println!("Hello {}", name);\n}\n',
    'markdown': '# Hello\n\n**Bold** and *italic*.\n\n```python\nprint("Hello")\n```\n',
}


class CodeEditDemo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('codeEditInterface')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(BodyLabel('CodeEdit — 20 种语言；切换语言不改变代码，加载示例会替换内容。'))
        controls = QHBoxLayout()
        language = ComboBox(self)
        language.addItems(list(CodeEdit.supportedLanguages()))
        language.setCurrentText('json')
        sample = PushButton('加载示例', self)
        readonly = CheckBox('只读', self)
        numbers = CheckBox('行号', self)
        numbers.setChecked(True)
        theme = PushButton('切换主题', self)
        for widget in (language, sample, readonly, numbers, theme):
            controls.addWidget(widget)
        controls.addStretch()
        layout.addLayout(controls)
        self.editor = CodeEdit(self, language='json')
        self.editor.setPlainText(SAMPLES['json'])
        language.currentTextChanged.connect(self.editor.setLanguage)
        sample.clicked.connect(lambda: self.editor.setPlainText(SAMPLES[language.currentText()]))
        readonly.toggled.connect(self.editor.setReadOnly)
        numbers.toggled.connect(self.editor.setLineNumbersVisible)
        theme.clicked.connect(toggleTheme)
        layout.addWidget(self.editor, 1)
