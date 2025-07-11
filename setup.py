from setuptools import setup, find_packages
import os

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="transbank-oneclick-api",
    version="1.0.0",
    description="API REST para integración con Transbank Oneclick Mall, permitiendo pagos en un solo clic mediante tarjetas previamente inscritas.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Equipo EPC (ver README)",
    author_email="soporte@transbank.cl",
    url="https://www.transbankdevelopers.cl/",
    packages=find_packages(
        include=["app", "app.*"],
        exclude=["tests", "tests.*", "alembic", "alembic.*", "venv", "venv.*"]
    ),
    include_package_data=True,
    package_data={},
    exclude_package_data={"": ["alembic/*", "alembic.ini"]},
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "psycopg2-binary==2.9.9",
        "transbank-sdk==6.1.0",
        "python-multipart==0.0.6",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "structlog==23.2.0"
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-cov==4.1.0",
            "pytest-mock==3.12.0",
            "pytest-asyncio==0.21.1",
            "httpx==0.25.2",
            "black==23.11.0",
            "flake8==6.1.0",
            "mypy==1.7.1",
            "pre-commit==3.6.0"
        ]
    },
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            # No script CLI principal, se ejecuta con uvicorn
        ]
    },
    license="MIT",
    keywords="transbank oneclick fastapi pagos api rest",
    project_urls={
        "Documentación": "https://www.transbankdevelopers.cl/",
        "Código": "https://github.com/TransbankDevelopers/transbank-sdk-python"
    },
) 