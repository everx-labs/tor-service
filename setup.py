import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tor-service",
    version="0.0.0.1",
    author="TonLabs",
    author_email="",
    description=u"Authentication and authorization package for a website",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tonlabs/tor-service",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    python_requires='>=3.6',
    install_requires=[]
)
