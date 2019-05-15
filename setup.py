from setuptools import setup

requirements = [
    # TODO: put your package requirements here
    'PySide2',
    'hg+https://hephaistos.lpp.polytechnique.fr/rhodecode/HG_REPOSITORIES/LPP/INSTRUMENTATION/lppinstru', 'pyserial',
    'pyzmq', 'peakutils', 'numpy', 'pandas', 'appdirs', 'pint'
]

setup(
    name='Juice_SCM_GSE',
    version='0.0.1',
    description="Juice_SCM_GSE",
    author="Alexis Jeandet",
    author_email='alexis.jeandet@member.fsf.org',
    url='https://github.com/jeandet/Juice_SCM_GSE',
    packages=['juice_scm_gse', 'juice_scm_gse.gui'],
#    package_data={'juice_scm_gse.images': ['*.png']},
    entry_points={
        'console_scripts': [
            'Juice_SCM_GSE=juice_scm_gse.app:main'
        ]
    },
    install_requires=requirements,
    zip_safe=False,
    keywords='Juice_SCM_GSE',
    classifiers=[
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
