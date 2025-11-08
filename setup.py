from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="glcs",
    version="0.1.0",
    author="GLCS Team",
    author_email="",
    description="Global Logical Context Store - Practical contradiction detection for LLM conversations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GireeshS22/Global-Logic-Context-Store",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "streamlit>=1.28.0",
        ],
    },
)
