from setuptools import setup, find_packages

setup(
    name="auth2fa",
    version="0.1.2",
    packages=find_packages(),
    package_data={
        "auth2fa": ["sql/**/*.sql"],
    },
    install_requires=[
        "pyotp",
        "qrcode",
        "Pillow",
    ],
    extras_require={
        "sql": ["sqloader"],
    },
)
