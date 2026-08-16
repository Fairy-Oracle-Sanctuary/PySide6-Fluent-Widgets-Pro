import ast
from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def get_version():
    version_file = ROOT / "qfluentwidgets_pro" / "__init__.py"
    module = ast.parse(version_file.read_text(encoding="utf-8"))

    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value

    raise RuntimeError(f"Unable to find __version__ in {version_file}")

IMAGE_DEPENDENCIES = [
    "numpy",
    "Pillow",
    "scipy",
    "colorthief",
]

CHART_DEPENDENCIES = [
    "PySide6-WebEngine",
]


setup(
    name="qfluentwidgets-pro",
    version=get_version(),
    description="PySide6 Fluent Widgets Pro reimplementation",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Fairy-Oracle-Sanctuary/PySide6-Fluent-Widgets-Pro",
    license="GPLv3",
    packages=find_packages(
        include=[
            "qfluentwidgets_pro",
            "qfluentwidgets_pro.*",
        ]
    ),
    include_package_data=True,
    package_data={
        "": [
            "_rc/**/*",
        ],
    },
    python_requires=">=3.9",
    install_requires=[
        "PySide6>=6.6",
        "darkdetect>=0.8",
        'pywin32>=306; sys_platform == "win32"',
    ],
    extras_require={
        "image": IMAGE_DEPENDENCIES,
        "chart": CHART_DEPENDENCIES,
        "full": IMAGE_DEPENDENCIES + CHART_DEPENDENCIES,
    },
)
