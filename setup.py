import setuptools

setuptools.setup(
    name='LangChainKaltura',
    version='0.0.1',
    author='Mr. Lance E Sloan',
    author_email='lsloan-github.com@umich.edu',
    description='Collects captions from media in Kaltura and produces '
                'LangChain Document objects.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license_files=['LICENSE.txt', ],
    url='https://github.com/umich-its-ai/langchain_kaltura',
    project_urls={
        'Issues': 'https://github.com/umich-its-ai/langchain_kaltura/issues',
        'Homepage': 'https://github.com/umich-its-ai/langchain_kaltura', },
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Topic :: Scientific/Engineering :: Artificial Intelligence', ],
    keywords=[
        'Kaltura', 'LangChain', 'caption', 'AI', 'Artificial Intelligence', ],
    python_requires='>=3.11.8',
    include_package_data=True,  # to include tests/fixtures/*
    data_files=[('/', ['requirements.txt'])],
    install_requires=[
        r.split('=')[0] for r in open('requirements.txt').read().split()],
)
