"""setup.py controls the build, testing, and distribution of the egg"""

from setuptools import setup, find_packages
import re
import os.path


VERSION_REGEX = re.compile(r"""
    ^__version__\s=\s
    ['"](?P<version>.*?)['"]
""", re.MULTILINE | re.VERBOSE)

BUILD_REGEX = re.compile(r"""
    ^__build__\s=\s
    ['"](?P<version>.*?)['"]
""", re.MULTILINE | re.VERBOSE)

VERSION_FILE = os.path.join("amplium", "version.py")


def get_version():
    """Reads the version from the package"""
    with open(VERSION_FILE) as handle:
        lines = handle.read()
        version_result = VERSION_REGEX.search(lines)
        build_result = BUILD_REGEX.search(lines)
        if version_result and build_result:
            return "%s-%s" % (version_result.group(1), build_result.group(1))
        else:
            raise ValueError("Unable to determine __version__ and/or __build__")


def get_requirements():
    """Reads the installation requirements from requirements.pip"""
    with open("requirements.pip") as reqfile:
        return filter(lambda line: not line.startswith(('#', '-')), reqfile.read().split("\n"))

setup(
    name='amplium',
    version=get_version(),
    description="Lambda-based Selenium Grid written in Python.",
    long_description="",
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='',
    author='Amplify Education',
    author_email='github@amplify.com',
    url='',
    license='mit',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    dependency_links=[
    ],
    install_requires=get_requirements(),
    test_suite='nose.collector',
    entry_points="""
        [paste.app_factory]
        main=amplium:main
    """,
)
