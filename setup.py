from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="quanttradingpro",
    version="0.1.0",
    author="basten99",
    author_email="basten99@github.com",
    description="Professional Quantitative Trading Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/basten99/QuantTradingPro",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8,<3.12",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.930",
            "pre-commit>=2.17.0",
        ],
        "docs": [
            "sphinx>=4.3.0",
            "sphinx-rtd-theme>=1.0.0",
            "nbsphinx>=0.8.7",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
            "xgboost>=1.5.0",
            "lightgbm>=3.3.0",
            "tensorflow>=2.8.0",
            "torch>=1.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quanttrading=src.cli:main",
        ],
    },
)