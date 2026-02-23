from setuptools import setup, find_packages

setup(
    name="abyssac",
    version="0.1.0",
    description="AbyssAC是基于NNG导航和Y层记忆的AI操作系统反馈系统",
    author="AbyssAC Team",
    author_email="abyssac@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests==2.31.0",
        "pyyaml==6.0.1"
    ],
    extras_require={
        "dev": [
            "pytest==7.4.0",
            "black==23.3.0",
            "flake8==6.0.0",
            "mypy==1.4.1"
        ],
        "optional": [
            "python-dotenv==1.0.0",
            "colorlog==6.7.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "abyssac=core.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)