from setuptools import setup, find_packages

setup(
    name="instatrace",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "colorama>=0.4.6",
        "beautifulsoup4>=4.12.0",
        "phonenumbers>=8.13.0",
        "pycountry>=22.3.0",
        "python-whois>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "instatrace=instatrace.cli:main",
        ],
    },
    author="John-Varghese-EH",
    description="Ultimate Instagram OSINT Intelligence Tool",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/John-Varghese-EH/InstaTrace",
    license="GPL-3.0",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
    ],
)
