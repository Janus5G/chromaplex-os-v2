from setuptools import setup, find_packages

setup(
    name="chromaplex-os",
    version="0.1.0",
    description="ChromaPlex OS - krystalbaseret optisk datalagring",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "chromaplex=chromaplex_os.cli:main",
        ],
    },
    install_requires=[],
    python_requires=">=3.9",
)
